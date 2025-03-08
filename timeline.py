import datetime
import streamlit as st

# Function to parse the date (handling BC and AD dates)
def parse_date(date_str):
    try:
        # Check if the date contains "BC"
        if 'BC' in date_str:
            # Handle BC dates by removing the 'BC' and converting the year into a negative number
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
            # If no BC or AD, assume the date is in AD
            # Handle simple years (e.g., 1905, 300)
            if date_str.isdigit():
                return int(date_str)  # AD dates are positive numbers
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

    # Dynamically adjust the height of the timeline based on the events
    timeline_height = 1000  # Increased height for better display

    # Create a timeline line using CSS (make the timeline white)
    st.markdown(f"""
    <style>
        .timeline {{
            position: relative;
            width: 10px;
            background-color: white; /* White background */
            margin-left: 50%;
            margin-top: 50px;
            height: {timeline_height}px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Create the timeline line in the center
    st.markdown('<div class="timeline"></div>', unsafe_allow_html=True)

    # Loop through entries and display them on the vertical timeline
    for i, entry in enumerate(entries):
        event_date = entry[2]

        # Normalize event date (both BC and AD)
        normalized_position = parse_date(event_date)

        # If the date could not be parsed, skip this event
        if normalized_position is None:
            continue

        # Calculate position on the timeline (scaled for display)
        height_position = int((normalized_position - min_date) / (max_date - min_date) * timeline_height)  # timeline_height for scaling

        # Create the event marker and show it inside the expander (no button now)
        with st.expander(f"{entry[3]} ({entry[2]})"):
            A, B = st.columns([4, 1])
            with A:
                st.info(f"{entry[3]} by {entry[1]} in {entry[2]}")
                st.success(f"{entry[4]}")
                st.markdown(f"[{entry[5]}]({entry[4]})")
            with B:
                st.success(f"Tags: {entry[6]}")

# Function to simulate fetching entries (for testing purposes)
def fetch_entries():
    return [
        ("Einstein", "1905 AD", "Theory of Relativity", "Description of Theory of Relativity", "http://example.com", "Theory"),
        ("Newton", "1687 AD", "Laws of Motion", "Newton's 3 Laws of Motion", "http://example.com", "Physics"),
        ("Pythagoras", "500 BC", "Pythagorean Theorem", "Mathematical theorem", "http://example.com", "Math"),
        ("Galileo", "1610 AD", "Telescope", "Galileo's improvements to the telescope", "http://example.com", "Physics"),
        ("Aristotle", "350 BC", "Classical Physics", "Philosophy of motion and matter", "http://example.com", "Physics")
    ]

# Add some space after the timeline
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------MAIN--------------------------------------------------------
st.title("Physics and Mathematics Discoveries Timeline")

# Display the timeline
display_timeline()
