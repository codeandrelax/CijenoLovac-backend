# parser.py

def extract_fiscal_receipt(scraped_data):
    """
    Extracts the fiscal receipt from the scraped data and removes <img> tags.
    
    Parameters:
    scraped_data (str): The HTML/text content scraped from the URL.

    Returns:
    dict: A dictionary containing the status and extracted receipt or error message.
    """
    # Remove <img> tags from the scraped data
    cleaned_data = remove_img_tags(scraped_data)

    start_marker = "=========== ФИСКАЛНИ РАЧУН ==========="
    end_marker = "======== КРАЈ ФИСКАЛНОГ РАЧУНА ========="

    # Initialize the response
    response = {
        "status": "error",
        "message": "Fiscal receipt not found."
    }

    try:
        start_index = cleaned_data.find(start_marker)
        end_index = cleaned_data.find(end_marker)

        if start_index != -1 and end_index != -1 and start_index < end_index:
            # Extracting the fiscal receipt
            receipt = cleaned_data[start_index + len(start_marker):end_index].strip()
            response = {
                "status": "success",
                "receipt": receipt
            }
    except Exception as e:
        response["message"] = str(e)

    return response

def remove_img_tags(data):
    """
    Removes all <img> tags from the data.

    Parameters:
    data (str): The input string potentially containing <img> tags.

    Returns:
    str: The cleaned string with <img> tags removed.
    """
    # Replace <img tags and everything after it until the end of the line
    cleaned_data = []
    for line in data.splitlines():
        if '<img' in line:
            line = line.split('<img')[0]  # Remove <img> and everything after it
        cleaned_data.append(line)

    return '\n'.join(cleaned_data)
