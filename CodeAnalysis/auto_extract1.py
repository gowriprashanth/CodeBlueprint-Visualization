import ast
import json
import requests

def extract_project_attributes_from_commit(commit_sha, repo_owner, repo_name):
    class_attributes = {
        "lines_of_code": 0,
        "num_classes": 0,
        "num_methods": 0,
        "num_variables": 0,
        "classes": {}  
    }
    
    # GitHub API base URL
    BASE_URL = 'https://api.github.com'
    
    # Fetch file tree for the commit
    commit_files_url = f'{BASE_URL}/repos/{repo_owner}/{repo_name}/commits/{commit_sha}'
    commit_files_response = requests.get(commit_files_url)
    commit_files = commit_files_response.json()['files']
    
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

def get_main_branch_commits(repo_owner, repo_name):
    # GitHub API base URL
    BASE_URL = 'https://api.github.com'
    
    # Fetch list of commits for the main branch
    main_branch_url = f'{BASE_URL}/repos/{repo_owner}/{repo_name}/branches/main'
    main_branch_response = requests.get(main_branch_url)
    main_branch_data = main_branch_response.json()
    main_branch_sha = main_branch_data['commit']['sha']
    
    # Fetch commit history for the main branch
    commits_url = f'{BASE_URL}/repos/{repo_owner}/{repo_name}/commits'
    commits_response = requests.get(commits_url, params={'sha': main_branch_sha})
    commits_data = commits_response.json()
    
    # Extract commit SHAs
    commit_shas = [commit['sha'] for commit in commits_data]
    
    return commit_shas

# Repository details
repo_owner = 'psf'
repo_name = 'requests'

# Get commit SHAs for the main branch
main_branch_commits = get_main_branch_commits(repo_owner, repo_name)

# Initialize previous project attributes
prev_attributes = None

# Iterate through commits
for index, commit_sha in enumerate(main_branch_commits, start=1):
    # Extract project attributes for the commit
    attributes = extract_project_attributes_from_commit(commit_sha, repo_owner, repo_name)
    
    # Compare with previous attributes
    if prev_attributes:
        progress = {
            "lines_of_code_change": attributes["lines_of_code"] - prev_attributes["lines_of_code"],
            "num_classes_change": attributes["num_classes"] - prev_attributes["num_classes"],
            "num_methods_change": attributes["num_methods"] - prev_attributes["num_methods"],
            "num_variables_change": attributes["num_variables"] - prev_attributes["num_variables"]
        }
        print(f"Commit {index}/{len(main_branch_commits)}:")
        print(json.dumps(progress, indent=2))
        print()
    
    # Update previous attributes
    prev_attributes = attributes

# Prompt user to input a commit number and show growth
while True:
    try:
        commit_number = int(input(f"Enter a commit number (1 to {len(main_branch_commits)}): "))
        if 1 <= commit_number <= len(main_branch_commits):
            selected_commit_sha = main_branch_commits[commit_number - 1]
            attributes = extract_project_attributes_from_commit(selected_commit_sha, repo_owner, repo_name)
            if prev_attributes:
                progress = {
                    "lines_of_code_change": attributes["lines_of_code"] + prev_attributes["lines_of_code"],
                    "num_classes_change": attributes["num_classes"] + prev_attributes["num_classes"],
                    "num_methods_change": attributes["num_methods"] + prev_attributes["num_methods"],
                    "num_variables_change": attributes["num_variables"] + prev_attributes["num_variables"]
                }
                print(f"Commit {commit_number}/{len(main_branch_commits)}:")
                print(json.dumps(progress, indent=2))
                print()
            break
        else:
            print(f"Invalid commit number. Please enter a number between 1 and {len(main_branch_commits)}.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")
