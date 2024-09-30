# -*- coding: utf-8 -*-
import os
import sys
import json
import http.client
from urllib.parse import urlparse
import re 
from datetime import datetime

import logging
import sys
import mysql.connector

sys.path.insert(0, os.path.dirname(__file__))

def get_or_insert_item(cursor, item_name, description):
    # Step 1: Check for existing items
    check_query = '''
        SELECT item_id FROM Items 
        WHERE item_name LIKE %s OR description LIKE %s
    '''
    cursor.execute(check_query, (f'%{item_name}%', f'%{description}%'))
    result = cursor.fetchone()
    
    if result:
        # Item exists, return its id
        return result[0]  # item_id
    else:
        # Step 2: Insert new item since it doesn't exist
        insert_query = '''
            INSERT INTO Items (item_name, description) 
            VALUES (%s, %s)
        '''
        cursor.execute(insert_query, (item_name, description))
        
        # Step 3: Return the newly inserted item's id
        return cursor.lastrowid

def insert_receipt_to_db(parsed_receipt, fiscal_data, db_conn):
    cursor = db_conn.cursor()

    # Assume user_id and store_id are 1 for this case
    user_id = 1
    store_id = 1

    # Convert issue_date to correct datetime format
    try:
        issue_date_str = parsed_receipt['issue_date']  # e.g., '24.9.2024. 18:09:14'
        issue_date = datetime.strptime(issue_date_str, '%d.%m.%Y. %H:%M:%S')  # Convert to datetime object
        formatted_issue_date = issue_date.strftime('%Y-%m-%d %H:%M:%S')  # Format to 'YYYY-MM-DD HH:MM:SS'
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return None  # You can handle this more gracefully if needed

    # Insert the info about the store
    receipt_query = '''
    INSERT IGNORE INTO Stores (store_name, store_address)
    VALUES (%s, %s)
    '''
    cursor.execute(receipt_query, (
        parsed_receipt['store_name'],
        parsed_receipt['address']
    ))
    
    # Insert receipt info
    receipt_query = '''
    INSERT IGNORE INTO Receipts (issue_date, cashier_name, total_amount, user_id, store_name, store_address)
    VALUES (%s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(receipt_query, (
        formatted_issue_date,
        parsed_receipt['cashier_name'],
        parsed_receipt['total_amount'],
        1,
        parsed_receipt['store_name'],
        parsed_receipt['address']
    ))

    for item in parsed_receipt['items']:
        item_id = get_or_insert_item(cursor, item['name'], 'none')

    # Commit the transaction
    db_conn.commit()
    cursor.close()

def parse_receipt(receipt_string):
    # Split the receipt string into lines
    lines = receipt_string.strip().split('\n')
    
    # Initialize a dictionary to hold parsed data
    parsed_data = {
        'store_name': '',
        'address': '',
        'cashier_name': '',
        'items': [],
        'total_amount': 0.0,
        'issue_date': ''
    }
    
    # Regular expressions for extracting information
    store_name_pattern = re.compile(r'"(.*?)"\s*(.*?)\s*')
    cashier_pattern = re.compile(r'Касир:\s*(.*)')
    total_amount_pattern = re.compile(r'Укупан износ:\s*(\d+,\d+)')
    issue_date_pattern = re.compile(r'ПФР вријеме:\s*(.*)')  # Pattern for issue date
    
    # Parse the receipt line by line
    for i, line in enumerate(lines):
        # Extract store name and address
        if i == 1:  # Assuming store name is always on line 2
            # Remove &quot; from the line and sanitize the name
            store_name = line.replace("&quot;", "").strip()
            parsed_data['store_name'] = store_name
        
        if i == 3 or i == 4:  # Address is on line 4 and line 5
            parsed_data['address'] += line.strip() + " " # Add space between address parts

        # Extract cashier name
        cashier_match = cashier_pattern.search(line)
        if cashier_match:
            parsed_data['cashier_name'] = cashier_match.group(1).strip()

        # Extract total amount
        total_match = total_amount_pattern.search(line)
        if total_match:
            parsed_data['total_amount'] = float(total_match.group(1).replace(',', '.'))

        issue_date_match = issue_date_pattern.search(line)
        if issue_date_match:
            parsed_data['issue_date'] = issue_date_match.group(1).strip()  # Capture date and time

        # Read item lines: name and data
        if line.strip() == "Артикли":
            for j in range(i + 3, len(lines), 2):  # Start reading items after 'Артикли'
                if lines[j].strip() == "----------------------------------------":
                    break  # Stop if we reach the line separator
                
                if j + 1 < len(lines):  # Ensure there is a next line
                    item_name = lines[j].strip()  # First line: item name
                    item_data = lines[j + 1].strip()  # Second line: item data
                    
                    # Split item_data by whitespace
                    numbers = re.split(r'\s+', item_data)
                    
                    if len(numbers) >= 3:  # Ensure we have enough parts
                        item_price = float(numbers[0].replace(',', '.'))  # Price
                        item_quantity = int(numbers[1])  # Quantity
                        item_total = float(numbers[2].replace(',', '.'))  # Total
                        
                        # Add to items list
                        parsed_data['items'].append({
                            'name': item_name,
                            'price': item_price,
                            'quantity': item_quantity,
                            'total': item_total
                        })

    return parsed_data

def application(environ, start_response):
    path = environ.get('PATH_INFO')
    
    if path.startswith('/scrape'):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0

        request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')

        try:
            json_data = json.loads(request_body)
            url = json_data.get('url', 'No URL provided')
            if url == 'No URL provided':
                raise ValueError("No URL provided")
        except (json.JSONDecodeError, ValueError) as e:
            start_response('400 Bad Request', [('Content-Type', 'text/plain')])
            response = f"Invalid input: {str(e)}"
            return [response.encode()]

        # Parse the URL to get the host and path
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        request_path = parsed_url.path if parsed_url.path else '/'
        query = parsed_url.query

        # Create an HTTP connection
        conn = http.client.HTTPConnection(host) if parsed_url.scheme == 'http' else http.client.HTTPSConnection(host)

        # Set headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        try:
            full_path = f"{request_path}?{query}" if query else request_path
            
            conn.request("GET", full_path, headers=headers)
            response = conn.getresponse()

            if response.status == 200:
                data = response.read().decode()
                
                def extract_fiscal_info(text):
                    # Omit <img ... /> sections
                    start_img_index = text.find("<br/><img ")
                    while start_img_index != -1:
                        end_img_index = text.find("/>", start_img_index)
                        if end_img_index != -1:
                            # Remove the <img ... /> section
                            text = text[:start_img_index] + text[end_img_index + 2:]
                            start_img_index = text.find("<img ")
                        else:
                            break
                    
                    start_marker = "============ ФИСКАЛНИ РАЧУН ============"
                    end_marker = "======== КРАЈ ФИСКАЛНОГ РАЧУНА ========="
                    start_index = text.find(start_marker)
                    if start_index == -1:
                        return None
                    start_index += len(start_marker)
                    end_index = text.find(end_marker, start_index)
                    if end_index == -1:
                        return None
                    fiscal_info = text[start_index:end_index].strip()
                    return fiscal_info

                fiscal_data = extract_fiscal_info(data)
                
                if fiscal_data:
                    
                    parsed_receipt = parse_receipt(fiscal_data)
                    parsed_data = {
                        'store_name': parsed_receipt.get('store_name', ''),
                        'address': parsed_receipt.get('address', ''),
                        'cashier_name': parsed_receipt.get('cashier_name', ''),
                        'items': parsed_receipt.get('items', []),
                        'total_amount': parsed_receipt.get('total_amount', 0.0),
                        'issue_date': parsed_receipt.get('issue_date', '')
                    }
                    
                    db_conn = mysql.connector.connect(
                        host="neutron.global.ba",
                        user="indigoin_cijenolovac_admin",
                        password="Pijanista123!",
                        database="indigoin_cijenolovac",
                        charset='utf8mb4'
                    )

                    # Insert the parsed receipt into the database
                    try:
                        insert_receipt_to_db(parsed_data, fiscal_data, db_conn)
                    finally:
                        db_conn.close()
                    
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    response_body = json.dumps(parsed_data)
                    return [response_body.encode()]
                else:
                    start_response('404 Not Found', [('Content-Type', 'application/json')])
                    response_body = json.dumps({
                        "status": "error",
                        "message": "Fiscal information not found."
                    })
                    return [response_body.encode()]

            else:
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                response = f"Failed to retrieve data. Status code: {response.status}"
                return [response.encode()]

        except Exception as e:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            response = f"Error occurred: {str(e)}"
            return [response.encode()]
        finally:
            conn.close()

    # Default response for paths that are not handled
    start_response('200 OK', [('Content-Type', 'text/plain')])
    message = 'It works!\n'
    version = 'Python v' + sys.version.split()[0] + '\n'
    response = '\n'.join([message, version])
    return [response.encode()]
