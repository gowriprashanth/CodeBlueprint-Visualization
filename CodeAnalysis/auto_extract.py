import ast
import json
import requests

def extract_project_attributes_from_commit(commit_sha, repo_owner, repo_name):
    class_attributes = {
        "commit_message": "",
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
    class_attributes["commit_message"] = commit_data["commit"]["message"]
    
    # Fetch file tree for the commit
    commit_files = commit_data['files']
    
    # Process each file in the commit
    for file in commit_files:
        if file['filename'].endswith(".py"):  # Only process Python files
            file_content_url = file['raw_url']
            file_content_response = requests.get(file_content_url)
            file_content = file_content_response.text
            
            try:
                code_lines = file_content.splitlines()
                class_attributes["lines_of_code"] += len(code_lines)
                
                tree = ast.parse(file_content)
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
                print(f"Error parsing {file['filename']}. Skipping.")

    return class_attributes

def get_commit_shas(repo_owner, repo_name):
    # GitHub API base URL
    BASE_URL = 'https://api.github.com'
    
    # Fetch list of commits
    commits_url = f'{BASE_URL}/repos/{repo_owner}/{repo_name}/commits'
    commits_response = requests.get(commits_url)
    commits_data = commits_response.json()
    
    # Extract commit SHAs
    commit_shas = [commit['sha'] for commit in commits_data]
    
    return commit_shas

# Repository details
repo_owner = 'psf'
repo_name = 'requests'

# Get commit SHAs
commit_shas = get_commit_shas(repo_owner, repo_name)

# Prompt user to input a commit number
while True:
    try:
        commit_number = int(input(f"Enter a commit number (1 to {len(commit_shas)}): "))
        if 1 <= commit_number <= len(commit_shas):
            selected_commit_sha = commit_shas[commit_number - 1]
            break
        else:
            print(f"Invalid commit number. Please enter a number between 1 and {len(commit_shas)}.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")

# Extract project attributes for the selected commit
attributes = extract_project_attributes_from_commit(selected_commit_sha, repo_owner, repo_name)

# Output the result in JSON format
json_output = json.dumps(attributes, indent=2)
print(json_output)
