from turtle import width
import pandas as pd
import streamlit as st
from pandas.core.indexes.datetimelike import DatetimeTimedeltaMixin
import datetime
import plotly.express as px
from streamlit.elements import image, text
from streamlit.proto.Image_pb2 import Image
from PIL import Image
import os.path


#Set Page Size
st.set_page_config(layout="wide")


# Create a Function That Reads in a csv, Selects Relevant Columns, Formats a Date, and Then Sorts by That Date
def import_data(path,date_col,columns):
    df = pd.read_csv(path)
    df = df[columns]
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df = df.sort_values(by=date_col)
    return df


#Some of These are Massive. Add Caching and Update the Import Function
@st.cache
def import_large_data(path,date_col,columns):
    df = pd.read_csv(path)
    df = df[columns]
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df["Month"] = df[date_col] + pd.offsets.MonthEnd(0)
    df = df.sort_values(by=date_col)
    df = df.loc[(df["Month"]== df["Month"].max())]
    return df


#Create Preliminary Variables that Will be Used in This Analysis
ontario_population = 14915270 #Based off of Q4 2021
ontario_population_under_five = 1882571 #Estimate based on age 0-4
eligible_for_vaccines = ontario_population-ontario_population_under_five #Children Under Five Not Eligible for a Vaccine 


#Import Datasets
#Daily COVID-19 Cases in Ontario
covid_status = 'https://data.ontario.ca/dataset/f4f86e54-872d-43f8-8a86-3892fd3cb5e6/resource/ed270bb8-340b-41f9-a7c6-e8ef587e6d11/download/covidtesting.csv'
covid_status_columns = ["Reported Date","Total Cases","Percent positive tests in last day","Resolved","Number of patients hospitalized with COVID-19","Number of patients in ICU due to COVID-19","Deaths",\
    "Total tests completed in the last day"]

daily_cases = import_data(covid_status,"Reported Date",covid_status_columns)

daily_cases.rename(columns={"Percent positive tests in last day":"Positivity Rate","Number of patients hospitalized with COVID-19":"Hospitalized","Number of patients in ICU due to COVID-19":"In ICU",
    "Total tests completed in the last day":"Total Tests"}, inplace= True)


#Add Column Calculations
daily_cases["Total New Cases"] = daily_cases["Total Cases"] - daily_cases["Total Cases"].shift()
#Get Increase/Decrease from Previous Day
daily_cases["Increase in Cases"] = daily_cases["Total New Cases"] - (daily_cases["Total Cases"].shift()-daily_cases["Total Cases"].shift(2))

#Calculate 7 Day Avg
daily_cases["Seven Day Average"] = daily_cases["Total New Cases"].rolling(7).mean()
#Get Increase / Decrease from Previous Day
daily_cases["Increase in Seven Day Average"] = daily_cases["Seven Day Average"] - daily_cases["Seven Day Average"].shift()

#Calculate Total Active Cases
daily_cases["Total Active"] = daily_cases["Total Cases"] - daily_cases["Resolved"]
#Get Increase / Decrease from Previous Day
daily_cases["Increase in Active Cases"] = daily_cases["Total Active"] - daily_cases["Total Active"].shift()
#Total Active Per 100k
daily_cases["Active Per 100k"] = (daily_cases["Total Active"]/ontario_population)*100000

#Get Increase / Decrease in Positivity Rate from Previous Day
daily_cases["Increase in Positivity"] = daily_cases["Positivity Rate"] - daily_cases["Positivity Rate"].shift()
daily_cases["Increase in Positivity"] = daily_cases["Increase in Positivity"].round(0)

#Calculate New Deaths as Well as Previous Day New Deaths to Get the Difference
daily_cases["Total New Deaths"] = daily_cases["Deaths"] - daily_cases["Deaths"].shift()
daily_cases["Seven Day Average Deaths"] = daily_cases["Total New Deaths"].rolling(7).mean()

#Get Increase/Decrease from Previous Day
daily_cases["Increase in Deaths"] = daily_cases["Total New Deaths"] - (daily_cases["Total New Deaths"].shift()-daily_cases["Total New Deaths"].shift(2))

#As of Dec 30, the Science Advisory Table Suggests Only 1/8 Cases are Being Reported. Add an Approximate Case Count From That
daily_cases["Approximate Cases"] = daily_cases["Total New Cases"] * 8

#Seven Day Average Hospitalizations & ICU
daily_cases["Seven Day Average Hospitalizations"] = daily_cases["Hospitalized"].rolling(7).mean()
daily_cases["Seven Day Average ICU"] = daily_cases["In ICU"].rolling(7).mean()


#Add Column to Report Positivity Rate and Increase as String
daily_cases["Positivity Reporting"] = daily_cases["Positivity Rate"].astype(str) + "%"
daily_cases["Increase in Positivity Reporting"] = daily_cases["Increase in Positivity"].astype(str)+"%"

#Replace NaN Values With 0
daily_cases = daily_cases.fillna(0)


#Import Cases by Vaccination Status 
vaccination_case_status_data = 'https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/eed63cf2-83dd-4598-b337-b288c0a89a16/download/cases_by_vac_status.csv'
vaccination_case_status_cols = ["Date","covid19_cases_unvac","covid19_cases_partial_vac","covid19_cases_full_vac","covid19_cases_vac_unknown","cases_unvac_rate_per100K","cases_partial_vac_rate_per100K",
    "cases_full_vac_rate_per100K","cases_unvac_rate_7ma","cases_partial_vac_rate_7ma","cases_full_vac_rate_7ma"]

vaccination_cases = import_data(vaccination_case_status_data,"Date",vaccination_case_status_cols)

#Rename Columns
vaccination_cases.rename(columns={"Date":"Reported Date","covid19_cases_unvac":"Total Unvaccinated Cases","covid19_cases_partial_vac":"Total Partial Vaccinated Cases","covid19_cases_full_vac":"Total Full Vaccinated Cases",
    "covid19_cases_vac_unknown":"Total Unkown Vaccine Status Cases","cases_unvac_rate_per100K":"Unvaccinated Rate Per 100k","cases_partial_vac_rate_per100K":"Partial Vaccination Rate Per 100k","cases_full_vac_rate_per100K":"Full Vaccination Rate Per 100k",
    "cases_unvac_rate_7ma":"Unvaccinated 7 Day Avg","cases_partial_vac_rate_7ma":"Partial Vaccination 7 Day Avg","cases_full_vac_rate_7ma":"Full Vaccination 7 Day Avg"},inplace=True)


#Get Hospitalizations by Vaccination Status
hospitalizations_data = 'https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/274b819c-5d69-4539-a4db-f2950794138c/download/vac_status_hosp_icu.csv'
hospitalizations_cols = ["date","icu_unvac","icu_partial_vac","icu_full_vac","hospitalnonicu_unvac","hospitalnonicu_partial_vac","hospitalnonicu_full_vac"]
hospitalizations = import_data(hospitalizations_data,"date",hospitalizations_cols)
hospitalizations = hospitalizations[(hospitalizations["date"]== hospitalizations["date"].max())]
hospitalizations.rename(columns={"date":"Reported Date"},inplace=True)

#Detailed Info on Confirmed Positive Cases in Ontario
covid_details = 'https://data.ontario.ca/dataset/f4112442-bdc8-45d2-be3c-12efae72fb27/resource/455fd63b-603d-4608-8216-7d8647f43350/download/conposcovidloc.csv'
covid_details_columns = ["Case_Reported_Date","Reporting_PHU_City","Age_Group","Client_Gender","Case_AcquisitionInfo","Outcome1","Reporting_PHU_Latitude","Reporting_PHU_Longitude","Row_ID"]
daily_details = import_large_data(covid_details,"Case_Reported_Date",covid_details_columns)
daily_details.rename(columns={"Case_Reported_Date":"Reported Date","Reporting_PHU_City":"City","Age_Group":"Age Group","Client_Gender":"Gender","Outcome1":"Outcome","Case_AcquisitionInfo":"Acquisition Type"}, inplace=True)

#Create a View for Acquisition of Confirmed Cases
acquisition = daily_details.copy()
acquisition = acquisition[["Reported Date","Acquisition Type","Row_ID"]]

age_groups = daily_details.copy()
age_groups = age_groups[["Age Group","Row_ID"]]

gender_groups = daily_details.copy()
gender_groups = gender_groups[["Gender","Row_ID"]]

#Get a Count of Total and Calculate Percentage of Total
def percentage_of_total(df,grouping,count):
    df = df.groupby([grouping])[count].count().reset_index(name="count")
    df["Percent of Total"] = (df["count"] / df["count"].sum()) * 100
    df["Percent of Total"] = df["Percent of Total"].round(2).astype(str) + "%"
    df = df.sort_values(by="count", ascending=True)
    return df


#Format Acquisition Labels to be More Readable
def cond_format(df,column,original,new):
    df.loc[df[column]== original,column]= new
    return df

cond_format(acquisition,"Acquisition Type","CC","Close Contact")
cond_format(acquisition,"Acquisition Type","OB","Outbreak")
cond_format(acquisition,"Acquisition Type","NO KNOWN EPI LINK","Community Spread")
cond_format(acquisition,"Acquisition Type","MISSING INFORMATION","Missing Information")
cond_format(acquisition,"Acquisition Type","TRAVEL","Travel")

#Exclude Missing Information as it Skews Charts
acquisition = acquisition.loc[(acquisition["Acquisition Type"]!= "Missing Information")]

#Get a Count of Total and Calculate Percentage of Total
def percentage_of_total(df,grouping,count):
    df = df.groupby([grouping])[count].count().reset_index(name="count")
    df["Percent of Total"] = (df["count"] / df["count"].sum()) * 100
    df["Percent of Total"] = df["Percent of Total"].round(2).astype(str) + "%"
    df = df.sort_values(by="count", ascending=True)
    return df

acquisition = percentage_of_total(acquisition,"Acquisition Type","Row_ID")
age_groups = percentage_of_total(age_groups,"Age Group","Row_ID") 
gender_groups = percentage_of_total(gender_groups,"Gender","Row_ID")
gender_groups["Gender"] = gender_groups["Gender"].str.title() #Title Case Gender


#Daily Stats on Vaccines
vaccine_link = 'https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/8a89caa9-511c-4568-af89-7f2174b4378c/download/vaccine_doses.csv'
vaccine_cols = ["report_date","previous_day_total_doses_administered","previous_day_at_least_one","previous_day_fully_vaccinated","total_doses_administered","total_individuals_at_least_one","total_individuals_partially_vaccinated",
    	"total_doses_in_fully_vaccinated_individuals","total_individuals_fully_vaccinated","total_individuals_3doses"]
vaccines = import_data(vaccine_link,"report_date",vaccine_cols)
vaccines.rename(columns={"report_date":"Reported Date","total_individuals_at_least_one":"At Least One Dose","total_individuals_fully_vaccinated":"Double Vaccinated","total_individuals_3doses":"Triple Vaccinated",
    "total_individuals_partially_vaccinated":"Partially Vaccinated"}, inplace=True)



#Get the Most Recent Case Data to Show as an Overview
latest_data = daily_cases.copy()
latest_data = latest_data[(latest_data["Reported Date"]== latest_data["Reported Date"].max())]


#Create a Dataframe and Views for Cases by Vaccination Status
#Replace NA Values With 0
vaccination_cases = vaccination_cases.fillna(0)

#Get Latest Data
latest_vaccination_cases = vaccination_cases.copy()
latest_vaccination_cases = latest_vaccination_cases[(latest_vaccination_cases["Reported Date"]== latest_vaccination_cases["Reported Date"].max())]

#Create a Function That Makes a String Column Showing Percentage of Cases by Vaccination Status
latest_vaccination_cases["Total Cases"] = latest_vaccination_cases["Total Unvaccinated Cases"] + latest_vaccination_cases["Total Partial Vaccinated Cases"] + latest_vaccination_cases["Total Full Vaccinated Cases"] + latest_vaccination_cases["Total Unkown Vaccine Status Cases"]

def get_percentage(df,name,numerator):
    df[name] = (df[numerator] / df["Total Cases"]) * 100
    df[name] = df[name].round(0)
    df[name +" Reporting"] = df[name].astype(str) + "%" #Column to add a string value to report on
    return df[name]

percent_unvaccinated = get_percentage(latest_vaccination_cases,"Percent Unvaccinated","Total Unvaccinated Cases")
percent_fully_vaccinated = get_percentage(latest_vaccination_cases,"Percent Fully Vaccinated","Total Full Vaccinated Cases")
percent_partially_vaccinated = get_percentage(latest_vaccination_cases,"Percent Partial Vaccinated","Total Partial Vaccinated Cases")
percent_unknown = get_percentage(latest_vaccination_cases,"Percent Unknown","Total Unkown Vaccine Status Cases")


#Format Data on Vaccine Distribution
vaccine_info = vaccines.copy()
vaccine_info["Unvaccinated"] = eligible_for_vaccines - vaccine_info["At Least One Dose"]


#Create a Function to Divide Total Vaccines by 1mm and Display as a String and Keep Original Column in Place
def show_millions(df,name):
    df[name+" Reporting"] = df[name] / 1000000
    df[name+" Reporting"] = df[name+" Reporting"].round(2)
    df[name+" Reporting"] = df[name+" Reporting"].astype(str) + " Million"
    return df[name]

#Create a Reporting Column for Total Individuals Vaccinated
vaccine_info["Total Double Vaccinated"] = show_millions(vaccine_info,"Double Vaccinated")
vaccine_info["Total Partially Vaccinated"] = show_millions(vaccine_info,"Partially Vaccinated")
vaccine_info["Total Triple Vaccinated"] = show_millions(vaccine_info,"Triple Vaccinated")
vaccine_info["At Least One Dose"] = show_millions(vaccine_info,"At Least One Dose")

#Hospitalizations Per 100k
#Merge Vaccines and Hospitalizations
hospital_and_vaccines = vaccine_info.merge(hospitalizations, how='inner', on='Reported Date')

#Create a Function to Calculate Hospitalization by Vaccine Status per 100k
def hospitalization_by_status_per_100k(colname,df,numerator,denominator):
    df[colname] = (df[numerator] / df[denominator]) * 100000
    df[colname] = df[colname].round(2)
    return df[colname]

unvaxxed_hospitalized_per100 = hospitalization_by_status_per_100k(
    "Not Vaccinated Hospitalized Per 100k",hospital_and_vaccines,"hospitalnonicu_unvac","Unvaccinated")

full_vax_hospitalized_per100 = hospitalization_by_status_per_100k(
    "Fully Vaccinated Hospitalized Per 100k",hospital_and_vaccines,"hospitalnonicu_full_vac","Double Vaccinated")

partial_vax_hospitalized_per100 = hospitalization_by_status_per_100k(
    "Partially Vaccinated Hospitalized Per 100k",hospital_and_vaccines,"hospitalnonicu_partial_vac","Total Partially Vaccinated")

unvaxxed_icu_per100 = hospitalization_by_status_per_100k(
    "Not Vaccinated ICU Per 100k",hospital_and_vaccines,"icu_unvac","Unvaccinated")

full_vax_icu_per100 = hospitalization_by_status_per_100k(
    "Fully Vaccinated ICU Per 100k",hospital_and_vaccines,"icu_full_vac","Double Vaccinated")

partial_vax_icu_per100 = hospitalization_by_status_per_100k(
    "Partially Vaccinated ICU Per 100k",hospital_and_vaccines,"icu_partial_vac","Total Partially Vaccinated")


#Overview on Vaccinations
latest_vaccines = vaccine_info.copy()
latest_vaccines = latest_vaccines[(latest_vaccines["Reported Date"] == latest_vaccines["Reported Date"].max())]


#Infographic Content
#Title and Blurb
ontario_covid_data = 'https://data.ontario.ca/dataset/status-of-covid-19-cases-in-ontario'
ontario_dashboard = 'https://covid19-sciencetable.ca/ontario-dashboard'

st.title("Status of COVID-19 Cases in Ontario")
st.caption("This application shows the current status of covid-19 cases in Ontario \
    and aims to provide some insights from the data. \
    Data is collected from the Ontario Government website which can be found [here](%s).\
    This application is for information purposes only, and is not in any way, shape, or form an authoritative source."% ontario_covid_data)

st.caption("For an in-depth look into COVID-19 in Ontario, head over to the Science Tables [Ontario Dashboard](%s)"% ontario_dashboard)

#Current Overview in Ontario (Cases, Hospitalizations, ICU Admission, Deaths)
# Declare Formatting Variables for Current Day Overview
latest_date = daily_cases["Reported Date"].iloc[-1].strftime("%A %B %d")
latest_cases = int(daily_cases["Total New Cases"].iloc[-1])
latest_increase = int(daily_cases["Increase in Cases"].iloc[-1])
active_cases_per_100k = int(daily_cases["Active Per 100k"].iloc[-1])
latest_hospitalization = int(daily_cases["Hospitalized"].iloc[-1])
latest_icu = int(daily_cases["In ICU"].iloc[-1])
latest_deaths = int(daily_cases["Total New Deaths"].iloc[-1])


#Create a Function that Determines an Increase or Decrease of a Metric
def increase_decrease(col):
    if col >0:
        message = "+"
    else: 
        message = ""
    return message

#Create a Function that Returns an Emoji Based on Active Cases Per 100k
def emoji_react():
    if active_cases_per_100k > 1000:
       reaction= ":dizzy_face:"
    elif active_cases_per_100k > 500:
        reaction=":exploding_head:"
    elif active_cases_per_100k > 200:
        reaction=":pensive:"
    elif active_cases_per_100k > 100:
        reaction=":upside_down_face:"
    elif active_cases_per_100k > 50:
        reaction=":unamused:"
    elif active_cases_per_100k > 25:
        reaction=":confused:"
    elif active_cases_per_100k > 10:
        reaction=":slightly_frowning_face:"
    elif active_cases_per_100k <= 10:
        reaction=":slightly_smiling_face:"
    return reaction


with st.expander("Current Overview in Ontario (New Cases, Active Cases, Acquisition, Deaths, Hospitalizations, and ICU Admission)"):
    st.subheader("Overview")
    st.caption(f"As of {latest_date}, Ontario is reporting **{latest_cases}*** new cases of COVID-19 ({increase_decrease(latest_increase)}{latest_increase} from previous day) and **{latest_deaths}** deaths.\
        Based on the latest information available, there are roughly **{int(active_cases_per_100k)}*** active cases per 100,000 residents **{emoji_react()}**.\
        During this same period, there are now **{latest_hospitalization}** hospitalizations and **{latest_icu}** patients in intensive care units.     ")
         
    st.caption("Below is a view on the progression of these cases:")

    active_cases_trend = px.area(daily_cases,
        x="Reported Date",
        y="Seven Day Average",
        color_discrete_sequence=["#fc7e00"],
        labels={"Reported Date":""},
        width=500,
        height=400,
        title="Seven Day Average of New Cases (All-Time)"
        )

    hospitalization_trend = px.line(daily_cases,
        x="Reported Date",
        y=["Seven Day Average Hospitalizations","Seven Day Average ICU"],
        color_discrete_sequence=["#4287f5","#9fbded"],
        labels={"Reported Date":"","value":"Seven Day Average","variable":"Measure Name"},
        width=500,
        height=400,
        title="Seven Day Average of Hospitalizations and ICU Admission (All-Time)"
        )
    hospitalization_trend.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor="whitesmoke",
        bordercolor="Black",
        borderwidth=1))

    
    death_trend = px.area(daily_cases,
    x="Reported Date",
    y="Seven Day Average Deaths",
    color_discrete_sequence=["#000000"],
    labels={"Reported Date":"","Seven Day Average Deaths":"Seven Day Average"},
    width=500,
    height=400,
    title="Seven Day Average of Deaths (All-Time)"
    )


    overview_chart1,overview_chart2,overview_chart3= st.columns(3)
    overview_chart1.plotly_chart(active_cases_trend, use_container_width=True)
    overview_chart2.plotly_chart(hospitalization_trend, use_container_width=True)
    overview_chart3.plotly_chart(death_trend, use_containter_width=True)

    st.caption("To get a better understanding of **how** and **where** COVID-19 is spreading, you'll find a breakdown below:")

    acquisition_breakdown = px.bar(acquisition,
    x="count", y="Acquisition Type",
    color_discrete_sequence=["#fc7e00"],
    labels={"Acquisition Type":"","Total":"Total Cases"},
    text="Percent of Total",
    orientation="h",
    width = 550,
    height=450,
    title="Percentage of Confirmed Cases by Acquisition Type"
    )
    acquisition_breakdown.update_layout(xaxis={'visible': False, 'showticklabels': False})

    age_breakdown = px.bar(age_groups,
    x="count", y="Age Group",
    color_discrete_sequence=["#fc7e00"],
    labels={"Age Group":"","Total":"Total Cases"},
    text="Percent of Total",
    orientation="h",
    width = 550,
    height=450,
    title="Percentage of Confirmed Cases by Age Group"
    )
    age_breakdown.update_layout(xaxis={'visible': False, 'showticklabels': False})  

    gender_breakdown = px.bar(gender_groups,
    x="count", y="Gender",
    color_discrete_sequence=["#fc7e00"],
    labels={"Gender":"","Total":"Total Cases"},
    text="Percent of Total",
    orientation="h",
    width = 550,
    height=450,
    title="Percentage of Confirmed Cases by Gender"
    )
    gender_breakdown.update_layout(xaxis={'visible': False, 'showticklabels': False})  
    
    overview_chart4,overview_chart5,overview_chart6 = st.columns(3)

    overview_chart4.plotly_chart(acquisition_breakdown,use_container_width=True)
    overview_chart5.plotly_chart(age_breakdown,use_container_width=True)
    overview_chart6.plotly_chart(gender_breakdown,use_container_width=True)

    #Add Caveats
    st.caption("*****")
    st.caption("'*' Ontario has drastically reduced the ability to get tested. New case counts are **not** an accurate representation.")



with st.expander("Current Overview on Vaccines (Distribution, Cases, and Hospitalizations)"):
    #Current Overview on Vaccinations
    full_to_unvax_hospital_likelihood = int(unvaxxed_hospitalized_per100 / full_vax_hospitalized_per100)
    full_to_unvax_icu_likelihood = int(unvaxxed_icu_per100 / full_vax_icu_per100)
    partial_to_unvax_hospital_likelihood = int(unvaxxed_hospitalized_per100 / partial_vax_hospitalized_per100)
    partial_to_unvax_icu_likelihood = int(unvaxxed_icu_per100 / partial_vax_icu_per100)


    cases_in_unknown = str(latest_vaccination_cases["Percent Unknown Reporting"].iloc[-1])

    st.caption("Based on the latest data provided by Ontario, here is a breakdown of how we are progressing with vaccine distribution:")
    
    one_dose,two_doses,three_doses = st.columns(3)
    one_dose.metric("At Least One Dose",str(latest_vaccines["At Least One Dose Reporting"].iloc[-1]))
    two_doses.metric("Total Double Vaccinated",str(latest_vaccines["Double Vaccinated Reporting"].iloc[-1]))
    three_doses.metric("Total Triple Vaccinated",str(latest_vaccines["Triple Vaccinated Reporting"].iloc[-1]))

    st.caption("") # Blank space
    st.caption("") # Blank space

    st.caption(f"When looking at the most recent cases, below you'll find a breakdown of cases by vaccination status:")

    percent_cases = []


    partial_vax,full_vax,no_vax,unknown = st.columns(4)
    partial_vax.metric("At Least One Dose",str(latest_vaccination_cases["Percent Partial Vaccinated Reporting"].iloc[-1]))
    full_vax.metric("At Least Two Doses",str(latest_vaccination_cases["Percent Fully Vaccinated Reporting"].iloc[-1]))
    no_vax.metric("Not Vaccinated",str(latest_vaccination_cases["Percent Unvaccinated Reporting"].iloc[-1]))
    st.caption(f"*Note that roughly **~{cases_in_unknown}** cases were reported in residents with an unknown vaccination status*")
    st.caption("")
    st.caption("Below, you'll find a breakdown of hospitalizations and ICU admissions by vaccination status per 100k residents. I have also included some insights on these charts below them:")

    hospital_comparison = px.bar(
    hospital_and_vaccines,
    x='variable',
    y=["Fully Vaccinated Hospitalized Per 100k","Partially Vaccinated Hospitalized Per 100k","Not Vaccinated Hospitalized Per 100k"],
    color_discrete_sequence=["#0077ff","#8fdbff","#ff5500"],
    labels={"value":"Hospitalized Per 100k","variable":""},
    text='value',
    width=500,
    height=500,
    title="Hospital Admissions Per 100k by Vaccination Status**"   
    )
    hospital_comparison.update_layout(xaxis={'visible': False, 'showticklabels': False})
    # hospital_comparison.update_layout(showlegend=False)
    hospital_comparison.update_traces(textposition='outside',textfont_size=12)

    icu_comparison = px.bar(
    hospital_and_vaccines,
    x='variable',
    y=["Fully Vaccinated ICU Per 100k","Partially Vaccinated ICU Per 100k","Not Vaccinated ICU Per 100k"],
    color_discrete_sequence=["#0077ff","#8fdbff","#ff5500"],
    labels={"value":"ICU Per 100k","variable":""},
    text='value',
    width=500,
    height=500,
    title="ICU Admissions Per 100k by Vaccination Status**"
    )
    icu_comparison.update_layout(xaxis={'visible': False, 'showticklabels': False})
    icu_comparison.update_traces(textposition='outside',textfont_size=12)

    hospital_chart1,hospital_chart2 = st.columns(2)
    hospital_chart1.plotly_chart(hospital_comparison, use_container_width=True)
    hospital_chart2.plotly_chart(icu_comparison, use_container_width=True)

    st.caption(f"When taking this all into consideration, these charts are telling us that you are roughly **{full_to_unvax_hospital_likelihood}x** more likely to end up in the hospital with COVID-19 if you are not vaccinated compared to someone with at least 2 doses \
        and **~{partial_to_unvax_hospital_likelihood}x** more likely compared to someone with at least 1 dose. Similarly, you are **~{full_to_unvax_icu_likelihood}x** more likely to end up in the ICU with COVID-19 if you \
        are not vaccinated compared to someone with at least 2 doses and **~{partial_to_unvax_icu_likelihood}x** more likely compared to someone with at least 1 dose.**")



    #Add Caveats
    st.caption("*****")
    stats_can = 'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901'
    st.caption("'**' Rates Per 100k are an approximation based off Q4 2021 information taken from Stats Canada. Info can be found [here](%s)."%stats_can)



## #About me
with st.expander("About Me (Plus Contact Info)"):
    linkedin = 'https://www.linkedin.com/in/jamesmwatkins/'
    email ='mailto:jameswatkins@live.com?subject=Your%20Cool%20Streamlit%20Dashboard!'

    script_dir = os.path.dirname(os.path.abspath(__file__))
    im = Image.open(os.path.join(script_dir, 'Me.JPG'))

    st.subheader("The TLDR About Me")
    st.image(im, caption=None, width=225, use_column_width=None, clamp=False, channels="RGB", output_format="auto")
    st.caption("Hey! I'm James. I'm strategic thinker with a knack for visualizing and tackling data driven problems.\
                Currently, I lead a really great team of Data Analysts at RBC in Toronto.")
    st.caption("When I am not working, I love hanging out with my\
                partner and two cats, lifting weights, kickboxing (Muay Thai), and eating all the great food Toronto restaurants have to offer.")
    st.caption("Over the winter break, I wanted to brush up on some Python and try out Streamlit.\
                There are a million reports out there that show the breakdown of COVID-19, and while I didnt plan on re-inventing the wheel,\
                I though it would be cool to try and consolidate a lot of different information into one view.")
    st.caption("I am not sure how frequent I will iterate on this, though I am open to any feedback or suggestions!")
    st.caption("Feel free to reach out via [email](%s)"% email)
    st.caption("Or drop me a connection on [LinkedIn](%s)"% linkedin)

