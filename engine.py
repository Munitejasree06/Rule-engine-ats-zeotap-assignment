class ASTNode:
    def __init__(self, type, left=None, right=None, value=None):
        self.type = type
        self.left = left
        self.right = right
        self.value = value

    def to_dict(self):
        return {
            'type': self.type,
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None,
            'value': self.value
        }

def create_rule(rule_string):
    # Simplified AST creation from a rule string for demonstration purposes
    return ASTNode('operator',
        ASTNode('operator',
            ASTNode('operand', value='age > 30'),
            ASTNode('operand', value="department = 'Sales'"),
            value='AND'
        ),
        ASTNode('operator',
            ASTNode('operand', value='salary > 50000'),
            ASTNode('operand', value='experience > 5'),
            value='OR'
        ),
        value='AND'
    )

def combine_rules(rules):
    # Combine multiple rules into one AST
    rule1 = create_rule(rules[0])
    rule2 = create_rule(rules[1])
    
    combined_ast = ASTNode('operator',
        rule1,
        rule2,
        value='AND'
    )
    return combined_ast

def evaluate_rule(rule_node, data):
    # Evaluates the rule AST against the provided data
    return eval_node(rule_node, data)

def eval_node(node, data):
    if node.type == 'operand':
        return evaluate_operand(node, data)
    
    left_value = eval_node(node.left, data)
    right_value = eval_node(node.right, data)
    
    if node.value == 'AND':
        return left_value and right_value
    elif node.value == 'OR':
        return left_value or right_value
    else:
        raise ValueError(f"Unknown operator: {node.value}")

def evaluate_operand(node, data):
    # Handle operand evaluation, such as 'age > 30' or "department = 'Sales'"
    try:
        attribute, comparison, value = node.value.split(' ', 2)
    except ValueError:
        raise ValueError(f"Unexpected operand format: {node.value}")

    attribute_value = data.get(attribute)

    # Handle if attribute is missing from the data
    if attribute_value is None:
        return False

    # Perform the comparison, handling different data types
    if value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).isdigit():
        value = float(value)
    elif value.startswith("'") and value.endswith("'"):
        value = value.strip("'")

    # Perform comparison based on the operator
    if comparison == '>':
        return attribute_value > value
    elif comparison == '<':
        return attribute_value < value
    elif comparison == '=':
        return attribute_value == value
    elif comparison == '!=':
        return attribute_value != value
    else:
        raise ValueError(f"Unknown comparison operator: {comparison}")

# Sample Test Data
data = {
    "age": 35,
    "department": "Sales",
    "salary": 60000,
    "experience": 6
}

# Running a test case
rule_string = "age > 30 AND department = 'Sales' AND (salary > 50000 OR experience > 5)"
rule_ast = create_rule(rule_string)
result = evaluate_rule(rule_ast, data)
print("Rule Evaluation Result:", result)
