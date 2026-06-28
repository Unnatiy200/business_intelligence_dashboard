# 📊 AI-Powered Business Intelligence Dashboard

An end-to-end Business Intelligence platform that transforms raw sales data 
into actionable insights using Python, SQL, AI and Power BI.

## 🎯 Problem Statement
Companies struggle to extract quick insights from large sales datasets. 
Manual reporting is slow, error-prone and requires technical expertise.

## 💡 Solution
An automated BI platform that:
- Stores data in SQL database
- Generates interactive visualizations
- Uses AI for natural language querying
- Forecasts future sales using ML
- Auto-generates business insights
- Exports professional PDF reports

## 🖥️ Live Demo
![Dashboard Screenshot](screenshot.png)

## ⚙️ Tech Stack
| Tool | Purpose |
|---|---|
| Python | Core programming |
| Pandas | Data cleaning & analysis |
| SQLite | Database storage |
| Plotly | Interactive charts |
| Streamlit | Web dashboard |
| Groq + Llama 3 | AI Chatbot |
| Prophet | Sales Forecasting |
| FPDF2 | PDF Report generation |
| Power BI | Professional BI Dashboard |

## 🚀 Features
- ✅ Interactive dashboard with filters
- ✅ KPI Cards — Sales, Profit, Orders, Customers
- ✅ AI Chatbot for natural language querying
- ✅ Automated business insights generator
- ✅ ML-based sales forecasting (Facebook Prophet)
- ✅ KPI Alerts & Warnings
- ✅ SQL Query Explorer
- ✅ PDF Report Export
- ✅ Power BI Dashboard

## 📊 Key Business Insights Found
- West region drives highest revenue ($725K)
- Technology is most profitable category ($145K profit)
- Furniture has high sales but only 2.5% profit margin
- Discounts above 30% cause $125K in losses
- November consistently shows peak sales every year

## 🛠️ Installation & Setup

### 1. Clone the repository
git clone https://github.com/Unnatiy200/business_intelligence_dashboard.git
cd business_intelligence_dashboard

### 2. Install dependencies
pip install -r requirements.txt

### 3. Set up environment variables
Create a .env file:
GROQ_API_KEY=your_groq_api_key_here

### 4. Create database
python create_database.py

### 5. Run dashboard
streamlit run dashboard.py

## 📁 Project Structure
business_intelligence_dashboard/
├── dashboard.py          # Main Streamlit app
├── create_database.py    # SQL database setup
├── superstore.db         # SQLite database
├── requirements.txt      # Dependencies
├── .env                  # API keys (not uploaded)
├── .gitignore            # Git ignore file
└── BI_Dashboard.pbix     # Power BI dashboard

## 🎓 Skills Demonstrated
- Data cleaning & preprocessing
- SQL database design & querying
- Exploratory Data Analysis (EDA)
- Machine Learning (Time Series Forecasting)
- AI/LLM integration
- Dashboard development
- Business Intelligence & Reporting
