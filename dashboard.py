import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from groq import Groq
# Initialize Groq Client (place this right after imports)
from dotenv import load_dotenv
import os
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Page Config
st.set_page_config(page_title="Business Intelligence Dashboard", 
                   page_icon="📊", layout="wide")

# Title
st.title("📊 Business Intelligence Dashboard")
st.markdown("### Superstore Sales Analysis")

# Load Data
@st.cache_data
def load_data():
    conn = sqlite3.connect('superstore.db')
    df = pd.read_sql("""
        SELECT *,
               strftime('%Y', [Order Date]) as Year_Str,
               strftime('%m', [Order Date]) as Month_Str
        FROM sales
    """, conn)
    conn.close()
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    df['Month Name'] = df['Order Date'].dt.strftime('%B')
    df = df.drop(columns=['Year_Str', 'Month_Str'], errors='ignore')
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

# SQL Query Explorer
st.markdown("---")
st.subheader("🔍 SQL Query Explorer")
st.markdown("Write your own SQL queries to explore the data!")

default_query = """SELECT Region, 
       ROUND(SUM(Sales), 2) as Total_Sales,
       ROUND(SUM(Profit), 2) as Total_Profit,
       COUNT(*) as Total_Orders
FROM sales
GROUP BY Region
ORDER BY Total_Sales DESC"""

user_query = st.text_area("Write SQL Query:", value=default_query, height=150)

if st.button("▶️ Run Query"):
    try:
        conn = sqlite3.connect('superstore.db')
        result = pd.read_sql(user_query, conn)
        conn.close()
        st.success(f"✅ Query returned {len(result)} rows")
        st.dataframe(result, use_container_width=True)

        # Download results as CSV
        csv = result.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"❌ SQL Error: {str(e)}")

        
# KPI Alerts Section
st.markdown("---")
st.subheader("🚨 KPI Alerts & Warnings")

def generate_alerts(df):
    alerts = []
    
    # Profit margin alert
    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    profit_margin = (total_profit / total_sales) * 100
    
    if profit_margin < 10:
        alerts.append(("🔴 CRITICAL", f"Profit margin is {profit_margin:.1f}% — critically low! Target is 15%+"))
    elif profit_margin < 15:
        alerts.append(("🟡 WARNING", f"Profit margin is {profit_margin:.1f}% — below target of 15%"))
    else:
        alerts.append(("🟢 HEALTHY", f"Profit margin is {profit_margin:.1f}% — on track!"))

    # Discount alert
    high_discount_orders = df[df['Discount'] > 0.3]
    high_discount_pct = (len(high_discount_orders) / len(df)) * 100
    high_discount_loss = high_discount_orders['Profit'].sum()
    
    if high_discount_pct > 30:
        alerts.append(("🔴 CRITICAL", f"{high_discount_pct:.1f}% of orders have discount above 30% — causing ${abs(high_discount_loss):,.0f} in losses!"))
    elif high_discount_pct > 15:
        alerts.append(("🟡 WARNING", f"{high_discount_pct:.1f}% of orders have discount above 30% — review discount policy"))
    else:
        alerts.append(("🟢 HEALTHY", f"Only {high_discount_pct:.1f}% of orders have excessive discounts — good control!"))

    # Region gap alert
    region_sales = df.groupby('Region')['Sales'].sum()
    top_region = region_sales.idxmax()
    low_region = region_sales.idxmin()
    gap_pct = ((region_sales.max() - region_sales.min()) / region_sales.max()) * 100
    
    if gap_pct > 50:
        alerts.append(("🔴 CRITICAL", f"Huge sales gap! {top_region} (${region_sales.max():,.0f}) vs {low_region} (${region_sales.min():,.0f}) — {gap_pct:.0f}% gap!"))
    elif gap_pct > 30:
        alerts.append(("🟡 WARNING", f"Sales gap between {top_region} and {low_region} is {gap_pct:.0f}% — needs attention"))
    else:
        alerts.append(("🟢 HEALTHY", f"Regional sales are balanced — gap is only {gap_pct:.0f}%"))

    # Furniture profit alert
    category_profit = df.groupby('Category')['Profit'].sum()
    category_sales = df.groupby('Category')['Sales'].sum()
    
    for cat in category_profit.index:
        cat_margin = (category_profit[cat] / category_sales[cat]) * 100
        if cat_margin < 5:
            alerts.append(("🔴 CRITICAL", f"{cat} profit margin is only {cat_margin:.1f}% — immediate pricing review needed!"))
        elif cat_margin < 10:
            alerts.append(("🟡 WARNING", f"{cat} profit margin is {cat_margin:.1f}% — below healthy threshold of 10%"))

    # Orders growth alert
    yearly_orders = df.groupby('Year')['Order ID'].nunique()
    if len(yearly_orders) >= 2:
        years = sorted(yearly_orders.index)
        growth = ((yearly_orders[years[-1]] - yearly_orders[years[-2]]) / yearly_orders[years[-2]]) * 100
        if growth < 0:
            alerts.append(("🔴 CRITICAL", f"Order count dropped {abs(growth):.1f}% vs last year — investigate immediately!"))
        elif growth < 5:
            alerts.append(("🟡 WARNING", f"Order growth is only {growth:.1f}% vs last year — needs boost"))
        else:
            alerts.append(("🟢 HEALTHY", f"Orders grew {growth:.1f}% vs last year — great momentum!"))

    return alerts

alerts = generate_alerts(df_filtered)

for status, message in alerts:
    if "🔴" in status:
        st.error(f"{status}: {message}")
    elif "🟡" in status:
        st.warning(f"{status}: {message}")
    else:
        st.success(f"{status}: {message}")


# PDF Report Export Section
st.markdown("---")
st.subheader("📄 Export Business Report")

from fpdf import FPDF
import tempfile

def generate_pdf_report(df):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'Business Intelligence Report', ln=True, align='C')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 8, f'Generated on: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(5)

    # KPI Section
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, '  Key Performance Indicators', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    total_orders = df['Order ID'].nunique()
    total_customers = df['Customer Name'].nunique()
    profit_margin = (total_profit / total_sales) * 100

    pdf.set_font('Helvetica', '', 11)
    kpis = [
        ('Total Sales', f'${total_sales:,.0f}'),
        ('Total Profit', f'${total_profit:,.0f}'),
        ('Profit Margin', f'{profit_margin:.1f}%'),
        ('Total Orders', f'{total_orders:,}'),
        ('Total Customers', f'{total_customers:,}'),
    ]
    for label, value in kpis:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(80, 8, f'  {label}:', ln=False)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, value, ln=True)
    pdf.ln(5)

    # Regional Performance
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, '  Regional Performance', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    region_data = df.groupby('Region').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
    region_data = region_data.sort_values('Sales', ascending=False)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(60, 8, '  Region', border=1, ln=False, align='C')
    pdf.cell(60, 8, 'Total Sales', border=1, ln=False, align='C')
    pdf.cell(60, 8, 'Total Profit', border=1, ln=True, align='C')

    pdf.set_font('Helvetica', '', 11)
    for _, row in region_data.iterrows():
        pdf.cell(60, 8, f"  {row['Region']}", border=1, ln=False)
        pdf.cell(60, 8, f"${row['Sales']:,.0f}", border=1, ln=False, align='C')
        pdf.cell(60, 8, f"${row['Profit']:,.0f}", border=1, ln=True, align='C')
    pdf.ln(5)

    # Category Performance
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, '  Category Performance', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    category_data = df.groupby('Category').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
    category_data = category_data.sort_values('Profit', ascending=False)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(60, 8, '  Category', border=1, ln=False, align='C')
    pdf.cell(60, 8, 'Total Sales', border=1, ln=False, align='C')
    pdf.cell(60, 8, 'Total Profit', border=1, ln=True, align='C')

    pdf.set_font('Helvetica', '', 11)
    for _, row in category_data.iterrows():
        pdf.cell(60, 8, f"  {row['Category']}", border=1, ln=False)
        pdf.cell(60, 8, f"${row['Sales']:,.0f}", border=1, ln=False, align='C')
        pdf.cell(60, 8, f"${row['Profit']:,.0f}", border=1, ln=True, align='C')
    pdf.ln(5)

    # Key Insights
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, '  Key Business Insights', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    top_region = df.groupby('Region')['Sales'].sum().idxmax()
    low_region = df.groupby('Region')['Sales'].sum().idxmin()
    top_profit_cat = df.groupby('Category')['Profit'].sum().idxmax()
    low_profit_cat = df.groupby('Category')['Profit'].sum().idxmin()
    high_discount_loss = df[df['Discount'] > 0.3]['Profit'].sum()
    best_month = df.groupby('Month Name')['Sales'].sum().idxmax()

    insights = [
        f"Top performing region by sales: {top_region}",
        f"Lowest performing region: {low_region} - needs strategy review",
        f"Most profitable category: {top_profit_cat}",
        f"Least profitable category: {low_profit_cat} - review pricing",
        f"Loss from discounts above 30%: ${abs(high_discount_loss):,.0f}",
        f"Best performing month: {best_month} - leverage seasonality",
        f"Overall profit margin: {profit_margin:.1f}%",
    ]

    pdf.set_font('Helvetica', '', 11)
    for insight in insights:
        pdf.set_x(10)
        pdf.multi_cell(180, 7, f"- {insight}")
    pdf.ln(3)

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    return tmp.name

if st.button("📥 Download Business Report"):
    with st.spinner("Generating PDF Report..."):
        pdf_path = generate_pdf_report(df_filtered)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        st.download_button(
            label="📄 Click Here to Download PDF",
            data=pdf_bytes,
            file_name="BI_Report.pdf",
            mime="application/pdf"
        )
        st.success("Report generated successfully! ✅")
        
# Sales Forecasting Section
st.markdown("---")
st.subheader("📈 Sales Forecasting (Next 3 Months)")

from prophet import Prophet

def forecast_sales(df):
    # Prepare MONTHLY data for Prophet (cleaner)
    monthly_sales = df.groupby(pd.Grouper(key='Order Date', freq='ME'))['Sales'].sum().reset_index()
    monthly_sales.columns = ['ds', 'y']
    monthly_sales = monthly_sales[monthly_sales['y'] > 0]  # Remove empty months
    
    # Train model
    model = Prophet(yearly_seasonality=True, 
                   weekly_seasonality=False,
                   daily_seasonality=False)
    model.fit(monthly_sales)
    
    # Predict next 90 days
    future = model.make_future_dataframe(periods=3, freq='ME')
    forecast = model.predict(future)
    
    return forecast, monthly_sales

if st.button("🔮 Generate Sales Forecast"):
    with st.spinner("Training forecasting model..."):
        forecast, actual = forecast_sales(df_filtered)
        
        
        # Plot
        fig = px.line()

        # Actual sales
        fig.add_scatter(x=actual['ds'], y=actual['y'],
                       name='Actual Sales', 
                       line=dict(color='royalblue', width=2))

        # Add last actual point to connect with forecast
        last_actual = actual.iloc[[-1]]
        future_forecast = forecast[forecast['ds'] > actual['ds'].max()]
        
        # Connect line by adding last actual point to forecast
        connect_ds = pd.concat([last_actual['ds'], future_forecast['ds']])
        connect_y = pd.concat([last_actual['y'], future_forecast['yhat']])
        
        fig.add_scatter(x=connect_ds, y=connect_y,
                       name='Forecasted Sales',
                       line=dict(color='lime', width=2, dash='dash'))

        # Confidence band
        fig.add_scatter(x=future_forecast['ds'], y=future_forecast['yhat_upper'],
                       name='Upper Bound',
                       line=dict(color='lightgreen', width=1, dash='dot'))
        fig.add_scatter(x=future_forecast['ds'], y=future_forecast['yhat_lower'],
                       name='Lower Bound',
                       line=dict(color='lightgreen', width=1, dash='dot'),
                       fill='tonexty', fillcolor='rgba(144,238,144,0.1)')

        fig.update_layout(title='Sales Forecast - Next 3 Months',
                         xaxis_title='Date', yaxis_title='Sales ($)',
                         hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        # Show forecast numbers
        st.markdown("### 📊 Forecasted Sales Numbers")
        future_forecast = future_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(90)
        future_forecast.columns = ['Date', 'Predicted Sales', 'Lower Bound', 'Upper Bound']
        future_forecast['Date'] = future_forecast['Date'].dt.strftime('%Y-%m-%d')
        future_forecast['Predicted Sales'] = future_forecast['Predicted Sales'].apply(lambda x: f"${x:,.0f}")
        future_forecast['Lower Bound'] = future_forecast['Lower Bound'].apply(lambda x: f"${x:,.0f}")
        future_forecast['Upper Bound'] = future_forecast['Upper Bound'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(future_forecast, use_container_width=True)


# Automated Insights Generator
st.markdown("---")
st.subheader("🧠 Automated Business Insights")

def generate_insights(df):
    # Prepare data summary for AI
    top_region = df.groupby('Region')['Sales'].sum().idxmax()
    low_region = df.groupby('Region')['Sales'].sum().idxmin()
    top_category_sales = df.groupby('Category')['Sales'].sum().idxmax()
    top_category_profit = df.groupby('Category')['Profit'].sum().idxmax()
    low_category_profit = df.groupby('Category')['Profit'].sum().idxmin()
    total_sales = df['Sales'].sum()
    total_profit = df['Profit'].sum()
    profit_margin = (total_profit / total_sales) * 100
    high_discount_loss = df[df['Discount'] > 0.3]['Profit'].sum()
    best_month = df.groupby('Month Name')['Sales'].sum().idxmax()

    summary = f"""
    You are a senior business analyst. Analyze this data and write 5 clear bullet point insights 
    for a business manager. Be specific with numbers. Highlight problems and opportunities.
    
    Data Summary:
    - Total Sales: ${total_sales:,.0f}
    - Total Profit: ${total_profit:,.0f}
    - Profit Margin: {profit_margin:.1f}%
    - Top Region by Sales: {top_region}
    - Lowest Region by Sales: {low_region}
    - Top Category by Sales: {top_category_sales}
    - Most Profitable Category: {top_category_profit}
    - Least Profitable Category: {low_category_profit}
    - Profit from orders with discount above 30%: ${high_discount_loss:,.0f}
    - Best performing month: {best_month}
    
    Write exactly 5 business insights as bullet points. Start each with an emoji.
    Be direct and actionable. Mention specific numbers.
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": summary}]
    )
    return response.choices[0].message.content

if st.button("🔍 Generate Business Insights"):
    with st.spinner("AI is analyzing your data..."):
        insights = generate_insights(df_filtered)
        st.markdown(insights)

# AI Chatbot Section
st.markdown("---")
st.subheader("🤖 AI Data Analyst Chatbot")
st.markdown("Ask any question about the data in plain English!")

# Groq Client
from dotenv import load_dotenv
import os
load_dotenv()
 

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