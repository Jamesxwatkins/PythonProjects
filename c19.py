import pandas as pd
import streamlit as st
from pandas.core.indexes.datetimelike import DatetimeTimedeltaMixin
import datetime
import plotly.express as px

# create a function that reads in a csv, selects relevant columns, formats a date, and then sorts by that date
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
covid_status_columns = ["Reported Date","Total Cases","Percent positive tests in last day","Resolved","Deaths"]
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
    "Seven Day Average","Increase in Seven Day Average","Total Active","Increase in Active Cases","Total New Deaths","Increase in Deaths"]]

daily_cases.rename(columns={"Percent positive tests in last day":"Positivity Rate"}, inplace= True)

#Create heading for Streamlit App
st.title("Status of COVID-19 Cases in Ontario")
st.caption("This application shows the current status of covid-19 cases in Ontario. \
    Data is collected from the Ontario Government website which can be found here: \
     https://data.ontario.ca/dataset/status-of-covid-19-cases-in-ontario. This application is for information purposes only.")

#Get the Most Recent Data to Show as an Overview
latest_data = daily_cases[(daily_cases["Reported Date"]== daily_cases["Reported Date"].max())]
st.header("Current Snapshot for "+str(latest_data["Reported Date"].max()))

#Add Columns and Display KPI's. **Note: Deltas are inversed as in this case, an increase is bad.**
kpicol1,kpicol2,kpicol3,kpicol4 = st.columns(4)
kpicol1.metric("Total Active Cases",int(latest_data["Total Active"]),int(latest_data["Increase in Active Cases"]), delta_color="inverse")
kpicol2.metric("Total New Cases",int(latest_data["Total New Cases"]),int(latest_data["Increase in Cases"]),delta_color="inverse")
kpicol3.metric("Positivity Rate %",latest_data["Positivity Rate"],int(latest_data["Increase in Positivity"]),delta_color="inverse")
kpicol4.metric("Seven Day Average",int(latest_data["Seven Day Average"]),int(latest_data["Increase in Seven Day Average"]),delta_color="inverse")

#Create a Dataframe to Plot All-Time Daily Stats
st.header("Daily Trends")
daily_cases_trend = daily_cases[["Reported Date","Total New Cases","Seven Day Average"]]

#Create a Date Picker to Filter the Daily Case Charts
date_vals = (daily_cases_trend["Reported Date"].min(),daily_cases_trend["Reported Date"].max())

start_date, end_date = st.slider("Select a Time Frame",value= date_vals)

mask = (daily_cases_trend["Reported Date"]>= start_date) & (daily_cases_trend["Reported Date"]<= end_date)

daily_cases_trend = daily_cases_trend.loc[mask]

#Use Plotly to Format Chart
daily_cases_trend_chart = px.line(daily_cases_trend, 
    x="Reported Date", y=["Total New Cases","Seven Day Average"],
    color_discrete_sequence=["#9c9c9c","#fc7e00"],
    labels={"Reported Date":"","value":"Total Cases","variable":"Measure Name"},
    title="Total Confirmed Cases by Day"
    )

st.plotly_chart(daily_cases_trend_chart,use_container_width=True)

#Plot Daily Deaths
#Create Dataframe for Daily Deaths
death_trending = daily_cases[["Reported Date","Total New Deaths"]]

#Add 7 Day Mean to Death Trend
death_trending["Seven Day Average"] = death_trending["Total New Deaths"].rolling(7).mean()

#Apply the Same Filtering as Daily Cases and Set Date as Index
death_trending = death_trending.loc[mask]

#Use Plotly to Format Chart
daily_death_trend_chart = px.line(death_trending, 
    x="Reported Date", y=["Total New Deaths","Seven Day Average"],
    color_discrete_sequence=["#9c9c9c","#ff0000"],
    labels={"Reported Date":"","value":"Total Deaths","variable":"Measure Name"},
    title="Total Deaths by Day"
    )

#Plot the Death Trends
st.plotly_chart(daily_death_trend_chart, use_container_width=True)
