from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
import json
import re
from flask_migrate import Migrate
import sys
import logging

sys.setrecursionlimit(10000)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/rule_engine_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.DEBUG)

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.Integer, primary_key=True)
    rule_string = db.Column(db.String(255), nullable=False)
    ast = db.Column(db.JSON, nullable=False)  # Store AST as JSON
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

def parse_rule(rule_string):
    print(f"Parsing rule string: {rule_string}")

    operator_pattern = r"\s*(AND|OR)\s*"
    operand_pattern = r"([a-zA-Z_][a-zA-Z0-9_.]*\s*(>=|<=|>|<|=|!=)\s*'?[a-zA-Z0-9_.]+'?)"
    paren_pattern = r"\s*\(\s*(.*?)\s*\)\s*"

    token_string = rule_string.strip()
    while True:
        match = re.search(paren_pattern, token_string)
        if match:
            inner = match.group(1)
            inner_ast = parse_rule(inner)  # Recursively parse inner expressions
            token_string = token_string[:match.start()] + json.dumps(inner_ast.to_dict()) + token_string[match.end():]
        else:
            break

    tokens = [token.strip() for token in re.split(operator_pattern, token_string) if token.strip()]
    current_node = None
    operator_stack = []

    for token in tokens:
        if re.match(operand_pattern, token):
            node = ASTNode('operand', value=token)

            if current_node is None:
                current_node = node
            else:
                if operator_stack:
                    last_operator = operator_stack.pop()
                    new_operator_node = ASTNode('operator', left=current_node, right=node, value=last_operator)
                    current_node = new_operator_node
                else:
                    raise ValueError("Missing operator before operand.")

        elif token in ["AND", "OR"]:
            operator_stack.append(token)

    while operator_stack:
        if current_node is None:
            raise ValueError("Unexpected end of expression.")
        
        right_node = current_node
        if not operator_stack:
            raise ValueError("Not enough operands for the operator.")
        
        last_operator = operator_stack.pop()
        left_node = ASTNode('operand', value='')  # Create a placeholder for the left node if it's not there
        current_node = ASTNode('operator', left=left_node, right=right_node, value=last_operator)

    return current_node if current_node else None


def create_rule(rule_string):
    try:
        return parse_rule(rule_string)
    except Exception as e:
        logging.error(f"Error in create_rule: {str(e)}")
        return None

def combine_rules(rules):
    if not rules:
        return None

    combined_ast = create_rule(rules[0])
    if combined_ast is None:
        raise ValueError("Failed to create AST from the first rule.")

    for rule in rules[1:]:
        new_ast = create_rule(rule)
        if new_ast is None:
            raise ValueError(f"Failed to create AST from the rule: {rule}")

        combined_ast = ASTNode('operator', left=combined_ast, right=new_ast, value='AND')

    return combined_ast

def evaluate_rule(rule_node, data):
    if rule_node is None:
        return False
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
    try:
        attribute, comparison, value = re.split(r'\s*(>=|<=|>|<|=|!=)\s*', node.value.strip())
    except ValueError:
        raise ValueError(f"Unexpected operand format: {node.value}")

    attribute_value = data.get(attribute)

    if attribute_value is None:
        return False

    if value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).isdigit():
        value = float(value)
    elif value.startswith("'") and value.endswith("'"):
        value = value.strip("'")

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_rule', methods=['POST'])
def create_rule_endpoint():
    rule_string = request.json.get('rule')
    try:
        node = create_rule(rule_string)
        if node is None:
            raise ValueError("Failed to create an AST from the rule string.")

        ast_dict = node.to_dict()  # Convert to dict for JSON storage
        new_rule = Rule(rule_string=rule_string, ast=json.dumps(ast_dict))
        db.session.add(new_rule)
        db.session.commit()

        return jsonify({"ast": ast_dict})
    except Exception as e:
        db.session.rollback()  # Rollback the session on error
        logging.error(f"Error creating rule: {str(e)}")
        return jsonify({"error": str(e)}), 400
@app.route('/combine_rules', methods=['POST'])
def combine_rules_endpoint():
    rules = request.json.get('rules')
    if not rules:
        return jsonify({"error": "No rules provided."}), 400
        
    combined_node = combine_rules(rules)
    if combined_node is None:
        return jsonify({"error": "Failed to combine rules."}), 400
    return jsonify({"ast": combined_node.to_dict()})

# Endpoint to evaluate a rule based on data
@app.route('/evaluate_rule', methods=['POST'])
def evaluate_rule_endpoint():
    rule_json = request.json.get('ast')
    data = request.json.get('data')
    if not rule_json or not data:
        return jsonify({"error": "No AST or data provided."}), 400

    try:
        result = evaluate_rule(ASTNode(**rule_json), data)
    except Exception as e:
        logging.error(f"Error evaluating rule: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
    return jsonify({"result": result})

# Endpoint to modify an existing rule
@app.route('/modify_rule/<int:rule_id>', methods=['PUT'])
def modify_rule(rule_id):
    rule_string = request.json.get('rule')
    if not rule_string:
        return jsonify({"error": "No rule string provided."}), 400

    rule = Rule.query.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    
    try:
        node = create_rule(rule_string)
        if node is None:
            raise ValueError("Failed to create an AST from the rule string.")
        
        ast_dict = node.to_dict()
        rule.rule_string = rule_string
        rule.ast = json.dumps(ast_dict)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error modifying rule: {str(e)}")
        return jsonify({"error": str(e)}), 400

    return jsonify({"ast": ast_dict})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)