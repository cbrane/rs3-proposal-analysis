# RS3 Document Analysis and Processing System
by Connor Raney - https://github.com/cbrane

## Table of Contents
1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
   - [Main Script](#main-script)
   - [S3 CLI Tool](#s3-cli-tool)
6. [Key Components](#key-components)
7. [Testing](#testing)
8. [Context Files](#context-files)
9. [Maintenance and Troubleshooting](#maintenance-and-troubleshooting)

## Overview

This project is an automated system for analyzing and processing RS3 (Responsive Strategic Sourcing for Services) documents. It was originally developed for Barbaricum during the summer of 2024 for proposal analysis. All sensitive details, including Barbaricum-specific documents and information, have been removed from this public repository. Any information in the context folder or elsewhere is LLM-generated example data meant to serve as a template.

**Important Note:** This repository is a demonstration of work completed during my summer internship and is not intended to be a production-ready solution. While the core logic and implementation are present, this version would require additional configuration, testing, and adjustments to be deployment-ready. There may be some errors in this public version due to the restructuring and removal of company-specific information, but the original project was fully polished and operational for Barbaricum. The primary purpose of this repository is to showcase the approach taken for document analysis using LLMs and serve as a reference for similar implementations.

The system leverages AI-powered assistants to extract information, classify documents, and generate reports. It integrates with AWS S3 for file storage and management. While this repository demonstrates how an organization can leverage LLMs for document analysis, it was specifically developed for Barbaricum's needs. Organizations wanting to use this system will need to configure their own prompts, context files, and classification logic to match their specific requirements.

Key features include:
- Document classification and analysis
- Email classification for identifying new RS3 reports
- Amendment handling for existing RS3 documents
- Report generation based on document analysis
- S3 bucket management and file operations

## Project Structure

```
├── main.py                # Main processing script
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
├── s3cli.py              # AWS S3 CLI tool
│
└── proposal_system/       # Core system package
    ├── context/          # Context files for analysis
    │   ├── account_plans.txt
    │   ├── barbaricum_2_pager.md
    │   ├── capability_statement.md
    │   ├── core_capabilities.md
    │   ├── keywords.txt
    │   └── locations.txt
    │
    ├── amendment_handler.py    # Handles amendments to RS3 documents
    ├── assistant_ids.json      # JSON file containing existing assistant IDs to reuse
    ├── email_classifier.py     # Classifies emails for new RS3 reports 
    ├── file_classification.py  # Classifies files in S3 buckets
    ├── patterns_and_capabilities.yaml  # Configuration for prompts used in the project
    ├── proposal_system.py      # Core system functionality
    ├── report_generator.py     # Generates analysis reports
    └── rs3_analysis.py        # Core analysis functions for RS3 documents
```

## Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd evaluation
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Set up AWS CLI credentials:
   - Install the AWS CLI if you haven't already: `pip install awscli`
   - Configure AWS CLI with your credentials:
     ```
     aws configure
     ```
   - Enter your AWS Access Key ID, Secret Access Key, default region, and output format when prompted.
   - This configuration will allow boto3 to use these credentials for both the main script and the AWS CLI tool.

2. Configure OpenAI Assistants:
   - Create your assistants in the OpenAI platform
   - Update `proposal_system/assistant_ids.json` with your assistant IDs
   - Each assistant ID starts with `asst_` and can be found in your OpenAI dashboard

3. Ensure all necessary context files are present in the `proposal_system/context/` directory.

4. Set up environment variables for API keys or sensitive information (e.g., OpenAI API key):
   ```
   export OPENAI_API_KEY='your_openai_api_key_here'
   ```

## Usage

### Main Script

The `main.py` is the core of the system. It orchestrates the entire process of document analysis and report generation.

To run the main script:

```
python mainscript.py
```

This will:
1. Check S3 buckets for new files
2. Classify emails and documents
3. Process amendments if necessary
4. Generate reports for new RS3 documents
5. Update S3 buckets with results

### S3 CLI Tool

The `s3cli.py` provides a command-line interface for managing S3 buckets and generating reports. This tool serves as a central hub for:
- Managing RS3 files stored in S3 buckets
- Generating analysis reports from RS3 documents already in S3
- Organizing and archiving proposal documents
- Streamlining the document analysis workflow
<img width="799" alt="image" src="https://github.com/user-attachments/assets/c905f033-a0cb-42aa-8033-fc584216abc7">



To use the S3 CLI tool:

```
python s3cli.py
```

The tool provides an interactive menu with options to:
1. **S3 File Manager**: Navigate and manage files in your S3 buckets
   - List bucket contents
   - Upload/download files
   - Archive or unarchive files
   - Organize proposal documents

2. **Run RS3 Report Generation**: Generate analysis reports for RS3 documents
   - Process RS3 documents stored in S3
   - Generate detailed analysis reports
   - Extract key information automatically
   - Apply AI-powered document analysis

3. **Exit**: Safely exit the application

This tool is designed to make it easy to manage your RS3 documents and generate reports without needing to directly interact with AWS S3 commands or write custom scripts.

## Key Components

1. **Amendment Handler** (`proposal_system/amendment_handler.py`):
   - Processes amendments to existing RS3 documents
   - Extracts key information from amendment emails

2. **Email Classifier** (`proposal_system/email_classifier.py`):
   - Classifies incoming emails to identify new RS3 reports
   - Uses AI to analyze email content
   - Note: Email classification patterns are currently configured for specific organizational needs. Other organizations may need to modify the classification logic and patterns to match their email structure and naming conventions.

3. **File Classification** (`proposal_system/file_classification.py`):
   - Classifies files in S3 buckets
   - Identifies RS3 reports based on file names and patterns
   - Note: File classification rules are organization-specific. The code may need to be modified to match different file naming conventions, directory structures, or document types used by other organizations.

4. **RS3 Analysis** (`proposal_system/rs3_analysis.py`):
   - Core functions for parsing and loading documents
   - Handles document format conversion (e.g., DOCX to PDF)
   - Manages report directory creation and file organization
   - Provides utility functions for text extraction and processing

5. **Report Generator** (`proposal_system/report_generator.py`):
   - Core functions for analyzing RS3 documents
   - Extracts requirements, analyzes scope, and generates report content

6. **Patterns and Capabilities** (`proposal_system/patterns_and_capabilities.yaml`):
   - Repository of prompts used in the project
   - Note: Actual prompt updates should be made in the OpenAI assistants console
   - Serves as a reference for the project's AI interactions
   - Maintained for historical context and documentation purposes
   - Our prompts are in the format of 'patterns' from the project: https://github.com/danielmiessler/fabric. These prompts are also organization-specific and may need to be modified for other organizations.

### Testing Report Generation

To generate a test report:

1. Use the `proposal_system/report_generator.py` file.
2. Hardcode a test PDF or DOCX file path that is in the evaluation directory locally.
3. Run the script to test the generation of a report.

### Testing the Main Script

To test `main.py`:

1. Prepare test files:
   - Option 1: Use the AWS S3 CLI tool to unarchive a folder of files for testing.
   - Option 2: If there are already unprocessed files in S3, you can use those.

2. Run `main.py`:
   - It will check S3 for unarchived files.
   - It will process these files to create reports or amendment reports.

This approach allows for multiple tests without waiting for new items from the government, giving you control over your testing scenarios.

## Context Files

The `proposal_system/context/` directory contains essential files used in the analysis process:

- `account_plans.txt`: List of account plans
- `barbaricum_2_pager.md`: Barbaricum's capabilities overview
- `capability_statement.md`: Detailed capability statement
- `core_capabilities.md`: Core capabilities of the organization
- `keywords.txt`: Key terms for document analysis
- `locations.txt`: Relevant locations for the project

These files are crucial for accurate document analysis and should be kept up-to-date.

## Maintenance and Troubleshooting

- Regularly update the context files to ensure accurate analysis
- Monitor S3 bucket usage and clean up old files periodically
- Check logs for any errors in the main script or S3 CLI tool
- If you want to change the models for the assistants, please make these changes in the OpenAI Assistants console

---

This README provides an overview of the RS3 Document Analysis and Processing System. For detailed information on specific components, please refer to the individual script files and their inline documentation.
