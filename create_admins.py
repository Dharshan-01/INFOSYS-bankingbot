import psycopg2
from werkzeug.security import generate_password_hash

# !!! PASTE YOUR NEON DB CONNECTION STRING HERE !!!
NEON_DB_URI = "" 

def create_admin_team():
    try:
        print("🔌 Connecting to Neon DB...")
        conn = psycopg2.connect(NEON_DB_URI)
        cursor = conn.cursor()

        # 1. Reset Admin Table (Clear old accounts)
        print("🧹 Clearing old admin accounts...")
        cursor.execute("DROP TABLE IF EXISTS admins;")
        cursor.execute("""
            CREATE TABLE admins (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin'
            );
        """)

        # 2. Define the 5 Admin Users
        # Format: (Username, Password)
        new_admins = [
            ("admin1", "pass_one_123"),
            ("admin2", "pass_two_456"),
            ("admin3", "pass_three_789"),
            ("super_admin", "secure_master_999"),
            ("manager_dave", "dave_bank_2025")
        ]

        print("👤 Creating 5 New Admin Accounts...")
        
        for user, raw_pass in new_admins:
            # Hash the password for security
            hashed_pw = generate_password_hash(raw_pass)
            
            try:
                cursor.execute(
                    "INSERT INTO admins (username, password_hash) VALUES (%s, %s)", 
                    (user, hashed_pw)
                )
                print(f"   ✅ Created: {user} / {raw_pass}")
            except Exception as e:
                print(f"   ❌ Error creating {user}: {e}")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 Success! You can now log in with any of these 5 accounts.")

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    create_admin_team()