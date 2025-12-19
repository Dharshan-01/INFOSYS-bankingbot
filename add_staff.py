import psycopg2

# !!! PASTE YOUR NEON DB URI HERE !!!
NEON_DB_URI = "" 

def fix_and_add_staff():
    print("🚀 Script started... (If you see this, Python is working)")
    try:
        print("🔌 Attempting to connect to Neon DB (10s timeout)...")
        conn = psycopg2.connect(NEON_DB_URI, connect_timeout=10)
        cur = conn.cursor()
        print("✅ Connected!")

        # 1. DELETE OLD TABLE (The Fix)
        print("🧹 Dropping old 'employees' table...")
        cur.execute("DROP TABLE IF EXISTS employees CASCADE;")
        conn.commit()

        # 2. CREATE NEW TABLE (With correct columns)
        print("🛠️  Creating fresh 'employees' table...")
        cur.execute("""
            CREATE TABLE employees (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                branch_name TEXT NOT NULL
            );
        """)
        print("✅ Table created!")
        conn.commit()

        # 3. INSERT DATA
        staff_list = [
            ("Sarah Conner", "Manager", "Downtown Branch"),
            ("James Bond", "Security Head", "Downtown Branch"),
            ("Peter Parker", "Intern", "Downtown Branch"),
            ("Tony Stark", "IT Admin", "Tech Park Branch"),
            ("Steve Rogers", "Manager", "Tech Park Branch"),
            ("Natasha Romanoff", "HR Lead", "City Center"),
            ("Bruce Wayne", "Investor Relations", "City Center"),
            ("Clark Kent", "Teller", "City Center")
        ]

        print(f"👤 Adding {len(staff_list)} Staff Members...")
        for name, role, branch in staff_list:
            cur.execute(
                "INSERT INTO employees (name, role, branch_name) VALUES (%s, %s, %s)",
                (name, role, branch)
            )

        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ SUCCESS! Staff table reset and data added.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_and_add_staff()