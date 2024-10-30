import pickle
import sys
import re
import yaml
from report_generator import process_prompt, AssistantManager
from rs3_analysis import save_report_to_pdf


class AmendmentHandler:
    """
    A class to handle amendments to RS3 documents.

    This class processes pickle data containing email information and integrates
    with the AssistantManager to analyze and handle changes in RS3 documents.
    """

    def __init__(self, pickle_file_path):
        """
                Initialize the AmendmentHandler.

                Args:
        None            pickle_file_path (str): Path to the pickle file containing email data.
        """
        self.pickle_file_path = pickle_file_path
        self.email_data = self.load_pickle_data()
        self.prompt = self.load_prompt()

    def determine_event_type(self, llm_analysis):
        """
        Determine if the event is an industry day, amendment, or other based on the LLM analysis.

        Args:
            llm_analysis (str): The analysis provided by the LLM.

        Returns:
            str: 'amendment', 'industry_day', or 'other'
        """
        lower_analysis = llm_analysis.lower()
        if "amendment" in lower_analysis:
            return "amendment"
        elif "industry day" in lower_analysis:
            return "industry_day"
        else:
            return "other"

    def load_prompt(self):
        """
        Load the prompt from the patterns_and_capabilities.yaml file.

        Returns:
            str: The prompt for RS3 email handling.
        """
        with open("patterns_and_capabilities.yaml", "r") as file:
            data = yaml.safe_load(file)
        return data["patterns"]["rs3_email"]

    def load_pickle_data(self):
        """
        Load and deserialize the pickle data.

        Returns:
            dict: The deserialized pickle data.

        Raises:
            SystemExit: If the pickle file is not found or cannot be unpickled.
        """
        try:
            with open(self.pickle_file_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"Error: Pickle file '{self.pickle_file_path}' not found.")
            sys.exit(1)
        except pickle.UnpicklingError:
            print(
                f"Error: Unable to unpickle file '{self.pickle_file_path}'. The file may be corrupted or in an incompatible format."
            )
            sys.exit(1)

    def get_email_subject(self):
        """
        Get the subject of the email.

        Returns:
            str: The email subject.
        """
        return self.email_data.get("subject", "")

    def get_email_body(self):
        """
        Get the body of the email.

        Returns:
            str: The email body.
        """
        return self.email_data.get("body", "")

    def get_combined_email_content(self):
        """
        Combine the email subject and body into a single string.

        Returns:
            str: The combined email content.
        """
        subject = self.get_email_subject()
        body = self.get_email_body()
        return f"Subject: {subject}\n\nBody:\n{body}"

    def extract_rs3_number(self):
        """
        Extract the RS3 number from the email subject.

        Returns:
            str: The RS3 number if found, else an empty string.
        """
        subject = self.get_email_subject()
        match = re.search(r"RS[23]-\d{2}-\d{4}", subject)
        return match.group(0) if match else ""

    def extract_rs3_type(self):
        """
        Extract the RS3 type from the email subject and body.

        Returns:
            str: The RS3 type if found (RFI, DRFP, or RFP), else 'Unknown'.
        """
        content = self.get_combined_email_content().upper()
        if "RFI" in content or "REQUEST FOR INFORMATION" in content:
            return "RFI"
        elif (
            "DRFP" in content
            or "DRAFT RFP" in content
            or "DRAFT REQUEST FOR PROPOSAL" in content
            or "DRAFT SOLICITATION" in content
        ):
            return "DRFP"
        elif "RFP" in content or "REQUEST FOR PROPOSAL" in content:
            return "RFP"
        elif "SOW" in content or "STATEMENT OF WORK" in content:
            return "SOW"
        elif "PWS" in content or "PERFORMANCE WORK STATEMENT" in content:
            return "PWS"
        else:
            return "Unknown"

    def get_llm_analysis(self):
        """
        Get LLM analysis of the email content using the stored prompt.

        Returns:
            str: The LLM's analysis of the email content.
        """
        email_content = self.get_combined_email_content()

        # Use the process_prompt function to get the LLM's response
        llm_response = process_prompt(
            AssistantManager(),
            "RS3 Email",
            "rs3_email",
            "Summarize the email that has the amendment or industry day.",
            email_info=email_content,
        )
        return llm_response

    def process_amendment(self):
        """
        Process the amendment to the RS3 document.

        This method implements the logic for processing amendments based on the email data
        and the RS3 document content.
        """
        print("Processing amendment...")
        rs3_number = self.extract_rs3_number()
        rs3_type = self.extract_rs3_type()

        print(f"RS3 Number: {rs3_number}")
        print(f"RS3 Type: {rs3_type}")

        # Get LLM analysis
        llm_analysis = self.get_llm_analysis()
        print("LLM Analysis:")
        print(llm_analysis)

        # Determine event type
        event_type = self.determine_event_type(llm_analysis)
        print(f"Event Type: {event_type}")

        # Save report to PDF
        filename = save_report_to_pdf(llm_analysis, f"{rs3_number}_{event_type}")
        print(f"Report saved as {filename}")  # This will now print the full path

        return filename

    def run_amendment_handler(pickle_file_path):
        handler = AmendmentHandler(pickle_file_path)
        handler.process_amendment()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 amendment_handler.py <pickle_file_path>")
        sys.exit(1)

    pickle_file_path = sys.argv[1]
    handler = AmendmentHandler(pickle_file_path)
    handler.process_amendment()
