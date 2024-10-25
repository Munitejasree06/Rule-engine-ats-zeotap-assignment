import mysql.connector

# Connect to the MySQL database
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='rule_engine_database'  
)

cursor = connection.cursor()

# Query to retrieve all rules
query = "SELECT * FROM rules;"  # Replace with your table name
cursor.execute(query)

# Fetch all the results
rules = cursor.fetchall()

# Optionally, you can get column names
columns = [column[0] for column in cursor.description]

# Define the filename
filename = 'rules.txt'

# Write rules to a file
with open(filename, 'w') as file:
    # Write column names as the first line
    file.write('\t'.join(columns) + '\n')
    
    # Write each rule
    for rule in rules:
        file.write('\t'.join(map(str, rule)) + '\n')

# Clean up
cursor.close()
connection.close()

print(f"All rules have been written to {filename}.")
