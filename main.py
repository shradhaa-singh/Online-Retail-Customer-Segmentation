import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import squarify

df=pd.read_csv("data.csv")

#Operations on data

#drop duplicates
df=df.drop_duplicates()

#CustomerID to int type
df = df.dropna(subset=['CustomerID'])
df['CustomerID'] = df['CustomerID'].astype(int)

# Remove cancelled orders(invoiceno contain "C" in start)
df = df[~df['InvoiceNo'].str.contains('C', na=False)]

# Filter out StockCodes that aren't actual products
tags_to_remove = ['POST', 'D', 'DOT', 'M', 'BANK CHARGES']
df = df[~df['StockCode'].isin(tags_to_remove)]

# Keep only positive quantities and unit prices
df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]

#to consider uppercase and lowercase name as same
df['Description'] = df['Description'].str.strip().str.upper()

df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# print(df.isnull().sum())   ---> to check if data is cleaned
#print(df.describe())
#df[df['InvoiceNo'].str.startswith('C', na=False)]
#print(df.duplicated().sum())

#total revenue. --->this will be y-axus for charts
df['TotalRevenue'] = df['Quantity'] * df['UnitPrice']

# Graph for Monthly Trends

df['MonthYear'] = df['InvoiceDate'].dt.to_period('M').astype(str)
monthly_trend = df.groupby('MonthYear')['TotalRevenue'].sum().reset_index()
plt.figure(figsize=(12, 6))
sns.lineplot(data=monthly_trend, x='MonthYear', y='TotalRevenue', marker='o', linewidth=2.5, color='#2ecc71')
plt.title('Total Monthly Revenue Trend (Dec 2010 - Dec 2011)', fontsize=15)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Revenue (£)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# Graph to show top countries

top_countries = df.groupby('Country')['TotalRevenue'].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(12, 6))
top_countries.plot(kind='bar', color='skyblue')
plt.title('Top 10 Countries by Revenue')
plt.ylabel('Revenue (£)')
plt.show()

# grpah to show top products

# Top 10 Products by Quantity
top_products_qty = df.groupby('Description')['Quantity'].sum().sort_values(ascending=False).head(10)

# Top 10 Products by Revenue
top_products_rev = df.groupby('Description')['TotalRevenue'].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(12, 12))

# quantity
plt.subplot(2, 1, 1)
top_products_qty.sort_values().plot(kind='barh', color='teal', edgecolor='black')
plt.title('Top 10 Products by Quantity Sold', fontsize=16, pad=20)
plt.xlabel('Total Units Sold', fontsize=12)
plt.ylabel('', fontsize=12) 

# Revenue
plt.subplot(2, 1, 2)
top_products_rev.sort_values().plot(kind='barh', color='coral', edgecolor='black')
plt.title('Top 10 Products by Revenue Generated', fontsize=16, pad=20)
plt.xlabel('Total Revenue (£)', fontsize=12)
plt.ylabel('', fontsize=12)

plt.tight_layout(pad=5.0) 
plt.show()

# recency, frequency, monetary

#one day after last day of dataset
snapshot_date = df['InvoiceDate'].max() + dt.timedelta(days=1)

rfm = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days, # Recency
    'InvoiceNo': 'nunique',                                 # Frequency
    'TotalRevenue': 'sum'                                   # Monetary
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

# Binning (qcut use karke barabar groups mein baantna)
rfm['R_score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1]) # Chota number = Better score
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
rfm['M_score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])

# Total RFM Score
rfm['RFM_Group'] = rfm.R_score.astype(str) + rfm.F_score.astype(str) + rfm.M_score.astype(str)
rfm['Total_Score'] = rfm[['R_score', 'F_score', 'M_score']].sum(axis=1)

# mapping logic
segment_map = {
    r'[1-2][1-2]': 'Hibernating',
    r'[1-2][3-4]': 'At Risk',
    r'[1-2]5': 'Can\'t Lose Them',
    r'3[1-2]': 'About To Sleep',
    r'33': 'Need Attention',
    r'[3-4][4-5]': 'Loyal Customers',
    r'41': 'Promising',
    r'51': 'New Customers',
    r'[4-5][2-3]': 'Potential Loyalists',
    r'5[4-5]': 'Champions'
}

rfm['Segment'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str)
rfm['Segment'] = rfm['Segment'].replace(segment_map, regex=True)

# Create a figure with subplots
fig = plt.figure(figsize=(16, 12))

# 1. Bar Chart (Top Left)
ax1 = plt.subplot(2, 2, 1)
sns.countplot(data=rfm, y='Segment', order=rfm['Segment'].value_counts().index, palette='viridis', ax=ax1)
ax1.set_title('Segment Counts')

# 2. Scatter Plot (Top Right)
ax2 = plt.subplot(2, 2, 2)
sns.scatterplot(data=rfm, x='Recency', y='Frequency', hue='Segment', alpha=0.5, ax=ax2)
ax2.set_title('Recency vs Frequency')

# 3. Treemap (Bottom - spans across both columns)
ax3 = plt.subplot(2, 1, 2)
top_segments = rfm['Segment'].value_counts()
squarify.plot(sizes=top_segments.values, label=top_segments.index, alpha=0.7, color=sns.color_palette("Spectral", len(top_segments)), ax=ax3)
ax3.set_title('RFM Segments Proportion')
plt.axis('off')

plt.tight_layout()
plt.show()