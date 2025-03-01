import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


# Access secrets
DB_NAME = st.secrets["db"]["name"]
DB_USER = st.secrets["db"]["user"]
DB_PASSWORD = st.secrets["db"]["password"]
DB_HOST = st.secrets["db"]["host"]
DB_PORT = st.secrets

# Connect to PostgreSQL database
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

# Create table if it doesn't exist
def create_table():
    conn = get_connection()
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

# Insert data into the database
def insert_entry(scientist_name, discovery_date, title, description, links, tags):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO discoveries (scientist_name, discovery_date, title, description, links, tags)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (scientist_name, discovery_date, title, description, links, tags))
    conn.commit()
    conn.close()

# Fetch all entries from the database
def fetch_entries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM discoveries")
    data = cursor.fetchall()
    conn.close()
    return data

# Authenticate user with a passcode
def authenticate():
    PASSCODE = os.getenv("PASSCODE")
    passcode = st.sidebar.text_input("Enter Passcode", type="password")
    return passcode == PASSCODE

# Display the timeline
def display_timeline():
    entries = fetch_entries()
    for entry in entries:
        st.write(f"**{entry[2]}** ({entry[1]})")
        st.write(f"**Scientist:** {entry[1]}")
        st.write(f"**Description:** {entry[3]}")
        st.write(f"**Links:** {entry[4]}")
        st.write(f"**Tags:** {entry[5]}")
        st.write("---")

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
