import os
import yaml
from openai import OpenAI
import docx
import PyPDF2
import markdown2
from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Global variable to store requirements
global_requirements = None

# Set OpenAI Key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_patterns(file_path):
    """Loads the patterns from the .yaml file so they can be used."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


patterns = load_patterns("patterns_and_capabilities.yaml")


def parse_docx(file_path):
    """Parses a .docx file and returns the text in the file."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        raise FileNotFoundError(
            f"The document file {file_path} does not exist or could not be read. Error: {e}"
        )


def parse_pdf(file_path):
    """Parses a .pdf file and returns the text in the file."""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        raise FileNotFoundError(
            f"The document file {file_path} does not exist or could not be read. Error: {e}"
        )


def parse_document(file_path):
    """Parses a document file and returns the text in the file."""
    if file_path.endswith(".docx"):
        return parse_docx(file_path)
    elif file_path.endswith(".pdf"):
        return parse_pdf(file_path)
    else:
        raise ValueError("Unsupported file format. Please use .docx or .pdf files.")


def get_rs3_number(document, patterns):
    """Gets the RS3 number from the document."""
    pattern = patterns["patterns"]["rs3_number"]
    prompt = f"{pattern}\n\n{document}"
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def task_1(document, patterns):
    """Generates the title, summary, type, and NAICS code from the document.
    Takes the RS3 Document as context."""
    pattern = patterns["patterns"]["task_1"]
    prompt = f"{pattern}\n\n{document}"
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def extract_requirements(document, patterns):
    """Extracts the requirements from the document. Sets the results as a
    global variable.
    Takes the RS3 Document as context."""
    global global_requirements
    pattern = patterns["patterns"]["extract_requirements"]
    prompt = f"{pattern}\n\n{document}"
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    global_requirements = response.choices[0].message.content.strip()
    return global_requirements


def task_2(document, patterns):
    """Analyzes the fit of the document with the capability statement,
    and the 7 core capabilities.
    Takes the RS3 Document, Capability Statement, and 7 Core Capabilities as
    context."""
    # Use the global requirements
    if global_requirements is None:
        raise ValueError("Global requirements not set. Please extract them first.")
    pattern = patterns["patterns"]["task_2"]
    capability_statement = patterns["capability_statement"]
    prompt = (
        f"{pattern}\n\n{global_requirements}\n\n{capability_statement}\n\n{document}"
    )
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def task_3(document, patterns):
    """Finds a match for each requirement/ task with Barbaricum's
    Capabilities.
    Takes the RS3 Document, List of Global Requirements/ Tasks, Core
    Capabilities, and Barbaricum's 2-pager as context."""
    if global_requirements is None:
        raise ValueError("Global requirements not set. Please extract them first.")
    pattern = patterns["patterns"]["task_3"]
    core_capabilities = patterns["core_capabilities"]
    capability_2_pager = patterns["barbaricum_2_pager"]
    prompt = f"{pattern}\n\n{global_requirements}\n\n{core_capabilities}\n\n{capability_2_pager}\n\n{document}"
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def task_4(document, patterns):
    """Analyzes the scope of work of the document to see if the tasks
    actually match the work scope summary.
    Takes the RS3 Document and List of Global Requirements/ Tasks as context."""
    if global_requirements is None:
        raise ValueError("Global requirements not set. Please extract them first.")
    pattern = patterns["patterns"]["task_4"]
    prompt = f"{pattern}\n\n{global_requirements}\n\n{document}"
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def task_5(document, patterns):
    """Identifies the RS3 specific keywords, locations, and account plans in
    the document.
    Takes the RS3 Document, RS3 Keywords, RS3 locations, and RS3 account plans
    as context."""
    pattern = patterns["patterns"]["task_5"]

    # Update paths
    context_dir = os.path.join(os.path.dirname(__file__), "context")
    
    # Read keywords from keywords.txt
    with open(os.path.join(context_dir, "keywords.txt"), "r") as file:
        keywords = file.read().splitlines()

    # Read locations from locations.txt
    with open(os.path.join(context_dir, "locations.txt"), "r") as file:
        locations = file.read().splitlines()

    # Read account plans from account_plans.txt
    with open(os.path.join(context_dir, "account_plans.txt"), "r") as file:
        account_plans = file.read().splitlines()

    prompt = f"{pattern}\n\n{keywords}\n\n{locations}\n\n{account_plans}\n\n{document}"
    response = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def save_report_to_pdf(report, rs3_number):
    """Saves the report to a PDF file."""
    # Create 'reports' directory if it doesn't exist
    if not os.path.exists("reports"):
        os.makedirs("reports")
    # Determine the file name
    base_filename = f"reports/{rs3_number}-report"
    filename = f"{base_filename}.pdf"
    count = 1
    while os.path.exists(filename):
        filename = f"{base_filename}({count}).pdf"
        count += 1
    # Convert Markdown to HTML
    html_content = markdown2.markdown(report)
    # Convert HTML to PDF with xhtml2pdf
    with open(filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(html_content, dest=result_file)
    if pisa_status.err:
        print(f"Error: {pisa_status.err}")
    else:
        print(f"Report saved to {filename}")

    return filename


def process_document(document_path, patterns):
    """Processes the document and generates the report."""
    document = parse_document(document_path)
    title_summary_type_naics = task_1(document, patterns)
    requirements = extract_requirements(document, patterns)
    fit_analysis = task_2(document, patterns)
    match_capabilities = task_3(document, patterns)
    scope_analysis = task_4(document, patterns)
    rs3_matches = task_5(document, patterns)
    report = f"""
# RS3 Analysis Report

## Title and TO Summary, RS3 Type, and NAICS Code
{title_summary_type_naics}

## Fit with Capability Statement
{fit_analysis}

## Match to Core Capabilities
{match_capabilities}

## Scope of Work Analysis
{scope_analysis}

## RS3 Specific Keywords, Locations, & Account Plans
{rs3_matches}
"""
    print(report)
    save_report_to_pdf(report, get_rs3_number(document, patterns))


def main():
    """Main function to run the program."""
    patterns = load_patterns("patterns_and_capabilities.yaml")
    document_path = "testrs3.pdf"  # Update with your test proposal document path
    report = process_document(document_path, patterns)


if __name__ == "__main__":
    main()