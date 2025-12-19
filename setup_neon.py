import psycopg2
from werkzeug.security import generate_password_hash
import random
from datetime import datetime, timedelta

# !!! PASTE YOUR NEON DB URI HERE !!!
NEON_DB_URI = "" 

def setup_database():
    try:
        print("🔌 Connecting to Nova Finance DB...")
        conn = psycopg2.connect(NEON_DB_URI)
        cursor = conn.cursor()

        # --- 1. CLEANUP ---
        cursor.execute("DROP TABLE IF EXISTS customers CASCADE;")
        
        # --- 2. CREATE TABLE ---
        print("🛠️ Creating Customers Table...")
        cursor.execute("""
            CREATE TABLE customers (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                account_number TEXT UNIQUE,
                balance FLOAT,
                account_type TEXT, -- Savings/Current
                joined_date DATE,
                has_loan BOOLEAN,
                loan_type TEXT,
                loan_amount FLOAT,
                loan_outstanding FLOAT,
                last_login TIMESTAMP
            );
        """)

        # --- 3. GENERATE DUMMY DATA ---
        print("👤 Generating Nova Finance Customers...")
        
        # Helper to get random date
        def rand_date():
            start = datetime.now() - timedelta(days=2000)
            return start + timedelta(days=random.randint(1, 2000))

        # Format: (User, Pass, Name, Bal, Type, Loan?, LoanType, LoanAmt)
        users = [
            ("user1", "pass1", "Arjun Reddy", 54000.50, "Savings", True, "Home Loan", 2500000),
            ("user2", "pass2", "Priya Menon", 125000.00, "Salary", False, None, 0),
            ("user3", "pass3", "Rahul Dravid", 850.75, "Savings", True, "Car Loan", 500000),
            ("rich_guy", "money", "Vijay Mallya", 9999999.99, "Current", True, "Business Loan", 10000000),
            ("student", "study", "Sneha Paul", 2500.00, "Student", True, "Education Loan", 400000)
        ]

        for u, p, name, bal, ac_type, has_ln, ln_type, ln_amt in users:
            pw_hash = generate_password_hash(p)
            acc_num = f"NOVA{random.randint(10000000, 99999999)}"
            join_dt = rand_date()
            
            # If they have a loan, calculate random outstanding amount
            outstanding = ln_amt * 0.8 if has_ln else 0
            
            cursor.execute("""
                INSERT INTO customers 
                (username, password_hash, full_name, account_number, balance, account_type, joined_date, has_loan, loan_type, loan_amount, loan_outstanding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (u, pw_hash, name, acc_num, bal, ac_type, join_dt, has_ln, ln_type, ln_amt, outstanding))
            
            print(f"   ✅ Created: {name} (User: {u} / Pass: {p})")

        conn.commit()
        conn.close()
        print("\n🎉 Nova Finance Database Ready!")

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    setup_database()