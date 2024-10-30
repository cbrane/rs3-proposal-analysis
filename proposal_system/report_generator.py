import os
from openai import OpenAI
import rs3_analysis as rs3
import json
import sys


class AssistantManager:
    """
    Manages the interaction with the OpenAI API for processing RS3 documents.
    """

    def __init__(self, rs3_document_path=None):
        """
        Initializes the AssistantManager with the path to the RS3 document.

        Args:
            rs3_document_path (str): The path to the RS3 document.
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Parse the RS3 document content
        if rs3_document_path:
            self.rs3_document_content = rs3.parse_document(rs3_document_path)
        else:
            self.rs3_document_content = None
        # Load existing assistants from a JSON file
        self.load_existing_assistants()

    def load_existing_assistants(self):
        """
        Loads existing assistants from a JSON file.
        """
        with open("assistant_ids.json", "r") as f:
            data = json.load(f)
        # Convert the list of assistants into a dictionary for easy access
        self.existing_assistants = {
            assistant["name"]: assistant["id"] for assistant in data["assistants"]
        }

    def create_or_get_assistant(self, name, instructions):
        """
        Creates or retrieves an assistant based on its name.

        Args:
            name (str): The name of the assistant.
            instructions (str): The instructions for the assistant.

        Returns:
            None
        """
        if name in self.existing_assistants:
            # Retrieve an existing assistant
            self.assistant = self.client.beta.assistants.retrieve(
                self.existing_assistants[name]
            )
            print(f"Using existing assistant: {name}")
        else:
            # Create a new assistant
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model="gpt-4o",
                tools=[{"type": "file_search", "file_search": {"max_num_results": 40}}],
            )
            print(f"Created new assistant: {name}")

    def create_thread(self, user_query):
        """
        Creates a new thread with a user query.

        Args:
            user_query (str): The user's query.

        Returns:
            None
        """
        self.thread = self.client.beta.threads.create(
            messages=[{"role": "user", "content": user_query}]
        )
        print(f"Thread created: {self.thread}")
        print(self.thread.tool_resources.file_search)

    def run_thread_and_retrieve_results(self, instructions):
        """
        Runs a thread and retrieves the results.

        Args:
            instructions (str): The instructions for the thread.

        Returns:
            str: The results of the thread.
        """
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id, assistant_id=self.assistant.id
        )
        print(f"Run created: {run}")

        if run.status == "failed":
            if run.last_error and run.last_error.code == "rate_limit_exceeded":
                raise RuntimeError(
                    "API quota exceeded. Please check your plan and billing details."
                )
            else:
                raise RuntimeError(
                    f"Run failed with error: {run.last_error.message if run.last_error else 'Unknown error'}"
                )

        messages = list(
            self.client.beta.threads.messages.list(
                thread_id=self.thread.id, run_id=run.id
            )
        )
        print(f"Messages retrieved: {messages}")

        if not messages:
            raise ValueError("No messages retrieved from the thread.")

        message_content = messages[0].content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = self.client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        if instructions == "extract_requirements":
            print("Requirements extracted.")

        return message_content.value


def process_prompt(
    assistant_manager,
    assistant_name,
    instructions,
    chat,
    *file_paths,
    requirements=None,
    report=None,
    email_info=None,
):
    """
    Processes a prompt using the AssistantManager.

    Args:
        assistant_manager (AssistantManager): The AssistantManager instance.
        assistant_name (str): The name of the assistant.
        instructions (str): The instructions for the assistant.
        chat (str): The chat message.
        file_paths (list): A list of file paths to additional content.
        requirements (str, optional): The requirements to include in the chat. Defaults to None.

    Returns:
        str: The results of the prompt processing.
    """
    global results
    rs3.load_patterns("patterns_and_capabilities.yaml")
    full_instructions = rs3.patterns["patterns"][instructions]
    # Get RS3 content from the assistant manager instance
    rs3_content = assistant_manager.rs3_document_content
    # Parse the additional content and append to the chat message
    # Check if email_info is provided
    if email_info:
        # If email_info is present, don't include rs3_content in the chat
        chat = f"{chat}"
    else:
        # If no email_info, include rs3_content as before
        chat = f"{chat}\n\nRS3 Document Content:\n{rs3_content}"
    for file_path in file_paths:
        with open(file_path, "r") as file:
            chat += f"\n\nAdditional Content from {file_path}:\n{file.read()}"
    if requirements:
        chat += f"\n\nRequirements:\n{requirements}"
    if report:
        chat += f"\n\n\nFull RS3 Analysis Report:\n{report}"
    if email_info:
        chat += f"\n\nEmail Info:\n{email_info}"
    # Create (most times get) assistant
    assistant_manager.create_or_get_assistant(assistant_name, full_instructions)
    # Create the chat thread with our query & content
    assistant_manager.create_thread(chat)
    results = assistant_manager.run_thread_and_retrieve_results(instructions)
    return results


def generate_report(rs3_file_path, pickle_file_path):
    import amendment_handler as amend

    """
    Generates a report based on the provided RS3 file and pickle file.

    Args:
        rs3_file_path (str): Path to the RS3 file.
        pickle_file_path (str): Path to the pickle file.

    Returns:
        None
    """
    print("Starting report generation...")

    # Get the directory of the current script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Base directory: {base_dir}")

    # Create a single instance of AssistantManager
    assistant_manager = AssistantManager(rs3_file_path)
    print("AssistantManager created")

    # Create a single instance of AmendmentHandler
    amendment_handler = amend.AmendmentHandler(pickle_file_path)
    print("AmendmentHandler created")

    # Process different prompts to analyze the RS3
    print("Starting to process prompts...")

    rs3_number = process_prompt(
        assistant_manager, "Extract RS3 Number", "rs3_number", "What is the RS3 number?"
    )
    print(f"RS3 Number: {rs3_number}")

    requirements = process_prompt(
        assistant_manager,
        "Extract Requirements",
        "extract_requirements",
        "What are the requirements in the RS3?",
    )
    print("Requirements extracted")

    title = process_prompt(
        assistant_manager,
        "Generate Title",
        "task_1",
        "What is the title, task order summary, and NAICS code from the document?",
    )
    print("Title generated")

    analyze_fit = process_prompt(
        assistant_manager,
        "Analyze Fit",
        "task_2",
        "Analyze the fit of the document with the capability statement, and the 7 core capabilities.",
        os.path.join(base_dir, "context", "capability_statement.md"),
        os.path.join(base_dir, "context", "core_capabilities.md"),
    )
    print("Fit analyzed")

    matches = process_prompt(
        assistant_manager,
        "Find Matches",
        "task_3",
        "Look for a match for each requirement/ task with Barbaricum's Capabilities.",
        os.path.join(base_dir, "context", "core_capabilities.md"),
        os.path.join(base_dir, "context", "barbaricum_2_pager.md"),
        requirements=requirements,
    )
    print("Matches found")

    keywords = process_prompt(
        assistant_manager,
        "Identify Keywords",
        "task_5",
        "Identify matches in the RS3 document with the keywords.txt, locations.txt, and account_plans.txt files. Do not make note of a keyword/ location/ account plan UNLESS IT IS EXPLICITLY MENTIONED IN THE RS3 DOCUMENT.",
        os.path.join(base_dir, "context", "keywords.txt"),
        os.path.join(base_dir, "context", "locations.txt"),
        os.path.join(base_dir, "context", "account_plans.txt"),
    )
    print("Keywords identified")

    scope = process_prompt(
        assistant_manager,
        "Analyze Scope",
        "task_4",
        "Analyze the scope of work of the document to see if the tasks match the work scope summary.",
        requirements=requirements,
    )
    print("Scope analyzed")

    past_performance = process_prompt(
        assistant_manager,
        "Compare Past Performance",
        "task_6",
        "Compare the past performance of Barbaricum with the past performance files in your knowledge base. If you find a match, make note of it and the document it is from so that Barbaricum can use them as references when writing a report on this RS3 to the government/ the client.",
    )
    print("Past performance compared")

    report = f"#{amendment_handler.extract_rs3_number()} - {amendment_handler.extract_rs3_type()}\n{title}\n{analyze_fit}\n{matches}\n{keywords}\n{scope}\n{past_performance}"
    print("Report generated")

    # Analyze the report to see if it is a bid or no bid
    analyze_bid = process_prompt(
        assistant_manager,
        "RS3 Bid",
        "analyze_bid",
        "Analyze whether or not Barbaricum should Bid this RS3 opportunity.",
        report=report,
    )
    print("Bid analysis completed")

    if "OVERALL_RECOMMENDATION=BID" in analyze_bid:
        recommend_bid = True
    elif "OVERALL_RECOMMENDATION=NO_BID" in analyze_bid:
        recommend_bid = False
    else:
        recommend_bid = "Unknown"

    # Append the recommendation to the beginning of the report
    if recommend_bid:
        report = f"# Barbaricum AI Recommendation: Bid\n{report}"
    elif recommend_bid == "Unknown":
        report = f"# Barbaricum AI Recommendation: Unknown\n{report}"
    else:
        report = f"# Barbaricum AI Recommendation: No Bid\n{report}"

    rs3_file = rs3.save_report_to_pdf(report, amendment_handler.extract_rs3_number())
    print("Report saved to PDF")

    print("Report generation completed")

    return rs3_file, recommend_bid


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a report based on RS3 and pickle files."
    )
    parser.add_argument("rs3_file_path", nargs="?", help="Path to the RS3 file")
    parser.add_argument("pickle_file_path", nargs="?", help="Path to the pickle file")
    args = parser.parse_args()

    if args.rs3_file_path and args.pickle_file_path:
        # Run with command-line arguments
        generate_report(args.rs3_file_path, args.pickle_file_path)
    else:
        # Run interactively
        rs3_file_path = input("Enter the path to the RS3 file: ")
        pickle_file_path = input("Enter the path to the pickle file: ")
        generate_report(rs3_file_path, pickle_file_path)


if __name__ == "__main__":
    main()
