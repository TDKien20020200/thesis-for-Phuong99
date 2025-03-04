import pandas as pd
import logging
import requests
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import warnings
import os

# Vô hiệu hóa cảnh báo không cần thiết
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Định nghĩa URL và header cho API
API_VNDIRECT = 'https://finfo-api.vndirect.com.vn/v4/stock_prices/'
HEADERS = {
    'User-Agent': 'Your_User_Agent',
    'Authorization': 'Your_Authorization_Token'  # Thêm token nếu API yêu cầu
}


# Hàm tiện ích
def convert_date(text, date_type='%Y-%m-%d'):
    return datetime.strptime(text, date_type)


def convert_text_dateformat(text, origin_type='%Y-%m-%d', new_type='%Y-%m-%d'):
    return convert_date(text, origin_type).strftime(new_type)


# Định nghĩa các lớp DataLoader
class DataLoader:
    def __init__(self, symbols, start, end, minimal=True):
        self.symbols = symbols
        self.start = start
        self.end = end
        self.minimal = minimal

    def download(self):
        loader = DataLoaderVND(self.symbols, self.start, self.end)
        stock_data = loader.download()

        if self.minimal:
            data = stock_data.copy()
            data.reset_index(inplace=True)
            data = data[['date', 'high', 'low', 'open', 'close', 'avg', 'volume']]
            return data
        else:
            return stock_data


class DataLoadProto:
    def __init__(self, symbols, start, end):
        self.symbols = symbols
        self.start = convert_text_dateformat(start)
        self.end = convert_text_dateformat(end)


class DataLoaderVND(DataLoadProto):
    def __init__(self, symbols, start, end):
        super().__init__(symbols, start, end)

    def download(self):
        stock_datas = []
        if not isinstance(self.symbols, list):
            symbols = [self.symbols]
        else:
            symbols = self.symbols

        for symbol in symbols:
            stock_datas.append(self.download_one_new(symbol))

        data = pd.concat(stock_datas, axis=1)
        return data

    def download_one_new(self, symbol):
        start_date = self.start
        end_date = self.end
        query = f'code:{symbol}~date:gte:{start_date}~date:lte:{end_date}'
        delta = convert_date(end_date) - convert_date(start_date)
        params = {
            "sort": "date",
            "size": delta.days + 1,
            "page": 1,
            "q": query
        }
        res = requests.get(API_VNDIRECT, params=params, headers=HEADERS)
        data = res.json()['data']
        data = pd.DataFrame(data)
        stock_data = data[['date', 'adClose', 'close', 'pctChange', 'average', 'nmVolume',
                           'nmValue', 'ptVolume', 'ptValue', 'open', 'high', 'low']].copy()
        stock_data.columns = ['date', 'adjust', 'close', 'change_perc', 'avg',
                              'volume_match', 'value_match', 'volume_reconcile', 'value_reconcile',
                              'open', 'high', 'low']

        stock_data = stock_data.set_index('date').apply(pd.to_numeric, errors='coerce')
        stock_data.index = list(map(convert_date, stock_data.index))
        stock_data.index.name = 'date'
        stock_data = stock_data.sort_index()
        stock_data.fillna(0, inplace=True)
        stock_data['volume'] = stock_data.volume_match + stock_data.volume_reconcile

        iterables = [stock_data.columns.tolist(), [symbol]]
        mulindex = pd.MultiIndex.from_product(iterables, names=['Attributes', 'Symbols'])
        stock_data.columns = mulindex

        logging.info(f'data {symbol} from {self.start} to {self.end} have already cloned!')
        return stock_data


# Danh sách công ty VN30
vn30_companies = ["ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG", "MBB",
                  "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB", "TCB", "TPB",
                  "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"]

# Đường dẫn thư mục lưu trữ trên macOS
OUTPUT_DIR = os.path.expanduser("~/Price/")
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

# Lặp qua từng mã chứng khoán trong VN30
for stock in vn30_companies:
    file_path = os.path.join(OUTPUT_DIR, f"{stock}_Price.csv")
    loader = DataLoader(stock, '2024-05-07', '2030-04-02', minimal=True)
    data = loader.download()

    # Đổi tên cột
    column_mapping = {
        'date': 'Date',
        'close': 'Close',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'volume': 'Vol.'
    }
    data = data.rename(columns=column_mapping)
    data.columns = [col[0] for col in data.columns]  # Lấy tên cột từ tuple

    # Chọn các cột cần thiết và nhân giá trị với 1000
    df1 = data[["Date", "Close", "Open", "High", "Low", "Vol."]]
    df1.loc[:, 'Close'] = df1['Close'] * 1000
    df1.loc[:, 'Open'] = df1['Open'] * 1000
    df1.loc[:, 'High'] = df1['High'] * 1000
    df1.loc[:, 'Low'] = df1['Low'] * 1000

    # Kiểm tra tệp tồn tại
    if not os.path.exists(file_path):
        df1.to_csv(file_path, index=False)
        print(f"{file_path} created.")
    else:
        df2 = pd.read_csv(file_path, index_col=False)
        df1['Date'] = pd.to_datetime(df1['Date'])
        df2['Date'] = pd.to_datetime(df2['Date'])
        merged_df_correct_order = pd.concat([df1, df2[~df2['Date'].isin(df1['Date'])]], ignore_index=True)
        sorted_merged_df = merged_df_correct_order.sort_values(by='Date', ascending=False).reset_index(drop=True)
        sorted_merged_df.to_csv(file_path, index=False)
        print(f"{file_path} updated.")