import streamlit as st
import psycopg2

# Access secrets
DB_NAME = st.secrets["db"]["name"]
DB_USER = st.secrets["db"]["user"]
DB_PASSWORD = st.secrets["db"]["password"]
DB_HOST = st.secrets["db"]["host"]
DB_PORT = st.secrets["db"]["port"]

# Connect to the database
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Create table if it doesn't exist
def create_table():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS discoveries (
            id SERIAL PRIMARY KEY,
            scientist_name TEXT,
            discovery_date TEXT,
            title TEXT,
            description TEXT,
            links TEXT,
            tags TEXT
        )
        """)
        conn.commit()
        conn.close()

# Main app function
def main():
    st.title("Physics Discoveries Timeline")
    st.sidebar.header("Add New Entry")

    # Initialize database
    create_table()

    # Show form if authenticated
    if authenticate():
        with st.sidebar.form("add_entry_form"):
            scientist_name = st.text_input("Scientist Name")
            discovery_date = st.text_input("Date of Discovery (e.g., 300 BC, 1905 AD)")
            title = st.text_input("Title of Discovery")
            description = st.text_area("Description")
            links = st.text_input("Supporting Links (comma-separated)")
            tags = st.multiselect("Tags", ["Optics", "Quantum", "Astro", "Classical Mechanics", "Thermodynamics"])
            submit_button = st.form_submit_button("Add Entry")

        if submit_button:
            tags_str = ", ".join(tags)
            insert_entry(scientist_name, discovery_date, title, description, links, tags_str)
            st.sidebar.success("Entry added successfully!")

    # Display the timeline
    display_timeline()

if __name__ == "__main__":
    main()
