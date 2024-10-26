# Rule-engine-ast-zeotap-assignment

## Objective
This application is a simple 3-tier rule engine that determines user eligibility based on various attributes like age, department, income, spend, etc. It utilizes an Abstract Syntax Tree (AST) to represent conditional rules, allowing for dynamic creation, combination, and modification of these rules.

## Data Structure
The AST is represented using a Node data structure with the following fields:

type: String indicating the node type ("operator" for AND/OR, "operand" for conditions).
left: Reference to another Node (left child).
right: Reference to another Node (right child for operators).
value: Optional value for operand nodes (e.g., number for comparisons).

## Sample Node Structure
python
class Node:
    def __init__(self, type, left=None, right=None, value=None):
        self.type = type  # "operator" or "operand"
        self.left = left  # Reference to the left child Node
        self.right = right  # Reference to the right child Node
        self.value = value  # Value for operand Nodes

## Data Storage
Database Choice: MySQL is chosen for storing the rules and application metadata.
**Schema**:
rules_table:
id: INT, Primary Key, Auto Increment
rule_string: VARCHAR, the string representation of the rule
created_at: TIMESTAMP, the time the rule was created

## Test Cases
**Create Individual Rules**:
Use create_rule with the sample rules to verify their AST representation.
**Combine Rules**:
Use combine_rules to combine the example rules and ensure the resulting AST reflects the combined logic.
**Evaluate Rules**:
Implement sample JSON data and test evaluate_rule for various scenarios.
**Additional Rules**:
Explore combining additional rules and test the functionality.

## Setup
Clone the repository:
git clone https://github.com/Munitejasree06/Rule-engine-ats-zeotap-assignment.git
cd Rule-engine-ats-zeotap-assignment

## Run the Application:

*Start the server*:
python app.py
Access the API through the designated endpoints.

## output
![image](https://github.com/user-attachments/assets/e7a5a856-2391-4976-9917-bea54f6ba7f4)

