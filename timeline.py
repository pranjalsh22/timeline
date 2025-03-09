import datetime
import streamlit as st
import psycopg2

# ----------------Access secrets----------------------------------------------------------------------------
DB_NAME = st.secrets["db"]["name"]
DB_USER = st.secrets["db"]["user"]
DB_PASSWORD = st.secrets["db"]["password"]
DB_HOST = st.secrets["db"]["host"]
DB_PORT = st.secrets["db"]["port"]
PASSCODE = st.secrets["app"]["passcode"]

# ----------------Authenticate and connect----------------------------------------------------------------------------
def authenticate():
    passcode = st.sidebar.text_input("Enter Passcode", type="password")
    return passcode == PASSCODE

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

# ---------------------------Data entry and access------------------------------------------------------------
def insert_entry(scientist_name, discovery_date, title, description, links, tags):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO discoveries (scientist_name, discovery_date, title, description, links, tags)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (scientist_name, discovery_date, title, description, links, tags))
        conn.commit()
        conn.close()

def fetch_entries():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM discoveries")
        data = cursor.fetchall()
        conn.close()
        return data
    return []

def update_entry(entry_id, scientist_name, discovery_date, title, description, links, tags):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE discoveries
        SET scientist_name = %s,
            discovery_date = %s,
            title = %s,
            description = %s,
            links = %s,
            tags = %s
        WHERE id = %s
        """, (scientist_name, discovery_date, title, description, links, tags, entry_id))
        conn.commit()
        conn.close()

# Function to parse the date (handling BC and AD dates)
def parse_date(date_str):
    try:
        # Strip any leading or trailing spaces from the input
        date_str = date_str.strip()

        # Check if the date contains "BC"
        if 'BC' in date_str:
            # Handle BC dates by removing 'BC' and converting the year into a negative number
            date_str = date_str.replace('BC', '').strip()
            if date_str.isdigit():
                return -int(date_str)  # Make BC years negative (e.g., 250 BC -> -250)
            else:
                st.error(f"Invalid BC year format: {date_str}")
                return None
        elif 'AD' in date_str:
            # Handle AD dates (convert it normally)
            date_str = date_str.replace('AD', '').strip()
            if date_str.isdigit():
                return int(date_str)  # For AD years (e.g., 1905 AD -> 1905)
            else:
                st.error(f"Invalid AD year format: {date_str}")
                return None
        else:
            # Handle simple years (e.g., 1905, 300) as AD years
            if date_str.isdigit():
                return int(date_str)  # AD dates are positive numbers (e.g., 1905 -> 1905)
            else:
                st.error(f"Invalid year format: {date_str}")
                return None
    except Exception as e:
        st.error(f"Error parsing date '{date_str}': {e}")
        return None

# ----------------MAKING TIMELINE-----------------------------------------------
def display_timeline():
    entries = fetch_entries()

    # Parse all dates and filter out None values
    valid_dates = [parse_date(entry[2]) for entry in entries]
    valid_dates = [date for date in valid_dates if date is not None]

    # Ensure there are valid dates to compute min and max
    if valid_dates:
        min_date = min(valid_dates)
        max_date = max(valid_dates)
    else:
        st.error("No valid dates found in the entries.")
        return

    # Calculate the total time span
    total_time_span = max_date - min_date

    # Add custom CSS for the vertical line
    st.markdown("""
        <style>
            .timeline-container {
                position: relative;
                margin-left: 50px;
            }
            .timeline-line {
                position: absolute;
                left: 20px;
                top: 0;
                bottom: 0;
                width: 4px;
                background-color: blue;
            }
            .event {
                position: relative;
                margin-bottom: 20px;
                padding-left: 40px;
            }
            .event::before {
                content: '';
                position: absolute;
                left: 16px;
                top: 10px;
                width: 12px;
                height: 12px;
                background-color: blue;
                border-radius: 50%;
                z-index: 1;
            }
        </style>
    """, unsafe_allow_html=True)

    # Create the timeline container
    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    st.markdown('<div class="timeline-line"></div>', unsafe_allow_html=True)

    # Loop through the entries and display them on the timeline
    for entry in entries:
        event_date = entry[2]
        normalized_position = parse_date(event_date)

        # If the date could not be parsed, skip this event
        if normalized_position is None:
            continue

        # Calculate the position of the event on the timeline
        position_ratio = (normalized_position - min_date) / total_time_span

        # Add spacing based on the position ratio
        st.markdown(f'<div style="margin-top: {position_ratio * 100}px;"></div>', unsafe_allow_html=True)

        # Display the event as an expander
        with st.expander(f"{entry[3]} ({entry[2]})"):
            st.markdown(f"**Scientist:** {entry[1]}")
            st.markdown(f"{entry[4]}")
            st.markdown(f"[Supporting Links]({entry[5]})")
            st.markdown(f"**Tags:** {entry[6]}")

    # Close the timeline container
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------MAIN--------------------------------------------------------
st.title("Timeline of Great Thoughts")

# Add some space after the timeline
st.markdown("<br>", unsafe_allow_html=True)

create_table()

# Show form if authenticated
if authenticate():
    # Add new entry form
    with st.sidebar.form("add_entry_form"):
        st.subheader("Add New Entry")
        scientist_name = st.text_input("Scientist Name")
        discovery_date = st.text_input("Date of Discovery (e.g., 300 BC, 1905 AD, or 1905)")
        title = st.text_input("Title of Discovery")
        description = st.text_area("Description")
        links = st.text_input("Supporting Links (comma-separated)")
        tags = st.multiselect("Tags", ["Optics", "Quantum", "Astro", "Classical Mechanics", "Thermodynamics"])
        submit_button = st.form_submit_button("Add Entry")

    if submit_button:
        tags_str = ", ".join(tags)
        insert_entry(scientist_name, discovery_date, title, description, links, tags_str)
        st.sidebar.success("Entry added successfully!")

    # Edit existing entries
    st.sidebar.subheader("Edit Existing Entry")
    entries = fetch_entries()
    entry_options = {f"{entry[3]} ({entry[2]})": entry for entry in entries}
    selected_entry_key = st.sidebar.selectbox("Select Entry to Edit", list(entry_options.keys()))

    if selected_entry_key:
        selected_entry = entry_options[selected_entry_key]
        with st.sidebar.form("edit_entry_form"):
            st.subheader("Edit Entry")
            scientist_name = st.text_input("Scientist Name", value=selected_entry[1])
            discovery_date = st.text_input("Date of Discovery", value=selected_entry[2])
            title = st.text_input("Title of Discovery", value=selected_entry[3])
            description = st.text_area("Description", value=selected_entry[4])
            links = st.text_input("Supporting Links", value=selected_entry[5])
            tags = st.multiselect("Tags", ["Optics", "Quantum", "Astro", "Classical Mechanics", "Thermodynamics"], default=selected_entry[6].split(", "))
            update_button = st.form_submit_button("Update Entry")

        if update_button:
            tags_str = ", ".join(tags)
            update_entry(selected_entry[0], scientist_name, discovery_date, title, description, links, tags_str)
            st.sidebar.success("Entry updated successfully!")

# Display the timeline
display_timeline()
