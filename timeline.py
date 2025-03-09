def display_timeline():
    entries = fetch_entries()

    # Parse all dates and filter out None values
    valid_entries = []
    for entry in entries:
        parsed_date = parse_date(entry[2])
        if parsed_date is not None:
            valid_entries.append((parsed_date, entry))

    # Sort entries by parsed date
    valid_entries.sort(key=lambda x: x[0])

    # Ensure there are valid dates to compute min and max
    if not valid_entries:
        st.error("No valid dates found in the entries.")
        return

    # Extract min and max dates from sorted entries
    min_date = valid_entries[0][0]
    max_date = valid_entries[-1][0]

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

    # Loop through the sorted entries and display them on the timeline
    for parsed_date, entry in valid_entries:
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
