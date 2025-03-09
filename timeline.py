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

    # Add custom CSS for the timeline
    st.markdown("""
        <style>
            .timeline {
                position: relative;
                max-width: 800px;
                margin: 0 auto;
            }
            .timeline::before {
                content: '';
                position: absolute;
                top: 0;
                bottom: 0;
                width: 4px;
                background-color: blue;
                left: 50%;
                margin-left: -2px;
            }
            .event {
                padding: 10px 40px;
                position: relative;
                background-color: inherit;
                width: 50%;
            }
            .event.left {
                left: 0;
            }
            .event.right {
                left: 50%;
            }
            .event::after {
                content: '';
                position: absolute;
                width: 20px;
                height: 20px;
                right: -10px;
                background-color: blue;
                border: 4px solid white;
                top: 15px;
                border-radius: 50%;
                z-index: 1;
            }
            .event.right::after {
                left: -10px;
            }
            .event-content {
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
        </style>
    """, unsafe_allow_html=True)

    # Create the timeline container
    st.markdown('<div class="timeline">', unsafe_allow_html=True)

    # Loop through the entries and display them on the timeline
    for i, entry in enumerate(entries):
        event_date = entry[2]
        normalized_position = parse_date(event_date)

        # If the date could not be parsed, skip this event
        if normalized_position is None:
            continue

        # Calculate the position of the event on the timeline
        position_ratio = (normalized_position - min_date) / total_time_span
        position_percentage = position_ratio * 100

        # Alternate events between left and right for better visual appeal
        if i % 2 == 0:
            event_class = "event left"
        else:
            event_class = "event right"

        # Display the event
        st.markdown("""
            <div class="{event_class}" style="top: {position_percentage}%;">
                <div class="event-content">
                    <h3>{entry[3]} ({entry[2]})</h3>
                    <p><strong>Scientist:</strong> {entry[1]}</p>
                    <p>{entry[4]}</p>
                    <a href="{entry[5]}" target="_blank">Supporting Links</a>
                    <p><strong>Tags:</strong> {entry[6]}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Close the timeline container
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------MAIN--------------------------------------------------------
st.title("Timeline of Great Thoughts")

# Add some space after the timeline
st.markdown("<br>", unsafe_allow_html=True)

create_table()

# Show form if authenticated
if authenticate():
    with st.sidebar.form("add_entry_form"):
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

# Display the timeline
display_timeline()
