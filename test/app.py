from flask import Flask, jsonify, request
from flask_cors import CORS 
import os
import ast
import requests
import subprocess
import tarfile
import logging
from flask import send_from_directory

app = Flask(__name__)
CORS(app)

def checkout_commit(commit_hash):
    subprocess.run(['git', 'checkout', commit_hash], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def extract_project_attributes(project_directory, repo_owner, repo_name):
    class_attributes = {
        "lines_of_code": 0,
        "num_classes": 0,
        "num_methods": 0,
        "num_variables": 0,
        "for_loops": 0,
        "classes": {}
    }

    # GitHub API base URL
    BASE_URL = 'https://api.github.com'

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

                                current_class = {"methods": [], "attributes": [], "loops": 0}  # Add loops attribute to current_class
                                parent_classes = []
                                for base_class in node.bases:
                                    if isinstance(base_class, ast.Name):
                                        parent_classes.append(base_class.id)

                                if parent_classes:
                                    class_attributes["classes"].setdefault(parent_classes[0], {}).setdefault(class_name, current_class)
                                else:
                                    class_attributes["classes"][class_name] = current_class

                                for item in node.body:
                                    if isinstance(item, ast.FunctionDef):
                                        method_name = item.name
                                        class_attributes["num_methods"] += 1
                                        current_class["methods"].append(method_name)
                                    elif isinstance(item, ast.Assign):
                                        for target in item.targets:
                                            if isinstance(target, ast.Name):
                                                variable_name = target.id
                                                class_attributes["num_variables"] += 1
                                                current_class["attributes"].append(variable_name)
                                    elif isinstance(item, ast.For): 
                                        class_attributes["for_loops"] += 1
                                        current_class["loops"] += 1
                    except SyntaxError:
                        print(f"Error parsing {file_path}. Skipping.")

    return class_attributes

def fetch_repository_files(owner, repo, commit_sha, target_dir):
    url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{commit_sha}"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with tarfile.open(fileobj=response.raw, mode="r|gz") as tar:
            tar.extractall(path=target_dir)
    else:
        print(f"Failed to fetch repository files. Status code: {response.status_code}")

def fetch_commit_hash(owner, repo, commit_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": 1, "page": commit_number}
    response = requests.get(url, params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["sha"]
        else:
            print("Commit not found.")
            return None
    else:
        print(f"Failed to fetch commit hash in hash method. Status code: {response.status_code}")
        return None

# Function to fetch commit information including commit message from GitHub API
def fetch_commit_info(owner, repo, commit_sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("commit").get("message")
    else:
        print(f"Failed to fetch commit information. Status code: {response.status_code}")
        return None

# def fetch_commit_info(owner, repo, commit_sha):
#     return None

def transform_to_d3_format(data):
    root = {
        "lines_of_code": data["lines_of_code"],
        "num_classes": data["num_classes"],
        "num_methods": data["num_methods"],
        "num_variables": data["num_variables"],
        "for_loops": data["for_loops"],
        "children": []
    }
    for class_name, class_info in data["classes"].items():
        class_node = {"name": class_name, "children": []}
        if "methods" in class_info:
            for method in class_info["methods"]:
                class_node["children"].append({"name": method, "type": "method"})
        if "attributes" in class_info:
            for attribute in class_info["attributes"]:
                class_node["children"].append({"name": attribute, "type": "attribute"})
        root["children"].append(class_node)
    return root

logging.basicConfig(level=logging.INFO)

from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/get_d3_data', methods=['POST'])
def get_d3_data():
    try:
        data = request.json
        owner = "psf"
        repo = "requests"
        commit_number = data['commit_number']

        commit_hash = fetch_commit_hash(owner, repo, commit_number)
        commit_hash = "86fb0cb23586b3bb326f5ba62abc4bf54447918f"
        if commit_hash:
            fetch_repository_files(owner, repo, commit_hash, "repo_files")

            project_directory = f"{owner}-{repo}-{commit_hash[:7]}"

            attributes = extract_project_attributes("repo_files/"+project_directory, owner, repo)

            commit_message = fetch_commit_info(owner, repo, commit_hash)

            d3_data = transform_to_d3_format(attributes)

            d3_data["commit_message"] = commit_message
            
            title = repo + " by " + owner
            
            d3_data["title"] = title
            
            d3_data["commit_number"] = commit_number
            
            response = jsonify(d3_data)
            response.headers.add('Access-Control-Allow-Origin', '*') 
            return response
        else:
            print(commit_hash)
            error_msg = 'Failed to fetch commit hash from GitHub API'
            logging.error(error_msg)
            return jsonify({'error': 'Failed to fetch commit hash in api'})
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        logging.exception(error_msg)
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)