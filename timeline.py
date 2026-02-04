import datetime
import streamlit as st
import sqlite3

# ----------------Access secrets----------------------------------------------------------------------------
PASSCODE = st.secrets["app"]["passcode"]

# ----------------Database connection (SQLite, cached)-----------------------------------------------------
@st.cache_resource
def get_connection():
    return sqlite3.connect("timeline.db", check_same_thread=False)

# ----------------Authenticate----------------------------------------------------------------------------
def authenticate():
    passcode = st.sidebar.text_input("Enter Passcode", type="password")
    return passcode == PASSCODE

# ----------------Create table once-----------------------------------------------------------------------
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discoveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scientist_name TEXT,
        discovery_date TEXT,
        title TEXT,
        description TEXT,
        links TEXT,
        tags TEXT
    )
    """)
    conn.commit()

if "db_initialized" not in st.session_state:
    create_table()
    st.session_state.db_initialized = True

# ---------------------------Data entry and access---------------------------------------------------------
def insert_entry(scientist_name, discovery_date, title, description, links, tags):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO discoveries (scientist_name, discovery_date, title, description, links, tags)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (scientist_name, discovery_date, title, description, links, tags))
    conn.commit()
    st.cache_data.clear()

@st.cache_data
def fetch_entries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM discoveries")
    return cursor.fetchall()

def update_entry(entry_id, scientist_name, discovery_date, title, description, links, tags):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE discoveries
    SET scientist_name = ?,
        discovery_date = ?,
        title = ?,
        description = ?,
        links = ?,
        tags = ?
    WHERE id = ?
    """, (scientist_name, discovery_date, title, description, links, tags, entry_id))
    conn.commit()
    st.cache_data.clear()

# ----------------Date parsing (BC / AD)-------------------------------------------------------------------
def parse_date(date_str):
    try:
        date_str = date_str.strip()

        if 'BC' in date_str:
            date_str = date_str.replace('BC', '').strip()
            if date_str.isdigit():
                return -int(date_str)
            else:
                st.error(f"Invalid BC year format: {date_str}")
                return None
        elif 'AD' in date_str:
            date_str = date_str.replace('AD', '').strip()
            if date_str.isdigit():
                return int(date_str)
            else:
                st.error(f"Invalid AD year format: {date_str}")
                return None
        else:
            if date_str.isdigit():
                return int(date_str)
            else:
                st.error(f"Invalid year format: {date_str}")
                return None
    except Exception as e:
        st.error(f"Error parsing date '{date_str}': {e}")
        return None

# ----------------MAKING TIMELINE---------------------------------------------------------------------------
def display_timeline():
    entries = fetch_entries()

    valid_entries = []
    for entry in entries:
        parsed_date = parse_date(entry[2])
        if parsed_date is not None:
            valid_entries.append((parsed_date, entry))

    sort_order = st.sidebar.selectbox("Sort Order", ["Ascending", "Descending"], index=0)
    if sort_order == "Ascending":
        valid_entries.sort(key=lambda x: x[0])
    else:
        valid_entries.sort(key=lambda x: x[0], reverse=True)

    all_tags = ["Biology", "Philosophy", "Mathematics", "Physics", "Optics", "Quantum", "Astro", "Classical Mechanics",
                "Thermodynamics","Statistical","Electronics","Material Science","Computer Science"]

    st.sidebar.subheader("Filter by Tags")
    selected_tags = []
    with st.sidebar.form("tag_filter_form"):
        for tag in all_tags:
            if st.checkbox(tag, value=True, key=tag):
                selected_tags.append(tag)
        st.form_submit_button("Apply Filter")

    filtered_entries = []
    for parsed_date, entry in valid_entries:
        tags = entry[6].split(", ") if entry[6] else []
        if any(tag in selected_tags for tag in tags):
            filtered_entries.append((parsed_date, entry))

    if not filtered_entries:
        st.error("No valid entries found for the selected tags.")
        return

    min_date = filtered_entries[0][0]
    max_date = filtered_entries[-1][0]
    total_time_span = max_date - min_date if max_date != min_date else 1

    # ----------------CSS (UNCHANGED LOOK)-----------------------------------------------------------------
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Montserrat:wght@400;500;700&display=swap');
            html, body, .stApp, .stButton>button, .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
                font-family: 'Montserrat', sans-serif;
            }
            .glowing-title {
                font-size: 3rem;
                font-weight: 700;
                color: #00bcd4;
                text-align: center;
                text-shadow: 0 0 10px #00bcd4, 0 0 20px #00bcd4, 0 0 30px #00bcd4, 0 0 40px #00bcd4;
                animation: glow 1.5s ease-in-out infinite alternate;
            }
            @keyframes glow {
                from { text-shadow: 0 0 10px #00bcd4, 0 0 20px #00bcd4, 0 0 30px #00bcd4, 0 0 40px #00bcd4; }
                to { text-shadow: 0 0 20px #00bcd4, 0 0 30px #00bcd4, 0 0 40px #00bcd4, 0 0 50px #00bcd4; }
            }
            .stApp { background-color: #0e1117; color: #ffffff; }
            .stSidebar { background-color: #1e1e1e; }
            .stExpander { border: 2px solid #00bcd4 !important; border-radius: 10px !important; margin: 10px 0 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="glowing-title">Timeline of Great Thoughts</h1>', unsafe_allow_html=True)

    for parsed_date, entry in filtered_entries:
        position_ratio = (parsed_date - min_date) / total_time_span
        st.markdown(f'<div style="margin-top: {position_ratio * 100}px;"></div>', unsafe_allow_html=True)

        with st.expander(f"{entry[3]} ({entry[2]})"):
            event_html = f"""
                <div class="event-card">
                    <h3>{entry[3]} ({entry[2]})</h3>
                    <p><strong>Scientist:</strong> {entry[1]}</p>
                    <p>{entry[4]}</p>
                    <a href="{entry[5]}" target="_blank">Supporting Links</a>
                    <p><strong>Tags:</strong> {entry[6]}</p>
                </div>
            """
            st.markdown(event_html, unsafe_allow_html=True)

# ---------------------MAIN--------------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)

if authenticate():
    if submit_button:
        # Strip whitespace and validate
        if not scientist_name.strip():
            st.sidebar.error("Scientist name is required.")
        elif not discovery_date.strip():
            st.sidebar.error("Discovery date is required.")
        elif not title.strip():
            st.sidebar.error("Title is required.")
        elif not description.strip():
            st.sidebar.error("Description is required.")
        elif not links.strip():
            st.sidebar.error("At least one supporting link is required.")
        elif not tags or len(tags) == 0:
            st.sidebar.error("You must select at least one tag.")
        else:
            tags_str = ", ".join(tags)
            insert_entry(scientist_name.strip(), discovery_date.strip(), title.strip(), description.strip(), links.strip(), tags_str)
            st.sidebar.success("Entry added successfully!")
            st.rerun()

    st.sidebar.subheader("Edit Existing Entry")
    entries = fetch_entries()
    entry_options = {f"{entry[3]} ({entry[2]})": entry for entry in entries}

    if entry_options:
        selected_entry_key = st.sidebar.selectbox("Select Entry to Edit", list(entry_options.keys()))
        selected_entry = entry_options[selected_entry_key]

        with st.sidebar.form("edit_entry_form"):
            scientist_name = st.text_input("Scientist Name", value=selected_entry[1])
            discovery_date = st.text_input("Date of Discovery", value=selected_entry[2])
            title = st.text_input("Title of Discovery", value=selected_entry[3])
            description = st.text_area("Description", value=selected_entry[4])
            links = st.text_input("Supporting Links", value=selected_entry[5])

            tags_list = selected_entry[6].split(", ") if selected_entry[6] else []
            tags = st.multiselect("Tags",
                                  ["Biology", "Philosophy", "Mathematics", "Physics", "Optics", "Quantum", "Astro",
                                   "Classical Mechanics", "Thermodynamics","Statistical","Electronics","Material Science","Computer Science"],
                                  default=tags_list)

            update_button = st.form_submit_button("Update Entry")

        if update_button:
            tags_str = ", ".join(tags)
            update_entry(selected_entry[0], scientist_name, discovery_date, title, description, links, tags_str)
            st.sidebar.success("Entry updated successfully!")

display_timeline()
