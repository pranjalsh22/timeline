import streamlit as st
import psycopg2
import datetime

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

    # Get min and max dates from the database to scale events vertically
    min_date = min([parse_date(entry[2]) for entry in entries if parse_date(entry[2]) is not None])
    max_date = max([parse_date(entry[2]) for entry in entries if parse_date(entry[2]) is not None])

    # Create a timeline line using CSS
    st.markdown("""
    <style>
        .timeline {
            position: relative;
            width: 10px;
            background-color: black;
            margin-left: 50%;
            margin-top: 50px;
            height: 600px;
        }
        .event {
            position: absolute;
            width: 150px;
            padding: 5px;
            background-color: lightblue;
            border: 1px solid black;
            text-align: center;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create the timeline line in the center
    st.markdown('<div class="timeline"></div>', unsafe_allow_html=True)

    # Loop through entries and display them on the vertical timeline
    for i, entry in enumerate(entries):
        event_date = entry[2]

        # Normalize event date (both BC and AD)
        normalized_position = parse_date(event_date)

        # Calculate position on the timeline (scaled for display)
        height_position = int((normalized_position - min_date) / (max_date - min_date) * 600)  # 600px height for the timeline

        # Display the event as a button and expanders for details
        event_button = st.button(f"{entry[3]} - {entry[2]}", key=f"button_{i}")

        # When button is clicked, show details in an expander
        if event_button:
            with st.expander(f"Details of {entry[3]}"):
                A, B = st.columns([4, 1])
                with A:
                    st.info(f"{entry[3]} by {entry[1]} in {entry[2]}")
                    st.success(f"{entry[4]}")
                    st.markdown(f"[{entry[5]}]({entry[4]})")
                with B:
                    st.success(f"Tags: {entry[6]}")

        # Create the event marker on the timeline (placed vertically)
        st.markdown(f"""
        <div class="event" style="top: {height_position}px;">
            {entry[3]}
        </div>
        """, unsafe_allow_html=True)

# Function to parse the date (handling BC and AD dates)
def parse_date(date_str):
    try:
        if 'BC' in date_str:
            # Handle BC dates
            date_obj = datetime.datetime.strptime(date_str, "%Y BC")
            return -date_obj.year  # Make BC years negative
        elif 'AD' in date_str:
            # Handle AD dates
            date_obj = datetime.datetime.strptime(date_str, "%Y AD")
            return date_obj.year
        else:
            return None
    except Exception as e:
        st.error(f"Error parsing date {date_str}: {e}")
        return None

# Add some space after the timeline
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------MAIN--------------------------------------------------------
st.title("Physics and Mathematics Discoveries Timeline")
st.sidebar.header("Add New Entry")
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
