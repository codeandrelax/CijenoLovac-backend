import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def user_signup(body):
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

            # Check if the username or email already exists
            check_query = """
            SELECT user_id FROM Users WHERE name = %s OR email = %s
            """
            cursor.execute(check_query, (username, email))

            result = cursor.fetchone()

            if result:
                return json.dumps({"error": "User with such email or username already exists"}), 409  # Conflict

            # Insert the new user
            insert_query = """
            INSERT INTO Users (name, surname, email, password_hash)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (username, "-", email, password))

            connection.commit()

            # Get the user_id of the newly inserted user
            new_user_id = cursor.lastrowid

            return json.dumps({
                "message": "User created successfully",
                "user_id": new_user_id,
                "user": username,
                "email": email
            }), 201  # Created

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
