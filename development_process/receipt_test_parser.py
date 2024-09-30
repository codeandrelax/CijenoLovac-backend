# -*- coding: utf-8 -*-
import re

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

# Sample receipt string
receipt_string = """
4512149430003
&quot;Atipico&quot; Nemanja Đurić s.p. Banja Luka
10024512149430001-&quot;Atipico&quot; Nemanja Đurić s.p. Banja Luka
Bulevar vojvode Živojina Mišića 10B
Banja Luka
Касир:                 Bojana Kolundžija
ЕСИР број:                        13/2.0
-------------ПРОМЕТ ПРОДАЈА-------------
Артикли
========================================
Назив   Цијена       Кол.         Укупно
Cappuccino (Е)                          
         2,50          1            2,50
----------------------------------------
Укупан износ:                       2,50
Готовина:                           2,50
========================================
Ознака       Име      Стопа        Порез
Е             ПДВ   17,00%          0,36
----------------------------------------
Укупан износ пореза:                0,36
========================================
ПФР вријеме:         24.9.2024. 18:09:14
ПФР број рачуна:  5QJYK88S-5QJYK88S-1034
Бројач рачуна:               1032/1034ПП
========================================
"""

# Parse the receipt
parsed_receipt = parse_receipt(receipt_string)

# Print the parsed data
for key, value in parsed_receipt.items():
    print("{}: {}".format(key, value))
