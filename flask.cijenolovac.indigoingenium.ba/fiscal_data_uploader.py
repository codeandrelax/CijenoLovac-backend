import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json

def upload_fiscal_data(fiscal_data, user_id):
    DB_HOST = 'neutron.global.ba'
    DB_USER = 'indigoin_cijenolovac_admin'
    DB_PASS = 'Pijanista123!'
    DB_NAME = 'indigoin_cijenolovac'

    connection = None
    
    data_save = fiscal_data
    
    try:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: Fiscal Data: {fiscal_data}\n")

        if isinstance(fiscal_data, str):
            fiscal_data = json.loads(fiscal_data)  # Use json.loads instead of eval

        if not isinstance(fiscal_data, dict):
            raise ValueError("fiscal_data is not a valid dictionary.")

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            charset='utf8mb4'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Check if user exists
            cursor.execute("SELECT COUNT(*) FROM Users WHERE user_id = %s", (user_id,))
            user_exists = cursor.fetchone()[0] > 0

            if not user_exists:
                return json.dumps({"error": f"User with user_id {user_id} not found"})
            
            # Check if a receipt with the same real_receipt_id already exists
            real_receipt_id = fiscal_data["real_receipt_id"]
            cursor.execute(
                "SELECT COUNT(*) FROM Receipts WHERE real_receipt_id = %s AND user_id = %s", 
                (real_receipt_id, user_id)
            )
            receipt_exists = cursor.fetchone()[0] > 0

            if receipt_exists:
                return json.dumps({"error": f"Receipt with real_receipt_id {real_receipt_id} already exists"})
            
            required_keys = ["receipt_issue_date", "cashier_name", "receipt_total", "full_receipt"]
            for key in required_keys:
                if key not in fiscal_data:
                    raise KeyError(f"Missing key in fiscal_data: {key}")

            # Encode strings to ensure proper formatting
            receipt_issue_date_str = fiscal_data["receipt_issue_date"]
            receipt_issue_date = datetime.strptime(receipt_issue_date_str, "%d.%m.%Y. %H:%M:%S")

            receipt_total = float(fiscal_data["receipt_total"].replace(',', '.'))

            values = (
                fiscal_data["real_receipt_id"],
                receipt_issue_date,
                fiscal_data["cashier_name"],
                receipt_total,
                user_id,
                fiscal_data["full_receipt"]
            )

            sql_query = """
            INSERT INTO Receipts (real_receipt_id, issue_date, cashier_name, total_amount, user_id, receipt_text)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # Log the values before inserting
            with open("upload_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()}: Values to insert: {values}\n")

            cursor.execute(sql_query, values)

            connection.commit()
            with open("upload_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()}: Record inserted successfully: {cursor.rowcount} row(s) affected.\n")
            
            return data_save
            
    except Error as e:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: Error while connecting to MySQL: {e}\n")
    except KeyError as e:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: Missing key: {e}\n")
    except ValueError as e:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: Value error: {e}\n")
    except Exception as e:
        with open("upload_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: An unexpected error occurred: {e}\n")

    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            with open("upload_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now()}: MySQL connection is closed.\n")

