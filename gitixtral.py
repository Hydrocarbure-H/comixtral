import subprocess
import requests
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv
import sys

load_dotenv()

MIXTRAL_API_URL: str = "https://api.mistral.ai/v1/chat/completions"
MIXTRAL_API_KEY: str = os.getenv("MIXTRAL_API_KEY")

GIT_DIFF_LIMIT: int = 8000  
MISTRAL_RESPONSE_LIMIT: int = 2000

def is_gh_installed() -> bool:
    """
    Check if the GitHub CLI (gh) is installed.

    Returns:
        bool: True if gh is installed, False otherwise.
    """
    try:
        subprocess.run(["gh", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def get_current_branch_name() -> str:
    """
    Get the current Git branch name.

    Returns:
        str: The name of the current branch.
    """
    try:
        result: subprocess.CompletedProcess = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting current branch name: {e}")
        return ""


def get_git_diff(base_branch: str) -> str:
    """
    Get the diff of all changes made on the current branch since its creation.

    Args:
        base_branch (str): The branch to compare against.

    Returns:
        str: The git diff of all changes made on the current branch.
    """
    try:
        result: subprocess.CompletedProcess = subprocess.run(
            ["git", "--no-pager", "diff",  f"{base_branch}..."],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return ""


def generate_pr_details(diff: str) -> Dict[str, str]:
    """
    Generate a pull request title and description using the Mistral AI API based on the provided git diff.

    Args:
        diff (str): The git diff of the staged changes.

    Returns:
        Dict[str, str]: A dictionary containing the generated title and description.
    """
    # Limit the length of the diff to GIT_DIFF_LIMITx characters
    truncated_diff: str = diff[:GIT_DIFF_LIMIT]
    if len(diff) > GIT_DIFF_LIMIT:
        truncated_diff += "\nand some other things."

    # Headers for API requests
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MIXTRAL_API_KEY}",
    }

    # Generate PR description first
    description_data: Dict[str, Any] = {
        "model": "codestral-latest",
        "messages": [
            {
                "role": "user",
                "content": f"Given all the following code changes in a git diff: \n\n{truncated_diff}\n\nplease generate a pull request description. The description has to be concise and to the point, and it has to be written in a way that is easy to understand for non-technical people. If that's relevant, you have to use bullet points and markdown formatting. YOUR ANSWER MUST ONLY HAVE THE DESCRIPTION AS OUTPUT.",
            }
        ],
        "temperature": 0.7,
        "top_p": 1,
        "max_tokens": MISTRAL_RESPONSE_LIMIT,
        "stream": False,
        "safe_prompt": False,
        "random_seed": 1337,
    }

    result = {"title": "", "description": ""}

    try:
        # Get description first
        desc_response: requests.Response = requests.post(
            MIXTRAL_API_URL, headers=headers, data=json.dumps(description_data)
        )
        desc_response.raise_for_status()
        desc_json = desc_response.json()
        result["description"] = str(desc_json["choices"][0]["message"]["content"].strip())
        
        # Use the generated description to create a better title
        title_data: Dict[str, Any] = {
            "model": "codestral-latest",
            "messages": [
                {
                    "role": "user",
                    "content": f"Given the following pull request description: \n\n{result['description']}\n\nplease generate a concise and clear pull request title that summarizes the changes. Your answer must be in the format of 'feat(scope): title'. YOUR ANSWER MUST ONLY HAVE THE TITLE AS OUTPUT.",
                }
            ],
            "temperature": 0.7,
            "top_p": 1,
            "max_tokens": 100,
            "stream": False,
            "safe_prompt": False,
            "random_seed": 1337,
        }

        # Get title based on the description
        title_response: requests.Response = requests.post(
            MIXTRAL_API_URL, headers=headers, data=json.dumps(title_data)
        )
        title_response.raise_for_status()
        title_json = title_response.json()
        result["title"] = str(title_json["choices"][0]["message"]["content"].strip())

        return result
    except requests.RequestException as e:
        print(f"Error calling Mistral API: {e}")
        return result

def create_pull_request(base_branch: str) -> None:
    """
    Create a pull request from the current branch into the specified base branch.

    Args:
        base_branch (str): The branch to merge into.
    """
    if not is_gh_installed():
        print("Error: GitHub CLI (gh) is not installed.")
        return

    current_branch = get_current_branch_name()
    if not current_branch:
        print("Error: Could not determine the current branch.")
        return

    # Get the diff
    diff: str = get_git_diff(base_branch)
    if not diff:
        print("No changes found for the pull request.")
        return

    while True:
        # Generate PR details
        pr_details: Dict[str, str] = generate_pr_details(diff)
        if not pr_details["title"] or not pr_details["description"]:
            print("Failed to generate PR details.")
            return

        # Display the PR title and description and ask for confirmation
        print(f"Title: \033[1;97m{pr_details['title']} \033[0m")
        print(f"Description: \033[1;97m{pr_details['description']} \033[0m")
        confirmation: str = input("Is that ok? (Y/n): ")
        
        if confirmation.lower() == "y" or confirmation == "":
            break
        elif confirmation.lower() == "n":
            # Re-run the process if user presses 'n'
            continue
        else:
            # Return if user presses any other key
            return

    # Create the pull request using gh CLI
    try:
        subprocess.run([
            "gh", "pr", "create",
            "--base", base_branch,
            "--head", current_branch,
            "--title", pr_details["title"],
            "--body", pr_details["description"]
        ], check=True)
        print("Pull request created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating pull request: {e}")


def main(base_branch: str) -> None:
    """
    Main function to execute the script.

    Args:
        base_branch (str): The branch to merge into.
    """
    create_pull_request(base_branch)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: gitixtral <base-branch>")
    else:
        main(sys.argv[1]) 