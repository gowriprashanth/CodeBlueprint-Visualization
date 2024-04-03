import json

# Load the JSON data from CA.json
with open("output.json", "r") as json_file:
    class_hierarchy_data = json.load(json_file)

# Transform the data into a nested format suitable for D3
def transform_to_d3_format(data):
    root = {
        "lines_of_code": data["lines_of_code"],
        "num_classes": data["num_classes"],
        "num_methods": data["num_methods"],
        "num_variables": data["num_variables"],
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

d3_data = transform_to_d3_format(class_hierarchy_data)

# Save the transformed data to a new JSON file
with open("transform.json", "w") as output_file:
    json.dump(d3_data, output_file, indent=2)

print("Transformed data saved to output.json")