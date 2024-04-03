import os
import ast
import json
import requests

def extract_project_attributes(project_directory):
    
    class_attributes = {
        "commit_message": "",
        "lines_of_code": 0,
        "num_classes": 0,
        "num_methods": 0,
        "num_variables": 0,
        "classes": {}  
    }

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

# Input the commit number from the user
commit_number = int(input("Enter the commit number (1 to 2270): "))

# Fetch the commit details from GitHub
commit_url = f"https://api.github.com/repos/request/request/commits/{commit_number}"
response = requests.get(commit_url, auth=("gowriprashanth", "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"))
if response.status_code == 200:
    commit_data = response.json()
    commit_sha = commit_data["sha"]
    commit_message = commit_data["commit"]["message"]
    print(f"Commit message: {commit_message}")

    # Download and extract the project repository at the given commit
    os.system(f"git clone --depth 1 --branch {commit_sha} https://github.com/request/request.git temp_repo")
    
    # Extract project attributes
    attributes = extract_project_attributes("temp_repo")
    
    # Remove temporary directory
    #os.system("rm -rf temp_repo")

    # Output the result in JSON format
    json_output = json.dumps(attributes, indent=2)
    print(json_output)
else:
    print("Error fetching commit details from GitHub.")
