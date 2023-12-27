import re
import streamlit as st
import holidays
import pandas as pd
import icalendar

# Get the list of available countries
available_countries = [re.sub(r"(\w)([A-Z])", r"\1 \2", value[0]) for key, value in holidays.registry.COUNTRIES.items()]

# Create the Streamlit app
def main():
    st.title("World Holidays to Calendar")
    st.subheader("Export holidays to your calendar as an .ICS file")

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
    st.write("Number of holidays:", len(holiday_list))
    st.write("Number of working days:", 365 - len(holiday_list))

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
    st.divider()
    st.subheader("About")
    st.write("Created by KL 2023")
    st.write("Thanks to the incredible holidays package: https://github.com/vacanza/python-holidays")
