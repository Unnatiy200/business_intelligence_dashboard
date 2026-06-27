import sqlite3
import pandas as pd

# Load CSV
df = pd.read_csv("Sample - Superstore.csv", encoding='latin1')

# Clean dates
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Ship Date'] = pd.to_datetime(df['Ship Date'])
df['Year'] = df['Order Date'].dt.year
df['Month'] = df['Order Date'].dt.month
df['Month Name'] = df['Order Date'].dt.strftime('%B')

# Remove unnecessary columns
df = df.drop(columns=['Row ID', 'Country', 'Product ID', 'Customer ID', 'Postal Code'])

# Create SQLite database
conn = sqlite3.connect('superstore.db')

# Save dataframe to SQL table
df.to_sql('sales', conn, if_exists='replace', index=False)

# Test some SQL queries
print("✅ Database created successfully!")
print(f"Total records: {pd.read_sql('SELECT COUNT(*) as count FROM sales', conn).iloc[0,0]}")

print("\n📊 Sales by Region (SQL Query):")
query1 = """
    SELECT Region, 
           ROUND(SUM(Sales), 2) as Total_Sales,
           ROUND(SUM(Profit), 2) as Total_Profit
    FROM sales
    GROUP BY Region
    ORDER BY Total_Sales DESC
"""
print(pd.read_sql(query1, conn))

print("\n📊 Top 5 Products by Sales (SQL Query):")
query2 = """
    SELECT [Product Name],
           ROUND(SUM(Sales), 2) as Total_Sales
    FROM sales
    GROUP BY [Product Name]
    ORDER BY Total_Sales DESC
    LIMIT 5
"""
print(pd.read_sql(query2, conn))

conn.close()
print("\n✅ All SQL queries executed successfully!")