import subprocess
import requests
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

MIXTRAL_API_URL: str = "https://api.mistral.ai/v1/chat/completions"
MIXTRAL_API_KEY: str = os.getenv("MIXTRAL_API_KEY")


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
        result: subprocess.CompletedProcess = subprocess.run(
            ["git", "--no-pager", "diff"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return ""


def generate_commit_message(diff: str) -> Dict[str, Any]:
    """
    Generate a commit message using the Mixtral API based on the provided git diff.

    Args:
        diff (str): The git diff of the staged changes.

    Returns:
        Dict[str, Any]: The response from the Mixtral API containing the generated commit message.
    """
    # Limit the length of the diff to 250 characters
    truncated_diff: str = diff[:250]
    if len(diff) > 250:
        truncated_diff += "\nand some other things."

    # Content of the message to send to the API
    data: Dict[str, Any] = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "user",
                "content": f"Given the following code changes in a git diff: \n\n{truncated_diff}\n\nplease analyze these code changes and generate a commit message that adheres to the Conventional Commits guidelines. The commit message should include an appropriate type ('feat', 'fix', 'chore', etc.), optionally a scope, and a clear description. The format should be: <type>(<scope>): <description>. Provide a message that clearly describes the purpose of the changes in a concise manner, suitable for inclusion in the project history. Your answer will only have the commit message as output.",
            }
        ],
        "temperature": 0.7,
        "top_p": 1,
        "max_tokens": 100,
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
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(
            ["git", "commit", "-m", commit_message.replace('"', "")], check=True
        )
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}")
        return


def main() -> None:
    """
    Main function to execute the script.
    """
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

    # Commit and push changes
    commit_and_push(commit_message)

    print(f"Generated and pushed commit message:\n{commit_message}")


if __name__ == "__main__":
    main()
