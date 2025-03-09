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
    valid_entries = []
    for entry in entries:
        parsed_date = parse_date(entry[2])
        if parsed_date is not None:
            valid_entries.append((parsed_date, entry))

    # Add sorting options
    sort_order = st.sidebar.selectbox("Sort Order", ["Ascending", "Descending"], index=0)
    if sort_order == "Ascending":
        valid_entries.sort(key=lambda x: x[0])
    else:
        valid_entries.sort(key=lambda x: x[0], reverse=True)

    # Add tag filtering with checkboxes
    all_tags = ["biology", "philosophy", "mathematics", "physics", "optics", "quantum", "astro", "classical mechanics", "thermodynamics"]
    st.sidebar.subheader("Filter by Tags")
    selected_tags = []
    with st.sidebar.form("tag_filter_form"):
        for tag in all_tags:
            if st.checkbox(tag, value=True, key=tag):
                selected_tags.append(tag)
        filter_button = st.form_submit_button("Apply Filter")

    # Filter entries based on selected tags
    filtered_entries = []
    for parsed_date, entry in valid_entries:
        tags = entry[6].split(", ")
        if any(tag in selected_tags for tag in tags):
            filtered_entries.append((parsed_date, entry))

    # Ensure there are valid dates to compute min and max
    if not filtered_entries:
        st.error("No valid entries found for the selected tags.")
        return

    # Extract min and max dates from filtered entries
    min_date = filtered_entries[0][0]
    max_date = filtered_entries[-1][0]

    # Calculate the total time span
    total_time_span = max_date - min_date

    # Add custom CSS for a modern tech look
    st.markdown("""
        <style>
            /* Modern font */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Montserrat:wght@400;500;700&display=swap');
            html, body, .stApp, .stButton>button, .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
                font-family: 'Montserrat', sans-serif;
            }

            /* Glowing blue title */
            .glowing-title {
                font-size: 3rem;
                font-weight: 700;
                color: #00bcd4;
                text-align: center;
                text-shadow: 0 0 10px #00bcd4, 0 0 20px #00bcd4, 0 0 30px #00bcd4, 0 0 40px #00bcd4;
                animation: glow 1.5s ease-in-out infinite alternate;
            }
            @keyframes glow {
                from {
                    text-shadow: 0 0 10px #00bcd4, 0 0 20px #00bcd4, 0 0 30px #00bcd4, 0 0 40px #00bcd4;
                }
                to {
                    text-shadow: 0 0 20px #00bcd4, 0 0 30px #00bcd4, 0 0 40px #00bcd4, 0 0 50px #00bcd4;
                }
            }

            /* Dark theme with neon accents */
            .stApp {
                background-color: #0e1117;
                color: #ffffff;
            }
            .stSidebar {
                background-color: #1e1e1e;
            }
            .stButton>button {
                background-color: #00bcd4;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: 500;
            }
            .stButton>button:hover {
                background-color: #0097a7;
            }
            .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #00bcd4;
                border-radius: 5px;
            }

            /* Blue highlight for expander */
            .stExpander {
                border: 2px solid #00bcd4 !important;
                border-radius: 10px !important;
                margin: 10px 0 !important;
            }
            .stExpander .stExpanderHeader {
                background-color: #1e1e1e !important;
                color: #00bcd4 !important;
                font-weight: 500 !important;
                padding: 10px 20px !important;
            }
            .stExpander .stExpanderContent {
                background-color: #1e1e1e !important;
                padding: 20px !important;
            }

            /* Card styling for events */
            .event-card {
                background-color: #1e1e1e;
                border: 1px solid #00bcd4;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 8px rgba(0, 188, 212, 0.2);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .event-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 16px rgba(0, 188, 212, 0.3);
            }
            .event-card h3 {
                color: #00bcd4;
                margin-bottom: 10px;
            }
            .event-card p {
                color: #ffffff;
                margin: 5px 0;
            }
            .event-card a {
                color: #00bcd4;
                text-decoration: none;
            }
            .event-card a:hover {
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)

    # Display the glowing title
    st.markdown('<h1 class="glowing-title">Timeline of Great Thoughts</h1>', unsafe_allow_html=True)

    # Loop through the filtered entries and display them on the timeline
    for parsed_date, entry in filtered_entries:
        # Calculate the position of the event on the timeline
        position_ratio = (parsed_date - min_date) / total_time_span

        # Add spacing based on the position ratio
        st.markdown(f'<div style="margin-top: {position_ratio * 100}px;"></div>', unsafe_allow_html=True)

        # Display the event as an expander
        with st.expander(f"{entry[3]} ({entry[2]})"):
            event_html = """
                <div class="event-card">
                    <h3>{title} ({date})</h3>
                    <p><strong>Scientist:</strong> {scientist}</p>
                    <p>{description}</p>
                    <a href="{links}" target="_blank">Supporting Links</a>
                    <p><strong>Tags:</strong> {tags}</p>
                </div>
            """.format(
                title=entry[3],
                date=entry[2],
                scientist=entry[1],
                description=entry[4],
                links=entry[5],
                tags=entry[6]
            )
            st.markdown(event_html, unsafe_allow_html=True)

# ---------------------MAIN--------------------------------------------------------

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
        tags = st.multiselect("Tags", ["biology", "philosophy", "mathematics", "physics", "optics", "quantum", "astro", "classical mechanics", "thermodynamics"])
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
            tags = st.multiselect("Tags", ["biology", "philosophy", "mathematics", "physics", "optics", "quantum", "astro", "classical mechanics", "thermodynamics"], default=selected_entry[6].split(", "))
            update_button = st.form_submit_button("Update Entry")

        if update_button:
            tags_str = ", ".join(tags)
            update_entry(selected_entry[0], scientist_name, discovery_date, title, description, links, tags_str)
            st.sidebar.success("Entry updated successfully!")

# Display the timeline
display_timeline()
