import sys
import boto3
from botocore.exceptions import ClientError
from proposal_system import (
    unarchive_files,
    run_all_steps,
    BUCKET_NAME,
    archive_root_files,
    manage_folder_archives,
)

# Initialize S3 client
s3 = boto3.client("s3")


# Utility functions for formatting output
def print_header(title):
    print("\n" + "=" * 60)
    print(f"{title:^60}")
    print("=" * 60)


def print_footer():
    print("=" * 60)


# Input validation functions
def get_user_input(prompt, validator):
    while True:
        try:
            user_input = input(prompt)
            validated_input = validator(user_input)
            return validated_input
        except ValueError as e:
            print(f"Invalid input: {e}")


def validate_positive_int(value):
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError("Please enter a positive integer.")
        return int_value
    except ValueError:
        raise ValueError("Please enter a valid integer.")


def validate_menu_choice(value, options):
    if value not in options:
        raise ValueError(f"Please enter a valid option.")
    return value


# Function to get appropriate emoji for file types
def get_file_emoji(filename):
    if filename.endswith("/"):
        return "📁"
    elif filename.endswith(".pkl"):
        return "🥒"
    elif filename.endswith(".pdf"):
        return "📚"
    elif filename.endswith(".docx"):
        return "📝"
    elif filename.endswith(".xlsx"):
        return "📊"
    else:
        return "📎"


# Function to handle unarchiving files
def unarchive_files_menu():
    print_header("Unarchive Files")
    num_folders = get_user_input(
        "Enter the number of folders to unarchive: ", validate_positive_int
    )
    print(f"Unarchiving files from {num_folders} folders...")
    unarchive_files(num_folders)
    print("Unarchiving complete.")
    print_footer()
    input("Press Enter to return to the S3 File Manager...")


# Function to run S3 report generation
def run_s3_report_generation():
    print_header("S3 Report Generation")
    print("Running S3 Report Generation...")
    run_all_steps()
    print("S3 Report Generation completed.")
    print_footer()
    input("Press Enter to return to the main menu...")


# Function to list S3 bucket contents
def list_s3_contents(prefix=""):
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix, Delimiter="/")

        print_header(f"S3 File Manager - Contents of s3://{BUCKET_NAME}/{prefix}")

        items = []

        # Display file operation options based on current location
        if prefix:  # We're inside a folder
            print("a. 📥 Archive Files in this Folder")
            print("b. 📤 Unarchive Files in this Folder")
            print("c. 🔙 Go Back")
        else:  # We're at the root
            print("a. 📤 Unarchive Files")
            print("b. 📥 Archive All Files")
            print("c. 🔙 Back to Main Menu")
        print("-" * 60)

        # Add option to go back if in a subfolder
        if prefix:
            print("1. 📁 ..")
            items.append("..")

        # List folders and files
        idx = 1 if prefix else 0  # Start index at 1 if in a subfolder, 0 if at root
        if "CommonPrefixes" in response:
            for obj in response["CommonPrefixes"]:
                idx += 1
                relative_path = (
                    obj["Prefix"][len(prefix) :] if prefix else obj["Prefix"]
                )
                print(f"{idx}. {get_file_emoji(obj['Prefix'])} {relative_path}")
                items.append(obj["Prefix"])

        if "Contents" in response:
            for obj in response["Contents"]:
                if obj["Key"] != prefix:
                    idx += 1
                    relative_path = obj["Key"][len(prefix) :] if prefix else obj["Key"]
                    print(f"{idx}. {get_file_emoji(obj['Key'])} {relative_path}")
                    items.append(obj["Key"])

        print_footer()

        return items
    except ClientError as e:
        print(f"Error accessing S3: {e}")
        return None


# Function to view contents of a file
def view_file_content(key):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        content = response["Body"].read().decode("utf-8")
        print_header(f"Content of {key}")
        content_lines = content.split("\n")[:20]  # Display first 20 lines
        for line in content_lines:
            print(line)
        if len(content_lines) == 20:
            print("...(content truncated)...")
        print_footer()
        input("Press Enter to return to the navigator...")
    except ClientError as e:
        print(f"Error accessing file: {e}")
        print_footer()
        input("Press Enter to return to the navigator...")


# Main S3 file manager function
def s3_file_manager():
    current_prefix = ""
    while True:
        items = list_s3_contents(current_prefix)
        if not items:
            break

        choice = input("\nEnter your choice (a/b/c or item number): ").strip().lower()

        # Handle file operations (archive/unarchive)
        if choice in ["a", "b"]:
            if current_prefix:
                action = "archive" if choice == "a" else "unarchive"
                action_ing = (
                    f"{action[:-1]}ing" if action.endswith("e") else f"{action}ing"
                )
                print(f"{action_ing.capitalize()} files in folder {current_prefix}...")
                manage_folder_archives(BUCKET_NAME, current_prefix, action)
                print(f"{action_ing.capitalize()} complete.")
                continue
            else:
                if choice == "a":
                    print("Unarchiving files...")
                    num_folders = get_user_input(
                        "Enter the number of folders to unarchive: ",
                        validate_positive_int,
                    )
                    unarchive_files(num_folders)
                    print("Unarchiving complete.")
                else:
                    print("Archiving all files...")
                    archive_root_files(BUCKET_NAME)
                    print("Archiving complete.")
                continue
        # Handle navigation
        elif choice == "c":
            if current_prefix:
                current_prefix = "/".join(current_prefix.split("/")[:-2]) + "/"
                if current_prefix == "/":
                    current_prefix = ""
            else:
                break
        elif choice.isdigit():
            idx = int(choice) - 1  # Subtract 1 to correct the indexing for selection
            if 0 <= idx < len(items):
                selected = items[idx]
                if selected == "..":
                    current_prefix = "/".join(current_prefix.split("/")[:-2]) + "/"
                    if current_prefix == "/":
                        current_prefix = ""
                elif selected.endswith("/"):
                    current_prefix = selected
                else:
                    view_file_content(selected)
            else:
                print("Invalid selection. Please try again.")
        else:
            print("Invalid input. Please enter 'a', 'b', 'c', or a number.")


# Main menu function
def main_menu():
    while True:
        print_header("cbrane S3 Nexus - Main Menu")
        print("1. 🗂️  S3 File Manager")
        print("2. 📊 Run RS3 Report Generation")
        print("3. 🚪 Exit")
        print_footer()

        choice = get_user_input(
            "Enter your choice (1-3): ",
            lambda x: validate_menu_choice(x, ["1", "2", "3"]),
        )

        if choice == "1":
            s3_file_manager()
        elif choice == "2":
            run_s3_report_generation()
        else:
            print_header("Exiting cbrane S3 Nexus")
            print("Thank you for using cbrane S3 Nexus. Goodbye!")
            print_footer()
            sys.exit(0)


# Main entry point
if __name__ == "__main__":
    print_header("Welcome to the cbrane S3 Nexus")
    print("Your gateway to seamless file management and processing.")
    print_footer()
    main_menu()
