import streamlit as st
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objs as go
import os
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import talib as ta
from talib import MA_Type
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score

def add_bg_and_custom_styles():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #ffffff;
        }}
        .css-18e3th9 {{
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 10px;
            margin: 10px;
            color: #000000 !important;
        }}
        .css-1aumxhk {{
            font-size: 18px;
            color: #000000 !important;
        }}
        .css-1aumxhk input {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px;
            font-size: 16px;
            width: 100%;
            margin-bottom: 10px;
            color: #000000 !important;
        }}
        .st-emotion-cache-1aumxhk {{
            color: #000000 !important;
            font-weight: bold !important;
        }}
        .element-container {{
            color: #000000 !important;
            font-weight: bold !important;
        }}
        .main-content h1, .main-content h2, .main-content h3, .main-content h4, .main-content h5, .main-content h6 {{
            color: #000000 !important;
        }}
        .main-content p {{
            color: #000000 !important;
        }}
        .news-title {{
            font-size: 18px;
            font-weight: bold;
            color: #000000 !important;
            text-decoration: none;
            display: block;
            margin-bottom: 1px;
        }}
        .news-date {{
            font-size: 14px;
            color: #000000 !important;
            margin-bottom: 1px;
        }}
        hr {{
            border: 0;
            height: 1px;
            background: #333;
            background-image: linear-gradient(to right, #ccc, #333, #ccc);
            margin-bottom: 20px;
        }}
        .tab-content {{
            margin: 20px;
        }}
        .stTabs {{
            margin-bottom: 10px;
        }}
        .stTabs [role="tab"] {{
            color: #000000 !important;
        }}
        .stTabs [role="tab"]:hover {{
            color: #000000 !important;
        }}
        .stTabs [role="tab"][aria-selected="true"] {{
            color: #ff0000 !important;  /* Change active tab color to red */
        }}
        .st-emotion-cache-183lzff.exotz4b0 {{
            color: #000000 !important;
            background-color: white !important;
            padding: 10px;
            border-radius: 10px;
            border: 2px solid #ddd;
            margin: 10px 0;
        }}
        .st-emotion-cache-10trblm.e1nzilvr1 {{
            color: #000000 !important;  /* Set text color to black */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Apply the custom styles
add_bg_and_custom_styles()


# Function to read price data from CSV in a folder
def get_price_from_csv(stock_code, folder_path='/Users/kien/Documents/code1/app/thesis-for-Phuong99/Price'):
    csv_file = os.path.join(folder_path, f'{stock_code}_Price.csv')
    try:
        df = pd.read_csv(csv_file)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Handle various formats
        df = df.dropna(subset=['Date'])
        df = df.sort_values(by='Date', ascending=True)
        return df
    except FileNotFoundError:
        return None


def get_quarter_report_from_csv(stock_code, folder_path='/Users/kien/Documents/code1/app/thesis-for-Phuong99/Quarter_report'):
    csv_file = os.path.join(folder_path, f'{stock_code}_quarter_report.csv')
    try:
        df = pd.read_csv(csv_file)
        return df
    except FileNotFoundError:
        return None


# Function to read news data from CSV in a folder
def get_news_from_csv(stock_code, folder_path='/Users/kien/Documents/code1/app/thesis-for-Phuong99/News'):
    csv_file = os.path.join(folder_path, f'{stock_code}_news.csv')
    try:
        df = pd.read_csv(csv_file)
        return df
    except FileNotFoundError:
        return pd.DataFrame()


# Function to perform OLS regression and plot candlestick chart
def perform_ols_and_plot(stock_code):
    # Đường dẫn đến các tệp CSV
    file_path1 = f'/Users/kien/Documents/code1/app/thesis-for-Phuong99/Price/{stock_code}_Price.csv'
    file_path2 = f"/Users/kien/Documents/code1/app/thesis-for-Phuong99/News/{stock_code}_news.csv"

    # Tải dữ liệu từ các tệp CSV
    df1 = pd.read_csv(file_path1)
    df2 = pd.read_csv(file_path2)

    # Chuyển đổi định dạng ngày
    df1['Date'] = pd.to_datetime(df1['Date'])
    df2['Time'] = pd.to_datetime(df2['Time'], format="%d/%m/%Y %H:%M")

    # Chỉ lấy phần ngày từ df2['Time']
    df2['Date'] = df2['Time'].dt.date

    # Chuyển đổi df2['Date'] sang kiểu datetime
    df2['Date'] = pd.to_datetime(df2['Date'])

    # Nhóm dữ liệu tin tức theo ngày và đếm số lượng tin tức trong mỗi ngày
    df2 = df2.groupby('Date', as_index=False).size()
    df2.columns = ['Date', 'News_Count']  # Đổi tên các cột

    # Gộp dữ liệu giá cổ phiếu với số lượng tin tức theo ngày
    df = pd.merge(df1, df2, left_on='Date', right_on='Date', how='left')

    # Thay thế giá trị NaN trong cột 'News_Count' bằng 0
    df['News_Count'] = df['News_Count'].fillna(0)

    # Sắp xếp dữ liệu theo ngày
    df = df.sort_values(by='Date')

    # Thêm cột 'Period'
    df.insert(0, 'Period', range(1, len(df) + 1))

    # Tạo biến tháng
    df['Month'] = df['Date'].dt.month
    df = pd.get_dummies(df, columns=['Month'], drop_first=True)

    # Chuẩn bị dữ liệu hồi quy
    X = df[['Period'] + [col for col in df.columns if 'Month_' in col] + ['News_Count']]
    y = df['Close']

    # Chuyển đổi kiểu dữ liệu nếu cần
    X = X.astype(float)
    y = y.astype(float)

    # Thêm hằng số vào biến độc lập
    X = sm.add_constant(X)

    # Khớp mô hình hồi quy
    model = sm.OLS(y, X).fit()

    df['News_Count'] = df['News_Count'].fillna(0)

    df = df.sort_values(by='Date')
    # Insert a n

    dt_all = pd.date_range(start=df.index[0], end=df.index[-1])

    dt_obs = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(df.index)]

    dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]

    # Plot candlestick chart
    import plotly.graph_objects as go
    fig_candlestick = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['Open'],
                                                     high=df['High'], low=df['Low'],
                                                     close=df['Close'])])
    # Sets customized padding
    fig_candlestick.update_layout(margin=go.layout.Margin(r=10, b=10))

    # Remove dates without values
    fig_candlestick.update_xaxes(rangebreaks=[dict(values=dt_breaks)])

    fig_candlestick.update_yaxes(title_text='Price')
    fig_candlestick.update_xaxes(title_text='Date')

    fig_candlestick.update_layout(title=f"{stock_code}" + ' - CandleStick Chart',
                                  xaxis_rangeslider_visible=False,
                                  height=500, template='plotly_dark')

    # Calculate RSI
    df['RSI'] = ta.RSI(df['Close'], 21)

    # Plot RSI
    fig_rsi = make_subplots(rows=1, cols=1)
    fig_rsi.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI'))
    fig_rsi.add_hline(y=30, line_dash='dash', line_color='limegreen', line_width=1)
    fig_rsi.add_hline(y=70, line_dash='dash', line_color='red', line_width=1)
    fig_rsi.update_yaxes(title_text='RSI Score')

    # Adds the range selector
    fig_rsi.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=6, label='6m', step='month', stepmode='backward'),
                    dict(count=1, label='YTD', step='year', stepmode='todate'),
                    dict(count=1, label='1y', step='year', stepmode='backward'),
                    dict(step='all')
                ]),
            type='date')
    )

    # Set the color from white to black on range selector buttons
    fig_rsi.update_layout(xaxis=dict(rangeselector=dict(font=dict(color='black'))))

    # Sets customized padding
    fig_rsi.update_layout(margin=go.layout.Margin(r=10, b=10))

    layout = go.Layout(template='plotly_dark', title=f"{stock_code} - RSI", height=500, legend_title='Legend')
    fig_rsi.update_layout(layout)

    # Calculate Bollinger Bands
    df['BU'], df['BM'], df['BL'] = ta.BBANDS(df.Close, timeperiod=20, matype=MA_Type.EMA)
    fig_bb = px.line(data_frame=df, x=df.index, y=['Close', 'BU', 'BM', 'BL'])

    # Update y & x axis labels
    fig_bb.update_yaxes(title_text='Price')
    fig_bb.update_xaxes(title_text='Date')

    fig_bb.data[0].name = 'Price'

    # Sets customized padding
    fig_bb.update_layout(margin=go.layout.Margin(r=10, b=10))

    layout = go.Layout(template='plotly_dark', title=f"{stock_code}" + ' - Price, Bollinger Bands', height=500,
                       legend_title='Legend')
    fig_bb.update_layout(layout)

    # Drop Buy and Sell columns if they exist
    df.drop(['Buy', 'Sell'], inplace=True, axis=1, errors='ignore')

    # Create DataFrame
    df_buy = df.query('Low < BL')[['Date', 'Close']]
    df_sell = df.query('High > BU')[['Date', 'Close']]

    # Round close values for both buy and sell
    df_buy['Close'] = round(df_buy.Close.round())
    df_sell['Close'] = round(df_sell.Close.round())

    fig_bs = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['Open'],
                                            high=df['High'],
                                            low=df['Low'],
                                            close=df['Close'],
                                            name='Candlestick')])

    # Plot BU line graph; don't show legend
    fig_bs.add_trace(go.Scatter(x=df['Date'], y=df['BU'],
                                fill=None, mode='lines', showlegend=False))

    # Plot BL line graph and fill upto BU; don't show legend
    fig_bs.add_trace(go.Scatter(x=df['Date'], y=df['BL'],
                                fill='tonexty', mode='lines', showlegend=False))

    # Plot Buy signals
    fig_bs.add_trace(go.Scatter(x=df_buy['Date'], y=df_buy['Close'], mode='markers',
                                marker=dict(symbol='x', size=7, line=dict(width=1)), name='Buy'))

    # Plot Sell Signls
    fig_bs.add_trace(go.Scatter(x=df_sell['Date'], y=df_sell['Close'], mode='markers',
                                marker=dict(symbol='diamond', size=7, line=dict(width=1)), name='Sell'))

    fig_bs.update_yaxes(title_text='Price')
    fig_bs.update_xaxes(title_text='Date')

    fig_bs.data[0].name = 'Price'
    fig_bs.update_layout(margin=go.layout.Margin(r=10, b=10))

    layout = go.Layout(template='plotly_dark',
                       title=f"{stock_code}" + ' - Buy / Sell Signals', height=500,
                       xaxis_rangeslider_visible=False)
    fig_bs.update_layout(layout)

    # Calculate MACD values
    # Empty Data Frame to collect MACD analysis results
    analysis = pd.DataFrame()
    analysis['macd'], analysis['macdSignal'], analysis['macdHist'] = ta.MACD(df.Close,
                                                                             fastperiod=12,
                                                                             slowperiod=26,
                                                                             signalperiod=9)
    fig_ma = make_subplots(rows=2, cols=1)

    # Candlestick chart for pricing
    fig_ma.append_trace(go.Candlestick(x=df['Date'], open=df['Open'],
                                       high=df['High'], low=df['Low'],
                                       close=df['Close'], showlegend=False),
                        row=1, col=1)

    # Fast Signal (%k)
    fig_ma.append_trace(go.Scatter(x=df['Date'],
                                   y=analysis['macd'],
                                   line=dict(color='#C42836', width=1),
                                   name='MACD Line'), row=2, col=1)

    # Slow signal (%d)
    fig_ma.append_trace(go.Scatter(x=df['Date'], y=analysis['macdSignal'],
                                   line=dict(color='limegreen', width=1),
                                   name='Signal Line'), row=2, col=1)

    # Colorize the histogram values
    colors = np.where(analysis['macd'] < 0, '#EA071C', '#57F219')

    # Plot the histogram
    fig_ma.append_trace(go.Bar(x=df['Date'], y=analysis['macdHist'],
                               name='Histogram', marker_color=colors),
                        row=2, col=1)

    fig_ma['layout']['yaxis']['title'] = 'Price'
    fig_ma['layout']['xaxis2']['title'] = 'Date'

    fig_ma.data[0].name = 'Price'

    # Sets customized padding
    fig_ma.update_layout(margin=go.layout.Margin(r=10, b=10))

    # Make it pretty
    layout = go.Layout(template='plotly_dark', title=f"{stock_code}" + ' - MACD Indicator', height=700,
                       xaxis_rangeslider_visible=False)

    # Update options and show plot
    fig_ma.update_layout(layout)

    fig_ma.update_layout(legend=dict(yanchor="top", y=0.45, xanchor="left", x=1.01))

    return model.summary(), fig_candlestick, fig_rsi, fig_bb, fig_bs, fig_ma


# Display stock price information
def display_stock_price_info(stock_code):
    stock_code = stock_code.upper()
    price_data = get_price_from_csv(stock_code)

    if price_data is not None:
        st.subheader(f"Thông tin giá cho cổ phiếu {stock_code}: ")

        # Date selection with a default range
        min_date = price_data['Date'].min()
        max_date = price_data['Date'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date_options = pd.date_range(min_date, max_date).strftime("%d/%m/%Y")
            default_start = pd.to_datetime(min_date).strftime("%d/%m/%Y")  # Default to min_date
            start_date = st.selectbox('Chọn ngày bắt đầu', options=start_date_options, index=0, key='start')
        with col2:
            end_date_options = pd.date_range(min_date, max_date).strftime("%d/%m/%Y")
            default_end = pd.to_datetime(max_date).strftime("%d/%m/%Y")  # Default to max_date
            end_date = st.selectbox('Chọn ngày kết thúc', options=end_date_options,
                                   index=len(end_date_options)-1, key='end')

        # Parse dates consistently
        start_date = pd.to_datetime(start_date, format="%d/%m/%Y")
        end_date = pd.to_datetime(end_date, format="%d/%m/%Y")

        # Filter price data
        filtered_price_data = price_data[(price_data['Date'] >= start_date) & (price_data['Date'] <= end_date)]

        # Display the filtered data table
        st.dataframe(filtered_price_data.reset_index(drop=True))

        # Ensure 'Close' column exists and is numeric
        if 'Close' not in filtered_price_data.columns:
            st.error("Error: 'Close' column not found in price data. Available columns: ", filtered_price_data.columns)
            return
        filtered_price_data['Close'] = pd.to_numeric(filtered_price_data['Close'], errors='coerce')

        # Create and display the Plotly chart
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=filtered_price_data['Date'],
                y=filtered_price_data['Close'],
                mode='lines+markers',  # Show lines and markers
                name='Close'
            )
        )
        fig.update_layout(
            title=dict(
                text=f'Giá đóng cửa của cổ phiếu {stock_code} theo thời gian',
                font=dict(color='black')
            ),
            xaxis=dict(
                title=dict(text='Ngày', font=dict(color='black')),
                tickfont=dict(color='black'),
                rangeslider=dict(visible=True),
                type='date',
                tickformat='%Y-%m-%d',
                showgrid=False,
                color='black'
            ),
            yaxis=dict(
                title=dict(text='Giá', font=dict(color='black')),
                tickfont=dict(color='black'),
                showgrid=False,
                color='black'
            ),
            plot_bgcolor='rgba(255,255,255,0.8)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='black')
        )
        st.plotly_chart(fig)

        # Display candlestick chart and RSI
        ols_summary, candlestick_fig, rsi_fig, bb_fig, bs_fig, ma_fig = perform_ols_and_plot(stock_code)
        st.subheader("OLS Regression Results")
        # st.text(ols_summary)

        st.plotly_chart(candlestick_fig)
        st.plotly_chart(rsi_fig)
        st.plotly_chart(bb_fig)
        st.plotly_chart(bs_fig)
        st.plotly_chart(ma_fig)



    else:
        st.error(f"Không tìm thấy thông tin giá cho cổ phiếu {stock_code}.")


# Display stock news information
def display_stock_news(stock_code):
    stock_code = stock_code.upper()
    news_data = get_news_from_csv(stock_code)

    if not news_data.empty:

        items_per_page = 5
        total_pages = len(news_data) // items_per_page + (1 if len(news_data) % items_per_page > 0 else 0)

        current_page = st.number_input('Chọn trang', min_value=1, max_value=total_pages, value=1, step=1)
        st.subheader(f"Tin tức liên quan cho cổ phiếu {stock_code}: (Trang {current_page}/{total_pages})")

        start_index = (current_page - 1) * items_per_page
        end_index = start_index + items_per_page
        paginated_news = news_data.iloc[start_index:end_index]

        for _, news_item in paginated_news.iterrows():
            st.markdown(f'<div class="news-date">{news_item["Time"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<a href="{news_item["Link"]}" class="news-title">{news_item["Title"]}</a>',
                        unsafe_allow_html=True)
            st.markdown('<hr>', unsafe_allow_html=True)
    else:
        st.warning(f'Không tìm thấy tin tức liên quan cho cổ phiếu {stock_code}.')


# Display stock quarter report information
def display_stock_quarter_report(stock_code):
    stock_code = stock_code.upper()
    quarter_report_data = get_quarter_report_from_csv(stock_code)

    if quarter_report_data is not None:
        st.subheader(f"Báo cáo tài chính theo từng quý cho cổ phiếu {stock_code}: ")
        unique_times = quarter_report_data['Time'].unique()
        selected_time = st.selectbox('Chọn mốc thời gian', unique_times)
        filtered_data = quarter_report_data[quarter_report_data['Time'] == selected_time]

        # Drop the 'Time' column before transposition to avoid mixing types
        if 'Time' in filtered_data.columns:
            filtered_data = filtered_data.drop(columns=['Time'])

        # Transpose the dataframe
        filtered_data = filtered_data.transpose()

        # Dynamically set column names based on the number of columns
        num_columns = filtered_data.shape[1]
        if num_columns == 1:
            filtered_data.columns = ['Value']
        else:
            filtered_data.columns = [f'Column_{i + 1}' for i in range(num_columns)]

        # Ensure consistent data types for Arrow compatibility
        for col in filtered_data.columns:
            # Try converting to float; if it fails, keep as string
            try:
                filtered_data[col] = pd.to_numeric(filtered_data[col], errors='coerce')
            except ValueError:
                filtered_data[col] = filtered_data[col].astype(str)

        # Display the dataframe
        st.dataframe(filtered_data, use_container_width=True)
    else:
        st.error(f"Không tìm thấy báo cáo tài chính theo từng quý cho cổ phiếu {stock_code}.")
        st.write(
            f"Debug info: File path tried - {os.path.join('/Users/kien/Documents/code1/app/thesis-for-Phuong99/Quarter_report', f'{stock_code}_quarter_report.csv')}")


# Function to read the filtered sorted stocks from the uploaded file
def get_filtered_sorted_stocks(file_path):
    try:
        df = pd.read_csv(file_path)
        df.index = range(1, len(df) + 1)
        return df
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()


# Display the filtered sorted stocks
def display_filtered_sorted_stocks():
    file_path = '/Users/kien/Documents/code1/app/thesis-for-Phuong99/ChooseStock/goodfindexstock.csv'

    filtered_sorted_stocks = get_filtered_sorted_stocks(file_path)

    if not filtered_sorted_stocks.empty:
        st.subheader("Các cổ phiếu nên đầu tư")
        st.dataframe(filtered_sorted_stocks)
    else:
        st.warning("Không tìm thấy dữ liệu cổ phiếu nên đầu tư.")


def perform_clustering():
    df = pd.read_csv("/Users/kien/Documents/code1/app/thesis-for-Phuong99/Clustering/Clustering.csv")
    df = pd.DataFrame(df)

    # Standardize the data
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df[['Average_Percentage_Increase', 'Price_Std_dev']])

    # Determine the optimal number of clusters using the Elbow Method and Silhouette Score
    wcss = []
    silhouette_scores = []
    K_range = range(2, 10)

    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=0)
        kmeans.fit(df_scaled)
        wcss.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(df_scaled, kmeans.labels_))

    # Plotting the Elbow Method and Silhouette Score
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(K_range, wcss, marker='o')
    plt.xlabel('Number of clusters')
    plt.ylabel('WCSS')
    plt.title('Elbow Method')

    plt.subplot(1, 2, 2)
    plt.plot(K_range, silhouette_scores, marker='o')
    plt.xlabel('Number of clusters')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Score Method')

    plt.tight_layout()
    st.pyplot(plt)

    # Choosing the number of clusters (let's go with 3 as per the previous analysis)
    optimal_k = 6
    kmeans = KMeans(n_clusters=optimal_k, random_state=0)
    df['Cluster'] = kmeans.fit_predict(df_scaled)

    # Plotting the final clusters with stock names
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(df['Average_Percentage_Increase'], df['Price_Std_dev'], c=df['Cluster'], cmap='viridis')
    plt.xlabel('Average Percentage Increase')
    plt.ylabel('Price Std Dev')
    plt.title('KMeans Clustering of Stocks')
    plt.colorbar(label='Cluster')

    # Annotate each point with the stock name
    for i, txt in enumerate(df['Stock']):
        plt.annotate(txt, (df['Average_Percentage_Increase'][i], df['Price_Std_dev'][i]))

    plt.grid(True)
    st.pyplot(plt)


# Main content
st.title('THÔNG TIN CỔ PHIẾU VN30')

# Add an option to display the filtered sorted stocks in the sidebar
show_stocks = st.sidebar.checkbox('Hiển thị các cổ phiếu nên đầu tư')

if show_stocks:
    display_filtered_sorted_stocks()

# Sidebar for stock search
st.sidebar.header('Tìm kiếm cổ phiếu')
search_query = st.sidebar.text_input('Nhập mã cổ phiếu: ')

if search_query:
    tabs = st.tabs(['Thông tin giá', 'Tin tức', 'Báo cáo tài chính', 'Clustering'])

    with tabs[0]:
        display_stock_price_info(search_query)
    with tabs[1]:
        display_stock_news(search_query)
    with tabs[2]:
        display_stock_quarter_report(search_query)
    with tabs[3]:
        perform_clustering()


# if search_query:
#     tabs = st.tabs(['Thông tin giá'])
#
#     with tabs[0]:
#         display_stock_price_info(search_query)
#     with tabs[1]:
#         display_stock_news(search_query)
