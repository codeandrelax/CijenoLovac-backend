import os
import sys
import json
import logging
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    filename='app.log',        # Log file name
    level=logging.DEBUG,       # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

sys.path.insert(0, os.path.dirname(__file__))


def scrape_link(url):
    """Scrape the provided URL and return the scraped data."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Customize how you want to scrape the data
        scraped_data = {
            "title": soup.title.string if soup.title else "No Title",
            "content": soup.get_text()[:200]  # Get the first 200 characters of text
        }
        return scraped_data
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None


def application(environ, start_response):
    path = environ['PATH_INFO']
    
    if path == '/scrape' and environ['REQUEST_METHOD'] == 'POST':
        try:
            content_length = int(environ['CONTENT_LENGTH'])
            body = environ['wsgi.input'].read(content_length)
            data = json.loads(body)

            url = data.get('url')
            if url:
                scraped_data = scrape_link(url)
                if scraped_data:
                    response = json.dumps({"status": "ok", "data": scraped_data})
                else:
                    response = json.dumps({"status": "failure", "message": "failure to scrape"})
            else:
                response = json.dumps({"status": "failure", "message": "No URL provided"})
            
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [response.encode()]
        except (ValueError, KeyError) as e:
            logging.error(f"Invalid request data: {e}")
            response = json.dumps({"status": "failure", "message": str(e)})
            start_response('400 Bad Request', [('Content-Type', 'application/json')])
            return [response.encode()]
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            response = json.dumps({"status": "failure", "message": "An unexpected error occurred"})
            start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
            return [response.encode()]
    
    elif path == '/' and environ['REQUEST_METHOD'] == 'GET':
        # Respond with a success message and Python version
        start_response('200 OK', [('Content-Type', 'text/plain')])
        message = 'It works!\n'
        version = 'Python v' + sys.version.split()[0] + '\n'
        response = '\n'.join([message, version])
        return [response.encode()]

    else:
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'Not Found']


if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    httpd = make_server('', 8000, application)
    logging.info("Serving on port 8000...")
    httpd.serve_forever()
