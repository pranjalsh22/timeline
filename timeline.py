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

    # Dynamically adjust the height of the timeline based on the events
    timeline_height = 1000  # Height of the timeline
    right_column_width = 600  # Width for the right part (for expanders)
    left_column_width = 50  # Reduced width of the left column for the white line

    # Create a container for the layout using st.columns with a 1:10 width ratio
    col1, col2 = st.columns([1, 10])  # 1:10 ratio, left for the line, right for events

    # ---------------- Left Column (White Line Column) ----------------
    with col1:
        # Create the white vertical line (fixed on the left)
        st.markdown("""
            <style>
                .timeline {
                    position: fixed;
                    left: 0px;  /* Start from the very left of the screen */
                    top: 0;
                    height: 100%;  /* Make sure the line spans the entire height of the screen */
                    width: 5px;  /* Reduced width */
                    background-color: white;
                    z-index: -1; /* Ensure it stays behind the header */
                }
            </style>
        """, unsafe_allow_html=True)

        # Create the white line on the page (visible as a fixed line)
        st.markdown('<div class="timeline"></div>', unsafe_allow_html=True)

    # ---------------- Right Column (Event Expander Column) ----------------
    with col2:
        # Loop through the entries and display them in the right column
        for i, entry in enumerate(entries):
            event_date = entry[2]

            # Normalize event date (both BC and AD)
            normalized_position = parse_date(event_date)

            # If the date could not be parsed, skip this event
            if normalized_position is None:
                continue

            # Calculate position on the timeline (scaled for display)
            height_position = int((normalized_position - min_date) / (max_date - min_date) * timeline_height)

            # Create the event expander with proper HTML structure
            st.markdown(
                f"<div class=\"event\" style=\"position: absolute; top: {height_position}px; left: 5%; width: 90%;\">"
                "<div class=\"expander\">"
                "<details>"
                f"<summary>{entry[3]} ({entry[2]})</summary>"
                f"<p><strong>Scientist:</strong> {entry[1]}</p>"
                f"<p>{entry[4]}</p>"
                f"<a href=\"{entry[5]}\" target=\"_blank\">Supporting Links</a>"
                f"<p><strong>Tags:</strong> {entry[6]}</p>"
                "</details>"
                "</div>"
                "</div>", unsafe_allow_html=True
            )

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

# ---------------------MAIN--------------------------------------------------------
st.title("Physics and Mathematics Discoveries Timeline")

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
