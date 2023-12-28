import re
import streamlit as st
import holidays
import pandas as pd
import icalendar
import datetime

# Sunday counter
def count_sundays(year: int):
    sundays = 0
    for month in range(1, 13):  # for each month in the year
        # loop through the days of the month
        for day in range(1, 32):
            try:
                # check if it is a Sunday
                if datetime.datetime(year, month, day).weekday() == 6:
                    sundays += 1
            except ValueError:
                # if not, it must be out of range for this month
                break
    return sundays

# Set Streamlit page config
st.set_page_config(
    page_title="World Holidays to ICS App",
    page_icon="📆",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://github.com/Karlosll91/holidays_to_ics/issues",
    }
)

# Show greetings
with st.sidebar:
    st.title("About")
    st.write("This app allows you to export the holidays of a country to an .ICS file to add them to your calendar")
    st.write("You can also import an existing .ICS file to see the events in it")
    st.write("The app is based on the incredible holidays package: https://github.com/vacanza/python-holidays")
    st.write("Created by KL 2023")


# Get the list of available countries
available_countries = [re.sub(r"(\w)([A-Z])", r"\1 \2", value[0]) for key, value in holidays.registry.COUNTRIES.items()]

# Create the Streamlit app
def main():
    st.title("World Holidays to Calendar")

    # Select action
    action = st.selectbox("", ["Select one action...", "Generate new calendar", "Load existing calendar"])
    if action == "Generate new calendar":
        generate_calendar()
    elif action == "Load existing calendar":
        load_calendar()
    
def parse_ics(ics):
    events = []
    cal = icalendar.Calendar.from_ical(ics)

    for component in cal.walk():
        if component.name == "VEVENT":
            event = {
                'start_time': component.get('dtstart').dt,
                'summary': component.get('summary')
            }
            events.append(event)
    events = pd.DataFrame(events)
    return events

def load_calendar():
    # Upload ICS file
    uploaded_file = st.file_uploader("Upload ICS file", type=["ics"])
    if uploaded_file is not None:
        # Read ICS file
        uploaded_file = uploaded_file.read().decode("utf-8")

        # Parse ICS file
        holiday_list = parse_ics(uploaded_file)

        # Display the holidays
        display_calendar(holiday_list)

def generate_calendar():
    c1,c2,c3 = st.columns(3)

    with c1:
        # Country selection
        country = st.selectbox("Country", available_countries)

        # Delete the space in the country code
        country_code = country.replace(" ", "")

    with c2:
        # Get current year
        current_year = int(pd.Timestamp.now().year)

        # Year selection
        year = st.number_input("Year", min_value=1900, max_value=2100, value=current_year)

    with c3:  
        # Get default language
        default_language = holidays.country_holidays(country_code).default_language

        # Get supported languages
        supported_languages = holidays.country_holidays(country_code).supported_languages

        # Language selection
        language = st.selectbox("Language", supported_languages, index=0 if default_language not in supported_languages else supported_languages.index(default_language))
        
    # Get the list of holidays
    holiday_list = holidays.country_holidays(country=country_code, years=year, language=language)
    holiday_list = pd.DataFrame(holiday_list.items(), columns=["start_time", "summary"])
    holiday_list = holiday_list.sort_values(by=["start_time"])
    holiday_list.index = holiday_list.index + 1

    display_calendar(holiday_list, country=country, year=year)

def export_calendar(holiday_list, country=""):
    # Generate ICS file
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//KL-HolidayToICS//EN\nCALSCALE:GREGORIAN\n"
    for index, row in holiday_list.iterrows():
        ics += "BEGIN:VEVENT\n"
        ics += "DTSTART;VALUE=DATE:" + row["start_time"].strftime("%Y%m%d") + "\n"
        ics += "DTEND;VALUE=DATE:" + row["start_time"].strftime("%Y%m%d") + "\n"
        ics += "SUMMARY:" + row["summary"] + "\n"
        ics += "DESCRIPTION:" + row["summary"] + " in " + country + "\n"
        ics += "END:VEVENT\n"
    ics += "END:VCALENDAR"
    return ics

def display_calendar(holiday_list, country="", year=""):
    # Display the holidays stats
    st.subheader("Holidays stats:")
    if len(holiday_list) > 0:
        year = holiday_list["start_time"].iloc[0].strftime("%Y")
        total_days = 366 if pd.Timestamp(year).is_leap_year else 365
        st.write(f"Total days for {year}:", total_days)
        st.write("Number of holidays:", len(holiday_list))
        total_sundays = count_sundays(int(year))
        st.write("Number of Sundays:", total_sundays)
        st.write("Number of working days:", total_days - len(holiday_list) - total_sundays)

    # Display a plot of the sum of holidays by month sorted by month number
    # from calendar import month_name
    try:
        holiday_plot = holiday_list.copy()
        holiday_plot["start_time"] = pd.to_datetime(holiday_plot["start_time"])
        holiday_plot["month"] = holiday_plot["start_time"].dt.month
        holiday_plot = holiday_plot.groupby("month").count()
        holiday_plot = holiday_plot.reindex(range(1, 13), fill_value=0)
        holiday_plot = holiday_plot.rename(columns={"start_time": "count"})
        holiday_plot = holiday_plot.reset_index()

        # Display the plot only for the sum of holidays
        holiday_plot = holiday_plot[["month", "count"]]
        holiday_plot = holiday_plot.sort_values(by=["month"])
        holiday_plot = holiday_plot.rename(columns={"count": "Holidays"})
        holiday_plot = holiday_plot.set_index(["month"])
        # holiday_plot = holiday_plot.reset_index(drop=True)
        st.bar_chart(holiday_plot)
    except:
        pass

    # Display the holidays
    st.subheader("Holidays:")
    holiday_list = holiday_list.reset_index(drop=True)
    
    # Add Day of the week column
    holiday_list["start_time_code"] = pd.to_datetime(holiday_list["start_time"])
    holiday_list["Day"] = holiday_list["start_time_code"].dt.day_name()
    holiday_list = holiday_list.drop(columns=["start_time_code"])

    
    if country == "":
        st.dataframe(holiday_list, height=len(holiday_list)*40)
    else:
        st.text("You can edit or delete the holidays in the table below, even add new ones")
        holiday_list_mod = st.data_editor(holiday_list, 
                            hide_index=True, 
                            use_container_width=True,
                            num_rows="dynamic",
                            key="holiday_list_mod",
                            height=len(holiday_list)*40,
                            #    disabled=["Index"],
                            #    column_config={"Date": {"width": 20}, "Holiday": {"width": 400}}
                            )
    
        # Export holidays to ICS file
        st.subheader("Export:")
        st.write("Export holidays to a ICS file to add them to your calendar")

        if st.button("Generate ICS file"):
            # Drop the Day column
            holiday_list_mod = holiday_list_mod.drop(columns=["Day"])
            st.success("ICS file generated")
            # Download ICS file
            st.download_button(
                label="Download ICS file",
                data=export_calendar(country=country, holiday_list=holiday_list_mod),
                file_name=f"holidays {country} {year}.ics",
                mime="text/calendar",
        )

if __name__ == "__main__":
    main()
    
    # Show greetings
    # st.divider()
    # st.subheader("About")
    # st.write("Created by KL 2023")
    # st.write("Thanks to the incredible holidays package: https://github.com/vacanza/python-holidays")
