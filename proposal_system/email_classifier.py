import pickle
import os
from openai import OpenAI

def load_pickle_file(file_path):
    # Attempt to load and return the contents of a pickle file
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print(f"Error: Pickle file '{file_path}' not found.")
        return None
    except pickle.UnpicklingError:
        print(f"Error: Unable to unpickle file '{file_path}'. The file may be corrupted or in an incompatible format.")
        return None

def get_combined_email_content(email_data):
    # Combine the subject and body of an email into a single string
    subject = email_data.get('subject', '')
    body = email_data.get('body', '')
    return f"Subject: {subject}\n\nBody:\n{body}"

def classify_email(email_content):
    # Classify an email as either a 'new RS3 report' or 'other' using OpenAI's API
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return None

    client = OpenAI(api_key=api_key)
    
    # Prepare the prompt for the AI model
    prompt = f"""
    Classify the following email as either a 'new RS3 report' or 'other':

    {email_content}
    
    Classification:
    """
    
    try:
        # Make an API call to OpenAI for classification
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """# IDENTITY and PURPOSE

You are an AI assistant specialized in classifying emails. Your primary responsibility is to accurately categorize incoming emails into two classes: 'new RS3 report' or 'other'. You have a deep understanding of RS3 reports, including RFIs, DRFPs, and RFPs, and can distinguish between new solicitations and ongoing threads, or emails that are not for a new RS3 report.

Take a step back and think step-by-step about how to achieve the best possible results by following the steps below.

# STEPS

1. Analyze the content of the email, focusing on the first message in the thread if multiple messages are present.
2. Assess whether it's the original solicitation or the original thread sending out an RS3. It must be the original information regarding the NEW solititation of an RS3, not a follow up or reply to an existing RS3. 
3. Assess whether the email has to do with an industry day, an amendment, a follow-up email, a question & answer email, or something else, these are all examples of 'other' and not of a new RS3 solititation/ report.
4. Based on the analysis, classify the email as either 'new RS3 report' or 'other'.

# Output Format:

[new RS3 report/other]

# OUTPUT INSTRUCTIONS

- Output only the classification: either "new RS3 report" or "other".
- Do not include any additional text, explanations, or formatting.

# INPUT INFO

The input will be the content of an email. Remember to base your classification on the first email message if the content contains multiple messages in a thread.

End of instructions.

# INPUT

Input: [Email content will be provided here]"""},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Process the AI's response
        classification = response.choices[0].message.content.strip().lower()
        new_report = 'new rs3 report' in classification
        
        return new_report
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        return None
    
def process_email(pickle_file_path):
    # Process a single email from a pickle file
    email_data = load_pickle_file(pickle_file_path)
    if email_data is None:
        return
    
    email_content = get_combined_email_content(email_data)
    is_new_report = classify_email(email_content)
    
    if is_new_report is not None:
        print(f"Is new RS3 report: {is_new_report}")
    else:
        print("Classification could not be performed.")

def main(pickle_file_path):
    # Main function to process an email from a pickle file
    email_data = load_pickle_file(pickle_file_path)
    if email_data is None:
        return
    
    email_content = get_combined_email_content(email_data)
    is_new_report = classify_email(email_content)
    
    if is_new_report is not None:
        print(f"Is new RS3 report: {is_new_report}")
    else:
        print("Classification could not be performed.")

if __name__ == "__main__":
    # Entry point of the script
    import sys
    if len(sys.argv) != 2:
        print("Usage: python email_classifier.py <pickle_file_path>")
        sys.exit(1)
    main(sys.argv[1])