-- Users Table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    surname VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL  -- Store the hashed password
);

-- Items Table
CREATE TABLE Items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);

-- Store_Items Table (without store_name and store_address)
CREATE TABLE Store_Items (
    store_item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT,
    store_item_name VARCHAR(255) NOT NULL,  -- Store-specific name
    current_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE,
    UNIQUE(store_item_name)  -- Ensure each store item name is unique
);

-- Receipts Table (without store_name and store_address)
CREATE TABLE Receipts (
    receipt_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_date DATETIME NOT NULL,
    cashier_name VARCHAR(100) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    user_id INT,  -- Reference to the user who created the receipt
    receipt_text TEXT,  -- New column to hold non-parsed data
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL  -- Optional: set to NULL if user is deleted
);

-- Receipt_Items Table
CREATE TABLE Receipt_Items (
    receipt_id INT,
    item_id INT,  -- Adding item_id to link to Items table
    quantity INT NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (receipt_id) REFERENCES Receipts(receipt_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE,
    PRIMARY KEY (receipt_id, item_id)  -- Composite primary key
);

-- Insert an admin user
INSERT INTO Users (name, surname, email, password_hash)
VALUES ('admin', 'admin', 'admin@admin', 'hashed_password_here');
