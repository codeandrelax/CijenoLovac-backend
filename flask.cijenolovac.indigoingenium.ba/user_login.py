import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def user_login(body):
    DB_HOST = 'neutron.global.ba'
    DB_USER = 'indigoin_cijenolovac_admin'
    DB_PASS = 'Pijanista123!'
    DB_NAME = 'indigoin_cijenolovac'

    connection = None

    try:
        # Parse the JSON string
        data = json.loads(body)

        username = data.get("user")
        email = data.get("email")
        password = data.get("password")

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            charset='utf8mb4'
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Prepare the SQL query to check for user existence
            sql_query = """
            SELECT user_id, password_hash FROM Users WHERE name = %s OR email = %s
            """
            cursor.execute(sql_query, (username, email))

            result = cursor.fetchone()

            if result:
                stored_password = result[1]
                user_id = result[0]
                # Check if the provided password matches the stored plain-text password
                if password == stored_password:
                    return json.dumps({"message": "Login successful", "user": username, "user_id": user_id}), 200
                else:
                    return json.dumps({"error": "Invalid username or password"}), 401
            else:
                return json.dumps({"error": "Invalid username or password"}), 401

    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON format"}), 400
    except Error as e:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: Database error: {e}\n")
        return json.dumps({"error": "Database error"}), 500
    except Exception as e:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: An unexpected error occurred: {e}\n")
        return json.dumps({"error": str(e)}), 500
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            with open("upload_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()}: MySQL connection is closed.\n")
