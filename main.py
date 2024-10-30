"""
Main entry point for the RS3 proposal processing system.
Orchestrates the execution of all processing steps.
"""

import logging
from proposal_system.proposal_system import (
    s3_and_df_creation,
    print_rs3_folders_df_status,
    run_email_classifier,
    print_email_classifier_results,
    run_file_classifier,
    print_rs3_files,
    prepare_files_for_report_generation,
    generate_reports,
    prepare_files_for_amendment_handling,
    generate_amendment_reports,
    save_reports_to_s3,
    send_email,
    archive_root_files,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_all_steps():
    """Execute all steps of the RS3 processing pipeline.

    This function orchestrates the entire process from checking S3 folders
    to archiving the processed files.
    """
    try:
        # Initialize global DataFrame
        logger.info("Step 1: Checking S3 folders and creating DataFrame...")
        s3_and_df_creation()
        print_rs3_folders_df_status()

        # Run Email Classification
        logger.info("Step 2: Running email classification...")
        run_email_classifier()
        print_email_classifier_results()

        # File Classification for Report Pipeline
        logger.info("Step 3a: Running file classification for new reports...")
        run_file_classifier()
        print_rs3_files()

        # Report Generation
        logger.info("Step 4a: Generating reports...")
        prepare_files_for_report_generation()
        generate_reports()

        # Amendment Pipeline
        logger.info("Step 3b: Processing amendments...")
        prepare_files_for_amendment_handling()
        generate_amendment_reports()

        # Save and Send Reports
        logger.info("Step 4: Saving reports to S3...")
        save_reports_to_s3("rs3-files")
        
        logger.info("Step 5: Sending email notifications...")
        send_email()

        # Archive Files
        logger.info("Step 6: Archiving processed files...")
        archive_root_files("rs3-files")

        logger.info("RS3 processing pipeline completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return False

def main():
    """Main entry point for the RS3 processing pipeline."""
    logger.info("Starting RS3 processing pipeline...")
    
    success = run_all_steps()
    
    if success:
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline failed to complete.")
        exit(1)

if __name__ == "__main__":
    main() 