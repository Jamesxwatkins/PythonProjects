import pandas as pd
import streamlit as st
from pandas.core.indexes.datetimelike import DatetimeTimedeltaMixin
import datetime
import plotly.express as px
from streamlit.elements import image, text
from streamlit.proto.Image_pb2 import Image
from PIL import Image


# Create a Function That Reads in a csv, Selects Relevant Columns, Formats a Date, and Then Sorts by That Date
def import_data(path,date_col,columns):
    df = pd.read_csv(path)
    df = df[columns]
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df = df.sort_values(by=date_col)
    return df

#Set Page Size
st.set_page_config(layout="wide")

#Daily COVID-19 Cases in Ontario
covid_status = 'https://data.ontario.ca/dataset/f4f86e54-872d-43f8-8a86-3892fd3cb5e6/resource/ed270bb8-340b-41f9-a7c6-e8ef587e6d11/download/covidtesting.csv'
covid_status_columns = ["Reported Date","Total Cases","Percent positive tests in last day","Resolved","Number of patients hospitalized with COVID-19","Number of patients in ICU due to COVID-19","Deaths",\
    "Total tests completed in the last day"]
daily_cases = import_data(covid_status,"Reported Date",covid_status_columns)


#Calculate New Cases as Well as Previous Day New Cases to Get the Difference
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

#Get Increase / Decrease in Positivity Rate from Previous Day
daily_cases["Increase in Positivity"] = daily_cases["Percent positive tests in last day"] - daily_cases["Percent positive tests in last day"].shift()
daily_cases["Increase in Positivity"] = daily_cases["Increase in Positivity"].round(0)
#Calculate New Deaths as Well as Previous Day New Deaths to Get the Difference
daily_cases["Total New Deaths"] = daily_cases["Deaths"] - daily_cases["Deaths"].shift()
#Get Increase/Decrease from Previous Day
daily_cases["Increase in Deaths"] = daily_cases["Total New Deaths"] - (daily_cases["Total New Deaths"].shift()-daily_cases["Total New Deaths"].shift(2))

#As of Dec 30, the Science Advisory Table Suggests Only 1/8 Cases are Being Reported. Add an Approximate Case Count From That
daily_cases["Approximate Cases"] = daily_cases["Total New Cases"] * 8

#Add Column to Report Positivity Rate and Increase as String
daily_cases["Positivity Reporting"] = daily_cases["Percent positive tests in last day"].astype(str) + "%"
daily_cases["Increase in Positivity Reporting"] = daily_cases["Increase in Positivity"].astype(str)+"%"

#Replace NaN Values With 0
daily_cases = daily_cases.fillna(0)

#Re-Organize Columns
daily_cases = daily_cases[["Reported Date","Total New Cases","Approximate Cases","Increase in Cases","Percent positive tests in last day","Total tests completed in the last day","Increase in Positivity","Seven Day Average",
    "Increase in Seven Day Average","Total Active","Increase in Active Cases","Number of patients hospitalized with COVID-19","Number of patients in ICU due to COVID-19","Total New Deaths","Increase in Deaths",
    "Positivity Reporting","Increase in Positivity Reporting"]]

daily_cases.rename(columns={"Percent positive tests in last day":"Positivity Rate","Number of patients hospitalized with COVID-19":"Hospitalized","Number of patients in ICU due to COVID-19":"In ICU",
    "Total tests completed in the last day":"Total Tests"}, inplace= True)

#Create heading for Streamlit App
st.title("Status of COVID-19 Cases in Ontario")
st.caption("This application shows the current status of covid-19 cases in Ontario. \
    Data is collected from the Ontario Government website which can be found here: \
     https://data.ontario.ca/dataset/status-of-covid-19-cases-in-ontario. This application is for information purposes only.")

#Get the Most Recent Data to Show as an Overview
latest_data = daily_cases.copy()
latest_data = latest_data[(latest_data["Reported Date"]== latest_data["Reported Date"].max())]
st.header("Current Snapshot as of "+str(latest_data["Reported Date"].max()))

#Add Columns and Display KPI's. **Note: Deltas are inversed as in this case, an increase is bad.**
kpicol1,kpicol2,kpicol3,kpicol4 = st.columns(4)
kpicol1.metric("Total Active Cases",int(latest_data["Total Active"]),int(latest_data["Increase in Active Cases"]), delta_color="inverse")
kpicol2.metric("Total New Cases",int(latest_data["Total New Cases"]),int(latest_data["Increase in Cases"]),delta_color="inverse")
kpicol3.metric("Positivity Rate %",str(latest_data["Positivity Reporting"].iloc[-1]),str(latest_data["Increase in Positivity Reporting"].iloc[-1]),delta_color="inverse")
kpicol4.metric("Seven Day Average",int(latest_data["Seven Day Average"]),int(latest_data["Increase in Seven Day Average"]),delta_color="inverse")

#Get Latest Values for Total Cases and Approximate Cases
todays_actual_cases = int(latest_data["Total New Cases"].iloc[-1])
todays_approximate_cases = int(latest_data["Approximate Cases"].iloc[-1])

st.caption("**Note:** As of December 30th 2021, the Ontario Science Table is estimating that approximately **1 in 8 cases are being reported**. Based on todays total of **{}** cases, we may actually be seeing upwards of **~{}** cases."\
    .format(todays_actual_cases,todays_approximate_cases))

#Create a Dataframe to Plot All-Time Daily Stats
st.header("Daily Trends")
daily_cases_trend = daily_cases.copy()
daily_cases_trend = daily_cases_trend[["Reported Date","Total New Cases","Seven Day Average","Hospitalized"]]

#Create a Date Picker to Filter the Daily Case Charts
date_vals = (daily_cases_trend["Reported Date"].min(),daily_cases_trend["Reported Date"].max())

start_date, end_date = st.slider("Select a Time Frame",value= date_vals)
#Create a Mask to Filter the Dataframe by Slider Values
trendcol1,trendcol2 = st.columns(2)
mask = (daily_cases_trend["Reported Date"]>= start_date) & (daily_cases_trend["Reported Date"]<= end_date)

daily_cases_trend = daily_cases_trend.loc[mask]

#Use Plotly to Format Chart
daily_cases_trend_chart = px.line(daily_cases_trend, 
    x="Reported Date", y=["Total New Cases","Hospitalized"],
    color_discrete_sequence=["#fc7e00","#87dbff"], #Removed 7 day average - hex is "#9c9c9c"
    labels={"Reported Date":"","value":"Total Cases","variable":"Measure Name"},
    #title="Total Confirmed Cases and Hospitalized by Day"
    )

trendcol1.subheader("Total Confirmed Cases and Hospitalized by Day")
trendcol1.plotly_chart(daily_cases_trend_chart,use_container_width=True)

#Plot Daily Deaths
#Create Dataframe for Daily Deaths
death_trending = daily_cases.copy()
death_trending = death_trending[["Reported Date","Total New Deaths","In ICU"]]

#Apply the Same Filtering as Daily Cases and Set Date as Index
death_trending = death_trending.loc[mask]

#Use Plotly to Format Chart
daily_death_trend_chart = px.line(death_trending, 
    x="Reported Date", y=["Total New Deaths","In ICU"],
    color_discrete_sequence=["#ff0000","#0074a6"],
    labels={"Reported Date":"","value":"Total","variable":"Measure Name"},
    #title="Total ICU & Deaths by Day"
    )

#Plot the Death Trends
trendcol2.subheader("Total ICU & Deaths by Day")
trendcol2.plotly_chart(daily_death_trend_chart, use_container_width=True)

#Import Cases by Vaccination Status 
vaccination_case_status_data = 'https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/eed63cf2-83dd-4598-b337-b288c0a89a16/download/cases_by_vac_status.csv'
vaccination_case_status_cols = ["Date","covid19_cases_unvac","covid19_cases_partial_vac","covid19_cases_full_vac","covid19_cases_vac_unknown","cases_unvac_rate_per100K","cases_partial_vac_rate_per100K",
    "cases_full_vac_rate_per100K","cases_unvac_rate_7ma","cases_partial_vac_rate_7ma","cases_full_vac_rate_7ma"]
vaccination_cases = import_data(vaccination_case_status_data,"Date",vaccination_case_status_cols)

#Rename Columns
vaccination_cases.rename(columns={"Date":"Reported Date","covid19_cases_unvac":"Total Unvaccinated Cases","covid19_cases_partial_vac":"Total Partial Vaccinated Cases","covid19_cases_full_vac":"Total Full Vaccinated Cases",
    "covid19_cases_vac_unknown":"Total Unkown Vaccine Status Cases","cases_unvac_rate_per100K":"Unvaccinated Rate Per 100k","cases_partial_vac_rate_per100K":"Partial Vaccination Rate Per 100k","cases_full_vac_rate_per100K":"Full Vaccination Rate Per 100k",
    "cases_unvac_rate_7ma":"Unvaccinated 7 Day Avg","cases_partial_vac_rate_7ma":"Partial Vaccination 7 Day Avg","cases_full_vac_rate_7ma":"Full Vaccination 7 Day Avg"},inplace=True)

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
    df[name] = df[name].astype(str) + "%"
    return df[name]

percent_unvaccinated = get_percentage(latest_vaccination_cases,"Percent Unvaccinated","Total Unvaccinated Cases")
percent_fully_vaccinated = get_percentage(latest_vaccination_cases,"Percent Fully Vaccinated","Total Full Vaccinated Cases")
percent_partially_vaccinated = get_percentage(latest_vaccination_cases,"Percent Partial Vaccinated","Total Partial Vaccinated Cases")
percent_unknown = get_percentage(latest_vaccination_cases,"Percent Unknown","Total Unkown Vaccine Status Cases")

#Show Latest Cases by Vaccination Status
st.header("Overview by Vaccination Status as of "+str(vaccination_cases["Reported Date"].max()))

#Display Latest Cases by Vaccine Status as Metrics in a Single Frame
full_vax,partial_vax,no_vax,unknown = st.columns(4)
full_vax.metric("Percentage Fully Vaccinated",str(latest_vaccination_cases["Percent Fully Vaccinated"].iloc[-1]))
partial_vax.metric("Percentage Partially Vaccinated",str(latest_vaccination_cases["Percent Partial Vaccinated"].iloc[-1]))
no_vax.metric("Percentage Unvaccinated",str(latest_vaccination_cases["Percent Unvaccinated"].iloc[-1]))
unknown.metric("Percentage Unknown",str(latest_vaccination_cases["Percent Unknown"].iloc[-1]))

#Create a Visual of Cases Per 100k by Status
daily_vax_cases = vaccination_cases.copy()

#Create a Date Picker to Filter the Daily Vax Case Chart
vax_date_vals = (daily_vax_cases["Reported Date"].min(),daily_vax_cases["Reported Date"].max())

vaxstart_date, vaxend_date = st.slider("Select a Time Frame",value= vax_date_vals)

#Create a Mask to Filter the Dataframe by Slider Values
vaxmask = (daily_vax_cases["Reported Date"]>= vaxstart_date) & (daily_vax_cases["Reported Date"]<= vaxend_date)
daily_vax_cases = daily_vax_cases.loc[vaxmask]

daily_vax_cases = daily_vax_cases[["Reported Date","Unvaccinated Rate Per 100k","Full Vaccination Rate Per 100k","Partial Vaccination Rate Per 100k"]]
vax_cases = px.line(daily_vax_cases, 
    x="Reported Date", y=["Unvaccinated Rate Per 100k","Full Vaccination Rate Per 100k","Partial Vaccination Rate Per 100k"],
    color_discrete_sequence=["#bebfbb","#00f2b5","#87dbff"], #Removed 7 day average - hex is "#9c9c9c"
    labels={"Reported Date":"","value":"Cases Per 100k","variable":"Measure Name"}
    )

st.subheader("Daily Cases Per 100k by Vaccination Status")
st.plotly_chart(vax_cases,use_container_width=True)


#Detailed COVID info is a massive file.
#Re-use existing function to import data, but isolate to current month
#and Include Caching
#Temporary Idea - Limit Size to Current Month or Max Month
st.header("Detailed Breakdown of Confirmed Cases in Ontario This Month")

@st.experimental_memo
def import_large_data(path,date_col,columns):
    df = pd.read_csv(path)
    df = df[columns]
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df["Month"] = df[date_col] + pd.offsets.MonthEnd(0)
    df = df.sort_values(by=date_col)
    df = df.loc[(df["Month"]== df["Month"].max())]
    return df


#Detailed Info on Confirmed Positive Cases in Ontario
covid_details = 'https://data.ontario.ca/dataset/f4112442-bdc8-45d2-be3c-12efae72fb27/resource/455fd63b-603d-4608-8216-7d8647f43350/download/conposcovidloc.csv'
covid_details_columns = ["Case_Reported_Date","Reporting_PHU_City","Age_Group","Client_Gender","Case_AcquisitionInfo","Outcome1","Reporting_PHU_Latitude","Reporting_PHU_Longitude","Row_ID"]
daily_details = import_large_data(covid_details,"Case_Reported_Date",covid_details_columns)
daily_details.rename(columns={"Case_Reported_Date":"Reported Date","Reporting_PHU_City":"City","Age_Group":"Age Group","Client_Gender":"Gender","Outcome1":"Outcome","Case_AcquisitionInfo":"Acquisition Type"}, inplace=True)


#Create a Dataframe and Chart for Cases by Age Group
current_age_breakdown = daily_details.copy()
current_age_breakdown = current_age_breakdown[["Reported Date","Age Group"]]
current_age_breakdown = current_age_breakdown.groupby(["Age Group"]).count()
current_age_breakdown.rename(columns={"Reported Date":"Total"}, inplace=True)
current_age_breakdown = current_age_breakdown.reset_index()
current_age_breakdown["Percentage of Total"] = (current_age_breakdown["Total"] / current_age_breakdown["Total"].sum())*100
current_age_breakdown["Percentage of Total"] = current_age_breakdown["Percentage of Total"].round(2)
current_age_breakdown["Percentage of Total Label"] = current_age_breakdown["Percentage of Total"].astype(str) + "%"
current_age_breakdown = current_age_breakdown.sort_values(["Percentage of Total"], ascending=[True])
current_age_breakdown = px.bar(current_age_breakdown,
     x="Percentage of Total", y="Age Group",
     color_discrete_sequence=["#fc7e00"],
     labels={"Age Group":"","Total":"Total Cases"},
     #title="Total Unresolved Cases by Age Group",
     text="Percentage of Total Label",
     orientation="h"
     )


#Create a View for Acquisition of Confirmed Cases
acquisition = daily_details.copy()
acquisition = acquisition[["Reported Date","Acquisition Type","Row_ID"]]

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

#Create a Dataframe and Chart for Cases by Acquisition Type
acquisition_overview = acquisition.copy()
acquisition_overview = acquisition_overview.groupby(["Acquisition Type"])["Row_ID"].count().reset_index()\
        .rename(columns={"Row_ID":"Total"})
acquisition_overview["Percentage of Total"] = (acquisition_overview["Total"] / acquisition_overview["Total"].sum())*100
acquisition_overview["Percentage of Total"] = acquisition_overview["Percentage of Total"].round(2)
acquisition_overview["Percentage of Total Label"] = acquisition_overview["Percentage of Total"].astype(str)+"%"
acquisition_overview = acquisition_overview.sort_values(["Percentage of Total"], ascending=[True])
acquisition_overview = px.bar(acquisition_overview,
     x="Percentage of Total", y="Acquisition Type",
     color_discrete_sequence=["#fc7e00"],
     labels={"Acquisition Type":"","Total":"Total Cases"},
     #title="Total Unresolved Cases by Age Group",
     text="Percentage of Total Label",
     orientation="h"
     )


#Create Columns for Charts
detail_chart1,detail_chart2 = st.columns(2)
detail_chart1.subheader("% Total Cases by Age Group")
detail_chart1.plotly_chart(current_age_breakdown,use_container_width=True)
detail_chart2.subheader("% Total Cases by Acquisition Type*")
detail_chart2.plotly_chart(acquisition_overview,use_container_width=True)
st.caption("'*' Excluding Case Counts Where Acquisition Type is Missing")


#Overview on Vaccinations
st.header("Overall Status of Vaccinations in Ontario")

#Daily Stats on Vaccines
vaccine_link = 'https://data.ontario.ca/dataset/752ce2b7-c15a-4965-a3dc-397bf405e7cc/resource/8a89caa9-511c-4568-af89-7f2174b4378c/download/vaccine_doses.csv'
vaccine_cols = ["report_date","previous_day_total_doses_administered","previous_day_at_least_one","previous_day_fully_vaccinated","total_doses_administered","total_individuals_at_least_one","total_individuals_partially_vaccinated",
    	"total_doses_in_fully_vaccinated_individuals","total_individuals_fully_vaccinated","total_individuals_3doses"]
vaccines = import_data(vaccine_link,"report_date",vaccine_cols)
vaccines.rename(columns={"report_date":"Reported Date","total_individuals_at_least_one":"At Least One Dose","total_individuals_fully_vaccinated":"Double Vaccinated","total_individuals_3doses":"Triple Vaccinated",
    "total_individuals_partially_vaccinated":"Partially Vaccinated"}, inplace=True)
#vaccines = vaccines.fillna(0)

latest_vaccines = vaccines.copy()
latest_vaccines = latest_vaccines[(latest_vaccines["Reported Date"] == latest_vaccines["Reported Date"].max())]

st.subheader("Overview of Vaccinations in Ontario as of "+str(latest_vaccines["Reported Date"].max()))

#Create a Function to Divide Total Vaccines by 1mm and Display as a String
def show_millions(df,name):
    df[name] = df[name] / 1000000
    df[name] = df[name].round(2)
    df[name] = df[name].astype(str) + " Million"
    return df[name]

#Create a Reporting Column for Total Individuals Vaccinated
latest_vaccines["Total Double Vaccinated"] = show_millions(latest_vaccines,"Double Vaccinated")
latest_vaccines["Total Partially Vaccinated"] = show_millions(latest_vaccines,"Partially Vaccinated")
latest_vaccines["Total Triple Vaccinated"] = show_millions(latest_vaccines,"Triple Vaccinated")

#Display Vaccination Overview as Metrics
one_dose,two_doses,three_doses = st.columns(3)
one_dose.metric("Total Partially Vaccinated",str(latest_vaccines["Total Partially Vaccinated"].iloc[-1]))
two_doses.metric("Total Double Vaccinated",str(latest_vaccines["Total Double Vaccinated"].iloc[-1]))
three_doses.metric("Total Triple Vaccinated",str(latest_vaccines["Total Triple Vaccinated"].iloc[-1]))


#Show a Trend of Vaccine Distribution Over Time
vaccine_trend = px.line(vaccines, 
    x="Reported Date", y=["At Least One Dose","Double Vaccinated","Triple Vaccinated"],
    color_discrete_sequence=["#87dbff","#00f2b5","#ff8e52"], 
    labels={"Reported Date":"","value":"Total Vaccinated","variable":"Measure Name"}
    )

#Plot Daily Vaccinations
st.plotly_chart(vaccine_trend,use_container_width=True)


# #About me
image = Image.open("Me.jpeg")
linkedin = 'https://www.linkedin.com/in/jamesmwatkins/'
email ='mailto:jameswatkins@live.com?subject=Your%20Cool%20Streamlit%20Dashboard!'

st.sidebar.write("The TLDR About Me")
st.sidebar.image(image, caption=None, width=225, use_column_width=None, clamp=False, channels="RGB", output_format="auto")
st.sidebar.write("Hey! I'm James. I'm strategic thinker with a knack for visualizing and tackling data driven problems.\
            Currently, I lead a really great team of Data Analysts at RBC in Toronto.")
st.sidebar.write("When I am not working, I love hanging out with my\
            partner and two cats, lifting weights, kickboxing (Muay Thai), and eating all the great food Toronto restaurants have to offer.")
st.sidebar.write("Over the winter break, I wanted to brush up on some Python and try out Streamlit.\
            There are a million reports out there that show the breakdown of COVID-19, and while I didnt plan on re-inventing the wheel,\
            I though it would be cool to try and consolidate a lot of different information into one view.")
st.sidebar.write("I am not sure how frequent I will iterate on this, though I am open to any feedback or suggestions!")
st.sidebar.write("Feel free to reach out via [email](%s)"% email)
st.sidebar.write("Or drop me a connection on [LinkedIn](%s)"% linkedin)

