import pandas as pd
import streamlit as st
from pandas.core.indexes.datetimelike import DatetimeTimedeltaMixin
import datetime
import plotly.express as px
from streamlit.elements import text



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
covid_status_columns = ["Reported Date","Total Cases","Percent positive tests in last day","Resolved","Number of patients hospitalized with COVID-19","Number of patients in ICU due to COVID-19","Deaths"]
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

#Calculate New Deaths as Well as Previous Day New Deaths to Get the Difference
daily_cases["Total New Deaths"] = daily_cases["Deaths"] - daily_cases["Deaths"].shift()
#Get Increase/Decrease from Previous Day
daily_cases["Increase in Deaths"] = daily_cases["Total New Deaths"] - (daily_cases["Total New Deaths"].shift()-daily_cases["Total New Deaths"].shift(2))

#Replace NaN Values With 0
daily_cases = daily_cases.fillna(0)

#Re-Organize Columns

daily_cases = daily_cases[["Reported Date","Total New Cases","Increase in Cases","Percent positive tests in last day","Increase in Positivity",
    "Seven Day Average","Increase in Seven Day Average","Total Active","Increase in Active Cases","Number of patients hospitalized with COVID-19","Number of patients in ICU due to COVID-19","Total New Deaths","Increase in Deaths"]]

daily_cases.rename(columns={"Percent positive tests in last day":"Positivity Rate","Number of patients hospitalized with COVID-19":"Hospitalized","Number of patients in ICU due to COVID-19":"In ICU"}, inplace= True)

#Create heading for Streamlit App
st.title("Status of COVID-19 Cases in Ontario")
st.caption("This application shows the current status of covid-19 cases in Ontario. \
    Data is collected from the Ontario Government website which can be found here: \
     https://data.ontario.ca/dataset/status-of-covid-19-cases-in-ontario. This application is for information purposes only.")

#Get the Most Recent Data to Show as an Overview
latest_data = daily_cases.copy()
latest_data = latest_data[(latest_data["Reported Date"]== latest_data["Reported Date"].max())]
st.header("Current Snapshot for "+str(latest_data["Reported Date"].max()))

#Add Columns and Display KPI's. **Note: Deltas are inversed as in this case, an increase is bad.**
kpicol1,kpicol2,kpicol3,kpicol4 = st.columns(4)
kpicol1.metric("Total Active Cases",int(latest_data["Total Active"]),int(latest_data["Increase in Active Cases"]), delta_color="inverse")
kpicol2.metric("Total New Cases",int(latest_data["Total New Cases"]),int(latest_data["Increase in Cases"]),delta_color="inverse")
kpicol3.metric("Positivity Rate %",latest_data["Positivity Rate"],int(latest_data["Increase in Positivity"]),delta_color="inverse")
kpicol4.metric("Seven Day Average",int(latest_data["Seven Day Average"]),int(latest_data["Increase in Seven Day Average"]),delta_color="inverse")

#Create a Dataframe to Plot All-Time Daily Stats
st.header("Daily Trends")
daily_cases_trend = daily_cases.copy()
daily_cases_trend = daily_cases_trend[["Reported Date","Total New Cases","Seven Day Average","Hospitalized"]]

#Create a Date Picker to Filter the Daily Case Charts
date_vals = (daily_cases_trend["Reported Date"].min(),daily_cases_trend["Reported Date"].max())

start_date, end_date = st.slider("Select a Time Frame",value= date_vals)
#Add Columns to charts
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


#Detailed COVID info is a massive file.
#Re-use existing function to import data, but isolate to current month
#and Include Caching
#Temporary Idea - Limit Size to Current Month or Max Month
st.header("Detailed Breakdown of Confirmed Cases in Ontario This Month")

@st.cache
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
current_age_breakdown = current_age_breakdown.sort_values(["Percentage of Total"], ascending=[True])
current_age_breakdown = px.bar(current_age_breakdown,
     x="Percentage of Total", y="Age Group",
     color_discrete_sequence=["#fc7e00"],
     labels={"Age Group":"","Total":"Total Cases"},
     #title="Total Unresolved Cases by Age Group",
     text="Percentage of Total",
     orientation="h"
     )


#Create a Dataframe and Chart for Cases by Age Group by Day
age_trend = daily_details.copy()
# age_trend = age_trend[(age_trend['Outcome'] == "Not Resolved")] 
age_trend = age_trend[["Reported Date","Age Group","Row_ID"]]
age_trend = age_trend.groupby(["Reported Date","Age Group"])["Row_ID"].count().reset_index()\
        .rename(columns={"Row_ID":"Total"})
age_trend["Total"] = age_trend["Total"].rolling(7).mean() #Convert Total to 7 Day Mean
age_trend = px.line(age_trend,
     x="Reported Date", y="Total", 
     color='Age Group',
     labels={"Reported Date":"","Total":"7 Day Avg."}
     )


#Create Columns for Charts
detail_chart1,detail_chart2 = st.columns(2)
detail_chart1.subheader("% Total Cases by Age Group")
detail_chart1.plotly_chart(current_age_breakdown,use_container_width=True)
detail_chart2.subheader("7 Day Average of Cases by Age Group by Day")
detail_chart2.plotly_chart(age_trend,use_container_width=True)


#Create a View for Acquisition of Confirmed Cases
acquisition = daily_details.copy()
acquisition = acquisition[["Reported Date","Acquisition Type","Row_ID"]]

#Format Acquisition Labels to be More Readable
acquisition.loc[acquisition["Acquisition Type"]=="CC", 'Acquisition Type'] = "Close Contact"
acquisition.loc[acquisition["Acquisition Type"]=="OB", 'Acquisition Type'] = "Outbreak"
acquisition.loc[acquisition["Acquisition Type"]=="NO KNOWN EPI LINK", 'Acquisition Type'] = "Community Spread"
acquisition.loc[acquisition["Acquisition Type"]=="MISSING INFORMATION", 'Acquisition Type'] = "Missing Information"
acquisition.loc[acquisition["Acquisition Type"]=="TRAVEL", 'Acquisition Type'] = "Travel"
acquisition = acquisition.loc[(acquisition["Acquisition Type"]!= "Missing Information")]

#Create a Dataframe and Chart for Cases by Acquisition Type
acquisition_overview = acquisition.copy()
acquisition_overview = acquisition_overview.groupby(["Acquisition Type"])["Row_ID"].count().reset_index()\
        .rename(columns={"Row_ID":"Total"})
acquisition_overview["Percentage of Total"] = (acquisition_overview["Total"] / acquisition_overview["Total"].sum())*100
acquisition_overview["Percentage of Total"] = acquisition_overview["Percentage of Total"].round(2)
acquisition_overview = acquisition_overview.sort_values(["Percentage of Total"], ascending=[True])
acquisition_overview = px.bar(acquisition_overview,
     x="Percentage of Total", y="Acquisition Type",
     color_discrete_sequence=["#fc7e00"],
     labels={"Acquisition Type":"","Total":"Total Cases"},
     #title="Total Unresolved Cases by Age Group",
     text="Percentage of Total",
     orientation="h"
     )


#Create a Dataframe and Chart for Cases by Acquisition Type by Day
acquisition_trend = acquisition.copy()
acquisition_trend = acquisition_trend.groupby(["Reported Date","Acquisition Type"])["Row_ID"].count().reset_index()\
        .rename(columns={"Row_ID":"Total"})
acquisition_trend = px.line(acquisition_trend,
     x="Reported Date", y="Total", 
     color='Acquisition Type',
     labels={"Reported Date":"","Total":"Total Cases"}
     )


#Create Columns for Charts
detail_chart3, detail_chart4 = st.columns(2)
detail_chart3.subheader("% Total Cases by Acquisition Type*")
detail_chart3.plotly_chart(acquisition_overview,use_container_width=True)
st.caption("* Excluding Case Counts Where Acquisition Type is Missing")
detail_chart4.subheader("Total Cases by Acquisition Type by Day*")
detail_chart4.plotly_chart(acquisition_trend,use_container_width=True)




# #test expander
# with st.expander("About The Author"):
#     st.write("Testing Some Text That I'll Eventually Write About Myself")

