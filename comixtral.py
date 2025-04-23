import subprocess
import requests
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

MIXTRAL_API_URL: str = "https://api.mistral.ai/v1/chat/completions"
MIXTRAL_API_KEY: str = os.getenv("MIXTRAL_API_KEY")
GIT_DIFF_LIMIT: int = 3000

def is_git_repo() -> bool:
    """
    Check if the current directory is a Git repository.

    Returns:
        bool: True if the current directory is a Git repository, False otherwise.
    """
    try:
        subprocess.run(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_git_diff() -> str:
    """
    Get the diff of the staged changes in the Git repository.

    Returns:
        str: The git diff of the staged changes.
    """
    try:
        subprocess.run(["git", "add", "."], check=True)
        result: subprocess.CompletedProcess = subprocess.run(
            ["git", "--no-pager", "diff", "--cached"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return ""


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


def generate_commit_message(diff: str) -> Dict[str, Any]:
    """
    Generate a commit message using the Mixtral API based on the provided git diff.

    Args:
        diff (str): The git diff of the staged changes.

    Returns:
        Dict[str, Any]: The response from the Mixtral API containing the generated commit message.
    """
    # Limit the length of the diff to GIT_DIFF_LIMITx characters
    truncated_diff: str = diff[:GIT_DIFF_LIMIT]
    if len(diff) > GIT_DIFF_LIMIT:
        truncated_diff += "\nand some other things."

    # Content of the message to send to the API
    data: Dict[str, Any] = {
        "model": "codestral-latest",
        "messages": [
            {
                "role": "user",
                "content": f"Given the following code changes in a git diff: \n\n{truncated_diff}\n\nplease analyze these code changes and generate a one sentence commit message that adheres to the Conventional Commits guidelines. The commit message should include an appropriate type ('feat', 'fix', 'chore', etc.), a scope, and a clear description. The format should be: <type>(<scope>): <description>. Provide a message that clearly describes the purpose of the changes, in a globally and concise manner, suitable for inclusion in the project history. Don't focus on only one code file, but on the overall changes. Your answer MUST ONLY HAVE THE COMMIT MESSAGE AS OUTPUT.",
            }
        ],
        "temperature": 0.7,
        "top_p": 1,
        "max_tokens": 200,
        "stream": False,
        "safe_prompt": False,
        "random_seed": 1337,
    }

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MIXTRAL_API_KEY}",
    }

    try:
        response: requests.Response = requests.post(
            MIXTRAL_API_URL, headers=headers, data=json.dumps(data)
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error calling Mixtral API: {e}")
        return {}


def commit_and_push(commit_message: str) -> None:
    """
    Add, commit, and push the changes with the generated commit message.

    Args:
        commit_message (str): The commit message to use for the commit.
    """
    try:
        subprocess.run(
            ["git", "commit", "-am", commit_message.replace('"', "").replace("`", "")], check=True
        )
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}")
        return


def main() -> None:
    """
    Main function to execute the script.
    """
    MODE = "ticket"  # Set the mode to 'ticket' or 'conventional'
    current_directory: str = os.getcwd()

    if not is_git_repo():
        print(f"Error: {current_directory} is not a Git repository.")
        return

    # Get the diff
    diff: str = get_git_diff()
    if not diff:
        print("No changes staged for commit.")
        return

    # Generate the commit message
    response: Dict[str, Any] = generate_commit_message(diff)
    if not response:
        print("Failed to generate commit message.")
        return

    # Extract the commit message from the API response
    try:
        commit_message: str = response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        print(f"Error extracting commit message from response: {e}")
        return

    # Check the mode and modify the commit message if necessary
    if MODE == "ticket":
        branch_name = get_current_branch_name()
        # Extract the type and ticket number from the branch name
        parts = branch_name.split("/")
        if len(parts) >= 3:
            commit_type = parts[0]
            ticket_number = parts[1]
            # Extract the description from the generated commit message
            description_start = commit_message.find("):") + 3
            description = commit_message[description_start:]
            commit_message = f"{commit_type}({ticket_number}): {description}"
        else:
            print("Branch name does not follow the expected pattern. Switching to conventional mode.")
            MODE = "conventional"

    # Display the commit message and ask for confirmation. If the confirmation is not given, re-generated the commit message.
    while True:
        commit_message = commit_message.replace('"', "").replace("`", "")
        print(f"Message: \033[1;97m{commit_message} \033[0m")
        confirmation: str = input("Is that ok? (Y/n/your message): ")
        if confirmation.lower() == "y" or confirmation == "":
            break
        elif confirmation.lower() == "n":
            response = generate_commit_message(diff)
            commit_message = response["choices"][0]["message"]["content"].strip()
        else:
            commit_message = confirmation
            break

    # Commit and push the changes
    commit_and_push(commit_message)

if __name__ == "__main__":
    main()
