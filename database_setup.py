import sqlite3

print("Connecting to database...")
# This will create the 'bot_database.db' file in your folder
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
print("Database connected.")

# --- 1. Create/Update Tables ---
print("Creating 'sessions' and 'history' tables...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    current_state TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    sender TEXT,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
)
''')

print("Creating 'ifsc_codes' and 'interest_rates' tables...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS ifsc_codes (
    branch_name TEXT PRIMARY KEY,
    ifsc_code TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS interest_rates (
    product_name TEXT PRIMARY KEY,
    rate TEXT
)
''')

# --- 2. NEW: Create Main Knowledge Base Table ---
print("Creating 'kb_local_intents' table...")
cursor.execute("DROP TABLE IF EXISTS kb_local_intents") # Drop old one if it exists
cursor.execute('''
CREATE TABLE kb_local_intents (
    intent_name TEXT PRIMARY KEY,
    response_text TEXT,
    response_link TEXT 
)
''')

# --- 3. Populate ALL Knowledge Base Tables ---
print("Populating Knowledge Base...")

# Add IFSC codes
ifsc_data = [ ('coimbatore', 'BANK0001234'), ('delhi', 'BANK0005678'), ('mumbai', 'BANK0009999') ]
cursor.executemany("INSERT OR IGNORE INTO ifsc_codes (branch_name, ifsc_code) VALUES (?, ?)", ifsc_data)

# Add interest rates
rates_data = [ ('Home Loans', '8.5%'), ('Car Loans', '9.2%'), ('Savings Account', '3.5%'), ('Personal Loan', '10.1%') ]
cursor.executemany("INSERT OR IGNORE INTO interest_rates (product_name, rate) VALUES (?, ?)", rates_data)

# --- 4. NEW: Populate the Main KB Table (with Links) ---
# All instances of 'NULL' have been replaced with 'None'
kb_data = [
    ("check_balance_guide", "To check your balance securely, you can use our NetBanking app, check your e-passbook, or use any UPI app in the 'Check Balance' section.", "https://examplelinkhere/balance"),
    ("check_transactions_guide", "You can see all your recent transactions by checking the 'Mini Statement' or 'e-Passbook' section in your NetBanking or mobile banking app.", "https://examplelinkhere/transactions"),
    ("find_account_details", "You can find your account number and customer ID printed on the front page of your bank passbook. You can also find it in your NetBanking app profile section.", "https://examplelinkhere/profile"),
    ("manage_credentials", "You can change your ATM PIN by visiting any of our nearest ATMs. You can change your NetBanking password by using the 'Forgot Password' link on the login page.", "https://examplelinkhere/change-password"),
    ("block_card_guide", "I can help with that. To confirm, are you blocking the card due to it being lost, stolen, or another reason?", "https://examplelinkhere/block-card"),
    ("update_kyc", "I can help with that. Are you looking to do a Mini-KYC (online with Aadhar) or a Full KYC?", "https://examplelinkhere/kyc-update"),
    ("transfer_funds_guide", "How would you like to transfer the money? By using a Phone Number (UPI), or by using an Account Number (NEFT/IMPS)?", "https://examplelinkhere/transfer"),
    ("get_transaction_limits", "Our standard daily transaction limits are:\n  - UPI: ₹1,00,000\n  - IMPS: ₹5,00,000\nYou can also check and set your *personal* limits within the 'Security' section of the NetBanking app.", "https://examplelinkhere/limits"),
    ("set_transaction_limits", "To set your personal transaction limits for security, please log in to the NetBanking app, go to 'Security & Settings', and 'Manage Transaction Limits'.", "https://examplelinkhere/manage-limits"),
    ("open_account", "What type of account are you interested in? We offer Savings, Current, and Demat accounts.", "https://examplelinkhere/open-account"),
    ("get_interest_rates", "I can help with that. Here are our current rates...", None), # <-- FIXED
    ("find_ifsc_code", "I can help with that. Which branch's IFSC code do you need?", None), # <-- FIXED
    ("get_bank_hours", "Our bank branches are open from 10:00 AM to 4:00 PM, Monday to Friday. We are closed on all Saturdays, Sundays, and public holidays.", None), # <-- FIXED
    ("check_loan_status_guide", "You can check your loan application status by visiting our website, logging in to your loan portal, and entering your application reference number.", "https://examplelinkhere/loan-status"),
    ("pay_bill_guide", "You can pay all your bills (electricity, phone, credit card, etc.) using the 'Bill Pay' or 'BBPS' section in our NetBanking or mobile app.", "https://examplelinkhere/bill-pay"),
    ("general_faq", "Our headquarters is located in Mumbai, India. For more information, please visit the 'About Us' section of our website.", "https://examplelinkhere/about-us"),
    ("greet", "Hello! How can I help you with your banking questions today?", None), # <-- FIXED
    ("summarize_conversation", "One moment, please. I will summarize our bank-related conversation for you.", None), # <-- FIXED
    ("fallback", "I'm sorry, I don't quite understand. Can you rephrase? I can help with account guides, transactions, and bank info.", None) # <-- FIXED
]
cursor.executemany("INSERT OR IGNORE INTO kb_local_intents (intent_name, response_text, response_link) VALUES (?, ?, ?)", kb_data)


# --- 5. Commit and Close ---
conn.commit()
conn.close()

print("Database setup complete!")
print("File 'bot_database.db' has been created and populated.")