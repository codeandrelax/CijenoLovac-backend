# -*- coding: utf-8 -*-
import os
import sys
import json
import http.client
from urllib.parse import urlparse
import re 
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

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
