import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq

# Page Config
st.set_page_config(page_title="Business Intelligence Dashboard", 
                   page_icon="📊", layout="wide")

# Title
st.title("📊 Business Intelligence Dashboard")
st.markdown("### Superstore Sales Analysis")

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("Sample - Superstore.csv", encoding='latin1')
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    df['Month Name'] = df['Order Date'].dt.strftime('%B')
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("🔍 Filters")
year = st.sidebar.multiselect("Select Year", 
                               options=df['Year'].unique(), 
                               default=df['Year'].unique())
region = st.sidebar.multiselect("Select Region", 
                                 options=df['Region'].unique(), 
                                 default=df['Region'].unique())
category = st.sidebar.multiselect("Select Category", 
                                   options=df['Category'].unique(), 
                                   default=df['Category'].unique())

# Filter Data
df_filtered = df[(df['Year'].isin(year)) & 
                 (df['Region'].isin(region)) & 
                 (df['Category'].isin(category))]

# KPI Cards
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Sales", f"${df_filtered['Sales'].sum():,.0f}")
col2.metric("📈 Total Profit", f"${df_filtered['Profit'].sum():,.0f}")
col3.metric("🛒 Total Orders", f"{df_filtered['Order ID'].nunique():,}")
col4.metric("👥 Total Customers", f"{df_filtered['Customer Name'].nunique():,}")

st.markdown("---")

# Row 1 Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales by Region")
    fig = px.bar(df_filtered.groupby('Region')['Sales'].sum().reset_index(),
                 x='Region', y='Sales', color='Region')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Sales by Category")
    fig = px.pie(df_filtered.groupby('Category')['Sales'].sum().reset_index(),
                 names='Category', values='Sales')
    st.plotly_chart(fig, use_container_width=True)

# Row 2 Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Sales Trend")
    monthly = df_filtered.groupby(['Year', 'Month'])['Sales'].sum().reset_index()
    fig = px.line(monthly, x='Month', y='Sales', color='Year', markers=True)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Profit by Category")
    fig = px.bar(df_filtered.groupby('Category')['Profit'].sum().reset_index(),
                 x='Category', y='Profit', color='Category')
    st.plotly_chart(fig, use_container_width=True)

# Row 3 - Discount vs Profit
st.subheader("Discount vs Profit Analysis")
fig = px.scatter(df_filtered, x='Discount', y='Profit', 
                 color='Category', opacity=0.5,
                 title='Impact of Discount on Profit')
fig.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)

# AI Chatbot Section
st.markdown("---")
st.subheader("🤖 AI Data Analyst Chatbot")
st.markdown("Ask any question about the data in plain English!")

# Groq Client
from dotenv import load_dotenv
import os
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))  

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Data Summary for AI context
data_summary = f"""
You are a business data analyst assistant. Here is the current filtered data summary:
- Total Sales: ${df_filtered['Sales'].sum():,.0f}
- Total Profit: ${df_filtered['Profit'].sum():,.0f}
- Total Orders: {df_filtered['Order ID'].nunique():,}
- Total Customers: {df_filtered['Customer Name'].nunique():,}
- Top Region by Sales: {df_filtered.groupby('Region')['Sales'].sum().idxmax()}
- Top Category by Sales: {df_filtered.groupby('Category')['Sales'].sum().idxmax()}
- Top Category by Profit: {df_filtered.groupby('Category')['Profit'].sum().idxmax()}
- Date Range: {df_filtered['Order Date'].min().date()} to {df_filtered['Order Date'].max().date()}
Answer questions based on this data clearly and concisely.
"""

# User Input
if prompt := st.chat_input("Ask something like: Which region has highest profit?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": data_summary},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})