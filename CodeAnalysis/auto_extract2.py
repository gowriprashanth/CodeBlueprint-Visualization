import os
import ast
import json
import requests
import subprocess
import shutil
import tarfile

def checkout_commit(commit_hash):
    
    subprocess.run(['git', 'checkout', commit_hash], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def extract_project_attributes(project_directory,commit_sha, repo_owner, repo_name):
    class_attributes = {
        "commit_message":"",
        "lines_of_code": 0,
        "num_classes": 0,
        "num_methods": 0,
        "num_variables": 0,
        "classes": {}
    }

    # GitHub API base URL
    BASE_URL = 'https://api.github.com'
    
    # Fetch commit information
    commit_url = f'{BASE_URL}/repos/{repo_owner}/{repo_name}/commits/{commit_sha}'
    commit_response = requests.get(commit_url)
    commit_data = commit_response.json()
    
    # Extract commit message
    commit_message = ""
    if "commit" in commit_data and "message" in commit_data["commit"]:
        commit_message = commit_data["commit"]["message"]
    class_attributes["commit_message"] = commit_message

    # Traverse all Python files in the project directory
    for root, _, files in os.walk(project_directory):
        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                with open(file_path, "r") as f:
                    try:
                        code_lines = f.readlines()
                        class_attributes["lines_of_code"] += len(code_lines)

                        tree = ast.parse("".join(code_lines))
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                class_name = node.name
                                class_attributes["num_classes"] += 1

                                # Class hierarchy update
                                current_class = {"methods": [], "attributes": []}
                                parent_classes = []
                                for base_class in node.bases:
                                    if isinstance(base_class, ast.Name):
                                        parent_classes.append(base_class.id)

                                if parent_classes:
                                    class_attributes["classes"].setdefault(parent_classes[0], {}).setdefault(class_name, current_class)
                                else:
                                    class_attributes["classes"][class_name] = current_class

                                # Process methods and attributes
                                for item in node.body:
                                    if isinstance(item, ast.FunctionDef):
                                        method_name = item.name
                                        class_attributes["num_methods"] += 1
                                        current_class["methods"].append(method_name)  # Add to 'current_class'
                                    elif isinstance(item, ast.Assign):
                                        for target in item.targets:
                                            if isinstance(target, ast.Name):
                                                variable_name = target.id
                                                class_attributes["num_variables"] += 1
                                                current_class["attributes"].append(variable_name)  # Add to 'current_class'
                    except SyntaxError:
                        print(f"Error parsing {file_path}. Skipping.")

    return class_attributes



def fetch_repository_files(owner, repo, commit_sha, target_dir):
    """
    Fetch repository files for a specific commit.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{commit_sha}"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with tarfile.open(fileobj=response.raw, mode="r|gz") as tar:
            tar.extractall(path=target_dir)
    else:
        print(f"Failed to fetch repository files. Status code: {response.status_code}")

def fetch_commit_hash(owner, repo, commit_number):
    """
    Fetch the commit hash for a specific commit number.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": 1, "page": commit_number}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["sha"]
        else:
            print("Commit not found.")
            return None
    else:
        print(f"Failed to fetch commit hash. Status code: {response.status_code}")
        return None



# GitHub repository information
owner = "psf"
repo = "requests"

# Take input from user for the commit number
commit_number = input("Enter commit number (1 to 6270): ")


# Fetch the commit hash for the specified commit number
commit_hash = fetch_commit_hash(owner, repo, commit_number)

selected_commit_sha = commit_hash[int(commit_number)-1]

if commit_hash:
    # Fetch repository files for the specific commit
    fetch_repository_files(owner, repo, commit_hash, "repo_files")

    project_directory = f"{owner}-{repo}-{commit_hash[:7]}"
    
    # Fetch commit messages
    #commit_messages = fetch_commit_messages(owner, repo, commit_number)

    # Extract project attributes
    attributes = extract_project_attributes("repo_files/"+project_directory,selected_commit_sha,owner,repo)

    # Output the result in JSON format
    json_output = json.dumps(attributes, indent=2)
    print(json_output)
    #print(commit_messages)
    # with open("output.json", "w") as f:
    #     f.write(json_output)
