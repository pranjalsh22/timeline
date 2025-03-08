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

    # Create the timeline line using CSS
    st.markdown(
        "<style>"
        ".timeline {"
        "    position: relative;"
        "    width: 10px;"
        "    background-color: black;"
        "    margin-left: 50%;"
        "    margin-top: 20px;"
        "    height: 100vh;"  # Full page height
        "}"
        ".event {"
        "    position: absolute;"
        "    width: 200px;"
        "    padding: 10px;"
        "    text-align: center;"
        "    cursor: pointer;"
        "    transform: translateX(-50%);"
        "}"
        "</style>", unsafe_allow_html=True
    )

    # Create the timeline line in the center
    st.markdown('<div class="timeline"></div>', unsafe_allow_html=True)

    # Sort entries from newest to oldest
    entries = sorted(entries, key=lambda x: parse_date(x[2]), reverse=True)

    # Loop through entries and display them on the vertical timeline
    for i, entry in enumerate(entries):
        event_date = entry[2]

        # Normalize event date (both BC and AD)
        normalized_position = parse_date(event_date)

        # If the date could not be parsed, skip this event
        if normalized_position is None:
            continue

        # Calculate position on the timeline (scaled for display)
        height_position = int((normalized_position - min_date) / (max_date - min_date) * 100)  # Scaled for 100% height of the page

        # Create the event marker on the timeline (placed vertically)
        st.markdown(
            "<div class='event' style='top: {0}%; left: 50%;'>"
            "    <div class='expander'>"
            "        <details>"
            "            <summary>{1} ({2})</summary>"
            "            <p><strong>Scientist:</strong> {3}</p>"
            "            <p><strong>Description:</strong> {4}</p>"
            "            <p><strong>Tags:</strong> {5}</p>"
            "            <p><a href='{6}' target='_blank'>Learn more</a></p>"
            "        </details>"
            "    </div>"
            "</div>".format(height_position, entry[3], entry[2], entry[1], entry[4], entry[6], entry[5]), 
            unsafe_allow_html=True
        )

# Function to parse the date (handling BC and AD dates)
def parse_date(date_str):
    try:
        # Check if the date contains "BC"
        if 'BC' in date_str:
            # Handle BC dates
            date_obj = datetime.datetime.strptime(date_str.replace('BC', '').strip(), "%Y")
            return -date_obj.year  # Make BC years negative
        elif 'AD' in date_str:
            # Handle AD dates
            date_obj = datetime.datetime.strptime(date_str.replace('AD', '').strip(), "%Y")
            return date_obj.year
        else:
            # If no BC or AD, assume the date is in AD
            # Handle simple years (e.g., 1905, 300)
            date_obj = datetime.datetime.strptime(date_str.strip(), "%Y")
            return date_obj.year
    except Exception as e:
        st.error(f"Error parsing date {date_str}: {e}")
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
