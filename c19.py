from pandas.core.indexes.datetimelike import DatetimeTimedeltaMixin
import streamlit as st
import pandas as pd

# create a function that reads in a csv, selects relevant columns, formats a date, and then sorts by that date
def import_data(path,date_col,columns):
    df = pd.read_csv(path)
    df = df[columns]
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df = df.sort_values(by=date_col)
    return df


#Daily COVID-19 Cases in Ontario
covid_status = 'https://data.ontario.ca/dataset/f4f86e54-872d-43f8-8a86-3892fd3cb5e6/resource/ed270bb8-340b-41f9-a7c6-e8ef587e6d11/download/covidtesting.csv'
covid_status_columns = ["Reported Date","Total Cases","Percent positive tests in last day"]
daily_cases = import_data(covid_status,"Reported Date",covid_status_columns)


#Get Previous Day Total Cases to Calculate New Case
daily_cases["Previous Day Total Cases"] = daily_cases["Total Cases"].shift()

#Calculate New Cases
daily_cases['Total New Cases'] = daily_cases['Total Cases'] - daily_cases['Previous Day Total Cases']

#Calculate 7 Day Avg
daily_cases["Seven Day Average"] = daily_cases['Total New Cases'].rolling(7).mean()

#Replace NaN Values With 0
daily_cases = daily_cases.fillna(0)

#Re-Organize Columns

daily_cases = daily_cases[["Reported Date","Total New Cases","Percent positive tests in last day",
    "Seven Day Average"]]

daily_cases.rename(columns={"Percent positive tests in last day":"Positivty Rate"}, inplace= True)

#Create heading for Streamlit App
st.header("Status of COVID-19 Cases in Ontario")
st.caption("This application shows the current status of covid-19 cases in Ontario. Data is collected from the Ontario Government website and Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut venenatis vitae nunc ultricies varius. Duis non efficitur diam. Phasellus venenatis laoreet risus. Donec commodo turpis leo, ac volutpat ante finibus ut. Sed euismod congue erat at condimentum. Nunc tincidunt tincidunt bibendum. Aliquam orci lectus, iaculis vitae erat eget, laoreet accumsan neque. Pellentesque eleifend tellus eu nisl varius posuere. Proin nibh est, auctor et convallis non, malesuada faucibus massa. Ut non ultrices mi. Proin commodo, ex ut auctor maximus, libero nisi egestas augue, eu venenatis tellus turpis a elit. Aliquam a erat fermentum, egestas risus ac, finibus velit.        ")


#Get the Most Recent Data to Show as an Overview
latest_data = daily_cases[(daily_cases["Reported Date"]== daily_cases["Reported Date"].max())]

#Drop the Date Column to Show Key Metrics
latest_table = latest_data[["Total New Cases","Positivty Rate","Seven Day Average"]]

st.subheader("Current Snapshot for "+str(latest_data["Reported Date"].max()))


#Add Columns and Display KPI's
kpicol1,kpicol2,kpicol3 = st.columns(3)
kpicol1.metric("Total New Cases",int(latest_data["Total New Cases"]))
kpicol2.metric("Positivity Rate %",latest_data["Positivty Rate"])
kpicol3.metric("Seven Day Average (Cases Per Day)",int(latest_data["Seven Day Average"]))

#Create a Dataframe to Plot  All-Time Daily Cases
daily_cases_trend = daily_cases[["Reported Date","Total New Cases"]]
st.subheader("Total Cases by Day")
st.line_chart(daily_cases_trend.set_index('Reported Date'))

st.header("TEST TEST TEST")
