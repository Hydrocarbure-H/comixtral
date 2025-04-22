import subprocess
import requests
import json
import os
import re
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


def extract_branch_info(branch_name: str) -> Dict[str, str]:
    """
    Extract branch type and ticket number from branch name.
    
    Args:
        branch_name (str): The name of the branch.
        
    Returns:
        Dict[str, str]: Dictionary containing branch type and ticket number.
    """
    result = {"type": "", "ticket": ""}
    
    # Match patterns like fix/ENG-123 or feature/ENG-456
    match = re.match(r'^([^/]+)/([A-Z]+-\d+)', branch_name)
    if match:
        result["type"] = match.group(1)
        result["ticket"] = match.group(2)
    
    return result


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


def generate_pr_details(diff: str, branch_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generate a pull request title and description using the Mistral AI API based on the provided git diff.

    Args:
        diff (str): The git diff of the staged changes.
        branch_info (Dict[str, str]): Dictionary containing branch type and ticket number.

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
                "content": f"Given all the following code changes in a git diff: \n\n{truncated_diff}\n\nplease generate a pull request description. The description has to be concise and to the point, and it has to be written in a way that is easy to understand for non-technical people. You have to use bullet points and start your answer with '### What's changed ?'. More simple and short is your answer, the better. You don't always have to use bullet points, but you should use them when the changes of the PR are really different from each other. YOUR ANSWER MUST ONLY HAVE THE DESCRIPTION AS OUTPUT.",
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
        description = str(desc_json["choices"][0]["message"]["content"].strip())
        
        # Add ticket number to the end of the description if available
        if branch_info["ticket"]:
            description += f"\n\nFixes: #{branch_info['ticket']}"
        
        result["description"] = description
        
        # Use the generated description to create a better title
        title_data: Dict[str, Any] = {
            "model": "codestral-latest",
            "messages": [
                {
                    "role": "user",
                    "content": f"Given the following pull request description: \n\n{description}\n\nplease generate a small, concise and clear pull request title that summarizes the changes. More simple and short is your answer, the better. You have to start the PR with the ticket number and the type of the PR (here it's {branch_info['type']} and {branch_info['ticket']}) with the format type(ticket): title. YOUR ANSWER MUST ONLY HAVE THIS FULL TITLE AS OUTPUT.",
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
        title = str(title_json["choices"][0]["message"]["content"].strip())
        
        # Add branch type and ticket number to the beginning of the title if available
        if branch_info["type"] and branch_info["ticket"]:
            title = f"{branch_info['type']}({branch_info['ticket']}): {title}"
        
        result["title"] = title

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
    
    # Extract branch type and ticket number
    branch_info = extract_branch_info(current_branch)

    # Get the diff
    diff: str = get_git_diff(base_branch)
    if not diff:
        print("No changes found for the pull request.")
        return

    while True:
        # Generate PR details
        pr_details: Dict[str, str] = generate_pr_details(diff, branch_info)
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