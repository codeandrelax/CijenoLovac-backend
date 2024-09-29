# data_extractor.py
import json

def extract_fiscal_data(receipt_data):
    """
    Extracts fiscal data from the receipt data string and returns it as a JSON object.

    Parameters:
    receipt_data (str): The string content of the fiscal receipt.

    Returns:
    str: A JSON string containing the extracted fiscal data.
    """
    lines = receipt_data.splitlines()

    # Extracting store name, address, cashier name, and issue date
    real_receipt_id = lines[1].strip() # First line
    store_name = lines[2].replace('&quot;', '').strip()  # Second line
    store_address = f"{lines[4].strip()} {lines[5].strip()}"  # Fourth and fifth lines
    cashier_name = lines[6].replace('Касир:', '').strip()  # Sixth line
    issue_date = extract_issue_date(lines)
    total_amount = extract_total_amount(lines)

    # Extracting item list
    item_list = extract_items(lines)

    # Creating the final data dictionary
    data = {
        "real_receipt_id": real_receipt_id,
        "store_name": store_name,
        "cashier_name": cashier_name,
        "store_address": store_address,
        "receipt_total": total_amount,
        "receipt_issue_date": issue_date,
        "item_list": item_list,
        "full_receipt": receipt_data
    }

    # Returning JSON formatted string
    return json.dumps(data, ensure_ascii=False)

def extract_issue_date(lines):
    """
    Extracts the issue date from the receipt lines.

    Parameters:
    lines (list): The list of lines from the receipt.

    Returns:
    str: The extracted issue date.
    """
    for line in lines:
        if "ПФР вријеме:" in line:
            return line.split("ПФР вријеме:")[1].strip()
    return ""

def extract_total_amount(lines):
    """
    Extracts the total amount from the receipt lines.

    Parameters:
    lines (list): The list of lines from the receipt.

    Returns:
    str: The extracted total amount.
    """
    for line in lines:
        if "Укупан износ:" in line:
            return line.split("Укупан износ:")[1].strip()
    return ""

def extract_items(lines):
    """
    Extracts the list of items from the receipt lines.

    Parameters:
    lines (list): The list of lines from the receipt.

    Returns:
    list: A list of items with their store names, prices, and quantities.
    """
    item_list = []
    item_section_started = False

    for i in range(len(lines)):
        if "Назив   Цијена       Кол.         Укупно" in lines[i]:
            item_section_started = True
            continue  # Skip the header line

        if item_section_started:
            # Read two lines at a time
            if i + 1 < len(lines):
                item_name = lines[i].strip()
                prices = lines[i + 1].strip().split()
                if len(prices) == 3:  # Ensure we have price, quantity, and total
                    price, quantity, _ = prices
                    item_list.append({
                        "item_store_name": item_name,
                        "price": price.strip(),
                        "quantity": quantity.strip()
                    })
            # Stop processing if we reach the line of dashes
            if "----------------------------------------" in lines[i + 1]:
                break

    return item_list
