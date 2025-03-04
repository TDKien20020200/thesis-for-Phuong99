import pandas as pd
import statsmodels.api as sm
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import talib as ta
from talib import MA_Type
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import talib as ta


# Nhập tên cổ phiếu
stock = input("Enter the stock name: ")

# Đường dẫn đến các tệp CSV
file_path1 = f"/Users/kien/Documents/code1/app/thesis-for-Phuong99/Price/{stock}_Price.csv"
file_path2 = f"/Users/kien/Documents/code1/app/thesis-for-Phuong99/News/{stock}_news.csv"

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

# # Kiểm tra kiểu dữ liệu
# print(X.dtypes)
# print(y.dtypes)

# Chuyển đổi kiểu dữ liệu nếu cần
X = X.astype(float)
y = y.astype(float)

# Thêm hằng số vào biến độc lập
X = sm.add_constant(X)

# Khớp mô hình hồi quy
model = sm.OLS(y, X).fit()

# In kết quả hồi quy
print(model.summary())
########################################################################################################################

dt_all = pd.date_range(start=df.index[0],end=df.index[-1])

dt_obs = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(df.index)]

dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]


fig = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['Open'],
                                     high=df['High'], low=df['Low'],
                                     close=df['Close'])])

# Sets customized padding
fig.update_layout(margin=go.layout.Margin(r=10,b=10))

# Remove dates without values
fig.update_xaxes(rangebreaks=[dict(values=dt_breaks)])

fig.update_yaxes(title_text='Price')
fig.update_xaxes(title_text='Date')

fig.update_layout(title = f"{stock}" + ' - CandleStick Chart',
                  xaxis_rangeslider_visible=False,
                  height=500, template='plotly_dark')
########################################################################################################################
# Chạy RSI
df['RSI'] = ta.RSI(df['Close'], 21)

# Construct a 1 x 1 Plotly figure
fig = make_subplots(rows=1, cols=1)

# Plot RSI
fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI'))

fig.add_hline(y=30, line_dash='dash', line_color='limegreen', line_width=1)
fig.add_hline(y=70, line_dash='dash', line_color='red', line_width=1)
fig.update_yaxes(title_text='RSI Score')

# Adds the range selector
fig.update_layout(
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
fig.update_layout(xaxis=dict(rangeselector=dict(font=dict(color='black'))))

# Sets customized padding
fig.update_layout(margin=go.layout.Margin(r=10, b=10))

# Remove dates without values
fig.update_xaxes(rangebreaks=[dict(values=dt_breaks)])

layout = go.Layout(template='plotly_dark', title=f"{stock} - RSI", height=500, legend_title='Legend')
fig.update_layout(layout)

fig.show()

########################################################################################################################
# Bollinger band
df['BU'], df['BM'], df['BL'] = ta.BBANDS(df['Close'], timeperiod=20, matype=MA_Type.EMA)

# Create the line chart with Plotly
fig = px.line(data_frame=df, x='Date',
              y=['Close', 'BU', 'BM', 'BL'],
              title=f"{stock} - Price, Bollinger Bands")

# Update y & x axis labels
fig.update_yaxes(title_text='Price')
fig.update_xaxes(title_text='Date')

# Rename the first data trace to 'Price'
fig.data[0].name = 'Price'

# Sets customized padding
fig.update_layout(margin=go.layout.Margin(
    r=10,
    b=10))

# Customize the layout with a dark theme and other specifications
fig.update_layout(template='plotly_dark',
                  title=f"{stock} - Price, Bollinger Bands",
                  height=500,
                  legend_title='Legend')

# Show the figure
fig.show()

########################################################################################################################
# Drop Buy and Sell columns if they exist
df.drop(['Buy', 'Sell'], inplace=True, axis=1, errors='ignore')

# Create DataFrame
df_buy = df.query('Low < BL')[['Date', 'Close']]
df_sell = df.query('High > BU')[['Date', 'Close']]

# Round close values for both buy and sell
df_buy['Close'] = round(df_buy.Close.round())
df_sell['Close'] = round(df_sell.Close.round())

fig = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['Open'],
                                     high=df['High'],
                                     low=df['Low'],
                                     close=df['Close'],
                                     name='Candlestick')])

# Plot BU line graph; don't show legend
fig.add_trace(go.Scatter(x=df['Date'], y=df['BU'],
                         fill=None, mode='lines', showlegend=False))

# Plot BL line graph and fill upto BU; don't show legend
fig.add_trace(go.Scatter(x=df['Date'], y=df['BL'],
                         fill='tonexty', mode='lines', showlegend=False))

# Plot Buy signals
fig.add_trace(go.Scatter(x=df_buy['Date'], y=df_buy['Close'], mode='markers',
                         marker=dict(symbol='x', size=7, line=dict(width=1)), name='Buy'))

# Plot Sell Signls
fig.add_trace(go.Scatter(x=df_sell['Date'], y=df_sell['Close'], mode='markers',
                         marker=dict(symbol='diamond', size=7, line=dict(width=1)), name='Sell'))

fig.update_yaxes(title_text='Price')
fig.update_xaxes(title_text='Date')

fig.data[0].name = 'Price'
fig.update_layout(margin=go.layout.Margin(r=10, b=10))

layout = go.Layout(template='plotly_dark',
                   title=f"{stock}" + ' - Buy / Sell Signals', height=500,
                   xaxis_rangeslider_visible=False)
fig.update_layout(layout)

########################################################################################################################
# Calculate MACD values
# Empty Data Frame to collect MACD analysis results
analysis = pd.DataFrame()
analysis['macd'], analysis['macdSignal'],analysis['macdHist'] = ta.MACD(df.Close,
                                                                fastperiod=12,
                                                                slowperiod=26,
                                                                signalperiod=9)
fig = make_subplots(rows=2, cols=1)

# Candlestick chart for pricing
fig.append_trace(go.Candlestick(x=df['Date'], open=df['Open'],
                                high=df['High'], low=df['Low'],
                                close=df['Close'], showlegend=False),
                                row=1, col=1)

# Fast Signal (%k)
fig.append_trace(go.Scatter(x=df['Date'],
                            y=analysis['macd'],
                            line=dict(color='#C42836', width=1),
                            name='MACD Line'), row=2, col=1)

# Slow signal (%d)
fig.append_trace(go.Scatter(x=df['Date'], y=analysis['macdSignal'],
                            line=dict(color='limegreen', width=1),
                            name='Signal Line'), row=2, col=1)

# Colorize the histogram values
colors = np.where(analysis['macd'] < 0, '#EA071C', '#57F219')

# Plot the histogram
fig.append_trace(go.Bar(x=df['Date'], y=analysis['macdHist'],
                        name='Histogram', marker_color=colors),
                       row=2, col=1)

fig['layout']['yaxis']['title']='Price'
fig['layout']['xaxis2']['title']='Date'

fig.data[0].name = 'Price'

# Sets customized padding
fig.update_layout(margin=go.layout.Margin(r=10, b=10))

# Make it pretty
layout = go.Layout(template='plotly_dark', title = f"{stock}" + ' - MACD Indicator', height=700,
    xaxis_rangeslider_visible=False)

# Update options and show plot
fig.update_layout(layout)

fig.update_layout(legend=dict(yanchor="top", y=0.45, xanchor="left", x=1.01))
fig.show()

########################################################################################################################
# RSI
df['RSI'] = ta.RSI(df['Close'], timeperiod=21)

# Bollinger Bands
df['BU'], df['BM'], df['BL'] = ta.BBANDS(df['Close'], timeperiod=20, matype=ta.MA_Type.EMA)

# MACD
df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)

# Signals
df['Buy_Signal'] = np.where((df['RSI'] < 30) & (df['Close'] < df['BL']), df['Close'], np.nan)
df['Sell_Signal'] = np.where((df['RSI'] > 70) & (df['Close'] > df['BU']), df['Close'], np.nan)

# Calculate Reverse Signal only if there are no Buy or Sell Signals
df['Reverse_Signal'] = np.where((df['MACD'].shift(1) < df['MACD_Signal'].shift(1)) &
                                (df['MACD'] > df['MACD_Signal']) |
                                (df['MACD'].shift(1) > df['MACD_Signal'].shift(1)) &
                                (df['MACD'] < df['MACD_Signal']) &
                                df['Buy_Signal'].isna() & df['Sell_Signal'].isna(), df['Close'], np.nan)

# Plotting
fig = go.Figure()

# Plot Price with Bollinger Bands and signals
fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
fig.add_trace(go.Scatter(x=df['Date'], y=df['BU'], line=dict(color='blue', width=1), name='Upper Band'))
fig.add_trace(go.Scatter(x=df['Date'], y=df['BL'], line=dict(color='red', width=1), name='Lower Band'))
fig.add_trace(go.Scatter(x=df['Date'], y=df['Buy_Signal'], mode='markers', marker=dict(symbol='triangle-up', color='green', size=10), name='Buy Signal'))
fig.add_trace(go.Scatter(x=df['Date'], y=df['Sell_Signal'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=10), name='Sell Signal'))
fig.add_trace(go.Scatter(x=df['Date'], y=df['Reverse_Signal'], mode='markers', marker=dict(symbol='x', color='orange', size=10), name='Reverse Signal'))

# Update layout
fig.update_layout(template='plotly_dark', title='Combined Technical Indicators with Signals', height=600, margin=go.layout.Margin(r=10, b=10))
fig.update_xaxes(title_text='Date')
fig.update_yaxes(title_text='Price')

fig.show()