import os
import sys
import json

from scraper import perform_scrape
from parser import extract_fiscal_receipt
from data_extractor import extract_fiscal_data
from fiscal_data_uploader import upload_fiscal_data
from user_login import user_login
from user_signup import user_signup

sys.path.insert(0, os.path.dirname(__file__))

# WSGI-compliant application function
def application(environ, start_response):
    """
    WSGI-compliant callable that handles incoming requests.
    """
    # Get the path from the environment
    path = environ.get('PATH_INFO', '')

    # Set the response headers
    headers = [('Content-Type', 'application/json')]

    # Check the path and return appropriate JSON responses
    if path == '/scrape':
        try:
            # Read the request body
            content_length = environ.get('CONTENT_LENGTH', '0')
            if not content_length.isdigit() or int(content_length) <= 0:
                response_body = json.dumps({"status": "error", "message": "Empty body"})
                start_response('400 Bad Request', headers)
                return [response_body.encode('utf-8')]

            body = environ['wsgi.input'].read(int(content_length))
            # Parse the JSON body
            json_data = json.loads(body)

            # Extract the URL from the JSON data
            url = json_data.get('url')
            user_id = json_data.get('user_id')
            
            if url:
                # Call the scrape function with the URL
                scraped_data = perform_scrape(url)

                # Call the extract_fiscal_receipt function on the scraped data
                parsing_result = extract_fiscal_receipt(scraped_data['data'])
                
                # Further extract fiscal data and return it as a dictionary (not JSON string)
                fiscal_data = extract_fiscal_data(parsing_result.get("receipt", ""))
                
                upload_result = upload_fiscal_data(fiscal_data, user_id)
                
                # Convert the fiscal data to JSON only when sending the response
                response_body = upload_result#json.dumps(fiscal_data)  # Ensure this is a dictionary, not a string
                start_response('200 OK', headers)
            else:
                response_body = json.dumps({"status": "error", "message": "Missing URL"})
                start_response('400 Bad Request', headers)

        except json.JSONDecodeError:
            response_body = json.dumps({"status": "error", "message": "Invalid JSON"})
            start_response('400 Bad Request', headers)
        except Exception as e:
            response_body = json.dumps({"status": "error", "message": str(e)})
            start_response('500 Internal Server Error', headers)
    elif path == '/login':
        try:
            # Read the request body
            content_length = environ.get('CONTENT_LENGTH', '0')
            if not content_length.isdigit() or int(content_length) <= 0:
                response_body = json.dumps({"status": "error", "message": "Empty body"})
                start_response('400 Bad Request', headers)
                return [response_body.encode('utf-8')]
    
            body = environ['wsgi.input'].read(int(content_length))
            # Call the user_login function to handle the login logic
            response_body, status_code = user_login(body)  # Get both the body and status code
            start_response(str(status_code), headers)  # Set the status code
    
        except Exception as e:
            # Log the error to a file
            with open(ERROR_LOG_FILE, 'a') as log_file:
                log_file.write(f"Error: {str(e)}\n")
    
            response_body = json.dumps({"status": "error", "message": "An internal error occurred."})
            start_response('500 Internal Server Error', headers)
    elif path == "/signup":
        try:
            # Read the request body
            content_length = environ.get('CONTENT_LENGTH', '0')
            if not content_length.isdigit() or int(content_length) <= 0:
                response_body = json.dumps({"status": "error", "message": "Empty body"})
                start_response('400 Bad Request', headers)
                return [response_body.encode('utf-8')]
    
            body = environ['wsgi.input'].read(int(content_length))
            # Call the signUp function to handle the signup logic
            response_body, status_code = user_signup(body)  # Pass the body directly to the function
            start_response(f'{status_code} OK', headers)
    
        except Exception as e:
            response_body = json.dumps({"status": "error", "message": str(e)})
            start_response('500 Internal Server Error', headers)

    else:
        response_body = json.dumps({"message": "CjenoLovac"})
        start_response('200 OK', headers)

    # Return the response as bytes (since WSGI requires bytes output)
    return [response_body.encode('utf-8')]

