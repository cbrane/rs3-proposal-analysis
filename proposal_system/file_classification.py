import os
import boto3
import re

def is_rs3_report_by_name(file_name):
    # Strong positive patterns (these can override 'attachment' and 'fopr')
    # These patterns are highly indicative of RS3 reports
    strong_positive_patterns = [
        r'RFI',
        r'Request for Information',
        r'DRFP',
        r'Draft RFP',
        r'Draft Request for Proposal',
        r'RFP',
        r'Request for Proposal',
        r'PWS',
        r'Performance Work Statement'
        r'SOW',
        r'Statement of Work'
    ]
    
    # Weak positive patterns (these don't override 'attachment' or 'fopr')
    # These patterns suggest RS3 reports but are not definitive
    weak_positive_patterns = [
        r'RS3',
        r'Responsive Strategic Sourcing for Services'
    ]
    
    # Negative patterns (excluding 'fopr' and 'attachment' as they're handled separately)
    # These patterns indicate the file is likely not an RS3 report
    negative_patterns = [
        r'amendment',
        r'questions',
        r'answers',
        r'Q&A',
        r'Q & A',
        r'industry',
        r'amend',
        r'CDRL',
        r'rev',
        r'revision',
        r'cover letter',
        r'labor',
        r'v2'
    ]
    
    # Check for matches using case-insensitive regular expressions
    strong_positive_match = any(re.search(pattern, file_name, re.IGNORECASE) for pattern in strong_positive_patterns)
    weak_positive_match = any(re.search(pattern, file_name, re.IGNORECASE) for pattern in weak_positive_patterns)
    negative_match = any(re.search(pattern, file_name, re.IGNORECASE) for pattern in negative_patterns)
    attachment_match = re.search(r'attachment', file_name, re.IGNORECASE)
    fopr_match = re.search(r'fopr', file_name, re.IGNORECASE)
    
    # Decision logic for classifying files
    if negative_match:
        return False, "File name contains negative patterns"
    elif strong_positive_match:
        return True, "File name contains strong RS3 indicator"
    elif weak_positive_match and not attachment_match and not fopr_match:
        return True, "File name contains weak RS3 indicator and is not an attachment or fopr"
    elif fopr_match and not strong_positive_match:
        return False, "File contains 'fopr' without strong RS3 indicator"
    else:
        return False, "File name does not match RS3 patterns or is an attachment/fopr without strong indicators"


def classify_files(bucket_name, folder_name):
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    # List objects in the specified S3 bucket and folder
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
    
    rs3_files = []
    
    # Iterate through each object in the S3 bucket
    for obj in response.get('Contents', []):
        file_name = obj['Key']
        
        # Filter for .docx and .pdf files only
        if not (file_name.endswith('.docx') or file_name.endswith('.pdf')):
            print(f"Skipping {file_name}: Not a .docx or .pdf file")
            continue
        
        # Classify the file based on its name
        is_rs3, reason = is_rs3_report_by_name(file_name)
        if is_rs3:
            print(f"RS3 report found: {file_name}")
            print(f"Reason: {reason}")
            rs3_files.append(file_name)
        else:
            print(f"Not an RS3 report: {file_name}")
            print(f"Reason: {reason}")
    
    return rs3_files

def main():
    # S3 bucket and folder configuration
    bucket_name = 'rs3-files'
    folder_name = 'RS3-24-0023/'
    
    # Classify files and get list of RS3 reports
    rs3_files = classify_files(bucket_name, folder_name)
    
    # Print results
    if rs3_files:
        print(f"\nFound {len(rs3_files)} RS3 file(s):")
        for file in rs3_files:
            print(f"- {file}")
    else:
        print("No RS3 files found in the specified location.")

if __name__ == "__main__":
    main()