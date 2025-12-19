import psycopg2
from werkzeug.security import generate_password_hash

# !!! PASTE YOUR NEON DB URI HERE !!!
NEON_DB_URI = "" 

def reset_admin_password():
    try:
        print("🔌 Connecting to Database...")
        conn = psycopg2.connect(NEON_DB_URI)
        cur = conn.cursor()

        # 1. Delete the old admin user to avoid conflicts
        print("🧹 Removing old 'admin' user...")
        cur.execute("DELETE FROM admins WHERE username = 'admin'")

        # 2. Create a fresh admin user
        # Username: admin
        # Password: admin123
        print("👤 Creating new admin user...")
        hashed_pw = generate_password_hash("admin123")
        
        cur.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s)", ('admin', hashed_pw))

        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ SUCCESS! You can now log in with:")
        print("   Username: admin")
        print("   Password: admin123")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_admin_password()