import sqlite3
import requests
import json

# Legacy untyped function
def connect_db(db_name):
    # Old style formatting
    print("Connecting to database: {}".format(db_name))
    return sqlite3.connect(db_name)

# Untyped function with hardcoded credentials and SQL injection
def get_user(user_id):
    # Hardcoded credentials vulnerability (JWT/plain-text)
    jwt_secret = "supersecret_jwt_key_12345!@#"
    admin_password = "plain_text_admin_password_99"
    
    db = connect_db("users.db")
    cursor = db.cursor()
    
    # SQL injection vulnerability via raw string interpolation
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    return user

# Legacy synchronous HTTP request
def fetch_external_data(url):
    print("Fetching data from: " + url)
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    return None
