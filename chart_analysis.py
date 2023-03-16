import datetime as dt
import re


import pandas as pd
import numpy as np
import pandas_datareader.data as pdr
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import talib as ta


#株価情報を取得する関数定義(Open,High,Low,Close,Volume)
#米国の株価情報を取得する場合は、17行目を'US'に変換
def get_stock_data(code):
    df = pdr.DataReader('{}.JP'.format(code), 'stooq').sort_index()
    return df

#企業名を取得する関数定義
def get_brand(code):
    url='https://finance.yahoo.co.jp/quote/{}'.format(code)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    elems = soup.find_all('h1')
    return elems

#株価情報取得
code = input('証券コードを入力してください：')
df = get_stock_data(code)
#企業名取得
elems = get_brand(code)
elems = list(elems)
brand_name_base = str(elems[1])
# print(type(brand_name_base))
#>や<に囲まれている企業名だけを抽出する
brand_name = re.search(r'>(.+)<',brand_name_base).group(1)
# print(brand_name)


#株価データの時期を指定
df = df[dt.datetime(2021,1,1):]

#レイアウトの定義
layout = {
    'height':800,
    'title': {'text':'{} {}'.format(code, brand_name), 'x': 0.5},
    'xaxis': {'rangeslider': {'visible': False}},
    'yaxis1': {'domain':[.56, 1.0], 'title': '価格(円)', 'side': 'left', 'tickformat': ','},
    'yaxis2': {'domain':[.40, .56]},
    'yaxis3': {'domain': [.30, .395], 'title': 'MACD', 'side': 'right'},
    'yaxis4': {'domain': [.20, .295], 'title': 'RSI', 'side': 'right'},
    'yaxis5': {'domain': [.10, .195], 'title': 'STC', 'side': 'right'},
    'yaxis6': {'domain':[.00, .095], 'title': 'Volume', 'side':'right'},
    'plot_bgcolor':'light blue'
}

#横軸の日付をDateTime型からstr型に変換し、土日の日付を詰めて表示する
df.index = pd.to_datetime(df.index).strftime('%m-%d-%Y')

#終値の移動平均データ
close = df['Close']
ma5, ma25 = ta.SMA(close, timeperiod=5) ,ta.SMA(close, timeperiod=25)
df['ma5'], df['ma25'] = ma5, ma25

#ゴールデンクロス、デッドクロスのトレンドの転換を定義
cross = ma5 > ma25
# print(cross)
cross_shift = cross.shift(1)
# print(cross_shift)
temp_gc = (cross != cross_shift) & (cross == True)
# print(temp_gc)
temp_dc = (cross != cross_shift) & (cross == False)

#ゴールデンクロス発生日であればMA5の値、それ以外はNAN
df['gc'] = [m if g == True else np.nan for g, m in zip(temp_gc, ma5)]
#デッドクロス発生日であればMA25の値、それ以外はNAN
df['dc'] = [m if d == True else np.nan for d, m in zip(temp_dc, ma25)]

#ボリンジャーバンドデータの定義
uuper2, _, lower2 = ta.BBANDS(close, timeperiod=25,
                              nbdevup=2, nbdevdn=2, matype=0)
df['uuper2'], df['lower2'] = uuper2, lower2

#MACD, シグナル, ヒスとグラムの算出
macd, macdsignal, hist = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
df['macd'] = macd
df['macd_signal'] = macdsignal
df['hist'] = hist

#RSI
rsi14 = ta.RSI(close, timeperiod=14)
rsi28 = ta.RSI(close, timeperiod=28)
df['rsi14'], df['rsi28'] = rsi14, rsi28
#補助線
df['70'], df['30'] = [70 for _ in close], [30 for _ in close]

#ストキャスティクス
slowK, slowD = ta.STOCH(df['High'], df['Low'], df['Close'], fastk_period=5, slowk_period=3,
                        slowk_matype=0, slowd_period=3, slowd_matype=0)
df['slowK'], df['slowD'] = slowK, slowD
#補助線
df['80'], df['20'] = [80 for _ in close], [20 for _ in close]

#データの定義
data = [go.Candlestick(yaxis='y1', x=df.index, open=df['Open'], high=df['High'], low=df['Low'],
                   close=df['Close'], increasing_line_color='red', increasing_line_width=1.0,
                   increasing_fillcolor='red',
                   decreasing_line_color='gray', decreasing_line_width=1.0,
                   decreasing_fillcolor='gray'),
                   #5日移動平均線
                   go.Scatter(yaxis='y1', x=df.index, y=df['ma5'], name='MA5',
                               line={'color':'royalblue', 'width':1.2}),
                   #25日移動平均線
                   go.Scatter(yaxis='y1', x=df.index, y=df['ma25'], name='MA25',
                               line={'color':'lightseagreen', 'width':1.2}),
                   #ゴールデンクロス
                   go.Scatter(yaxis='y1', x=df.index, y=df['gc'], name='Golden Cross',
                   opacity=0.5, mode='markers', marker={'size':15, 'color':'purple'}),
                   #デッドクロス
                   go.Scatter(yaxis='y1', x=df.index, y=df['dc'], name='Dead Cross',
                   opacity=0.8, mode='markers', marker={'size':15, 'color':'black', 'symbol':'x'}),
                   #ボリンジャーバンド
                   go.Scatter(yaxis='y1', x=df.index, y=df['uuper2'], name='',
                               line={'color':'lavender', 'width':0}),
                   go.Scatter(yaxis='y1', x=df.index, y=df['lower2'], name='BB',
                               line={'color':'lavender', 'width':0},
                               fill='tonexty', fillcolor='rgba(170,170,170,.2)'),
                   #MACD
                   go.Scatter(yaxis='y3', x=df.index, y=df['macd'],
                              name='macd', line={'color': 'magenta', 'width':1}),
                   go.Scatter(yaxis='y3', x=df.index, y=df['macd_signal'],
                              name='signal', line={'color': 'green', 'width':1}),
                   go.Bar(yaxis='y3', x=df.index, y=df['hist'],
                              name='histgram', marker={'color': 'slategray'}),
                   #RSI
                   go.Scatter(yaxis='y4', x=df.index, y=df['rsi14'],
                              name='RSI14', line={'color': 'magenta', 'width':1}),
                   go.Scatter(yaxis='y4', x=df.index, y=df['rsi28'],
                              name='RSI28', line={'color': 'green', 'width': 1}),
                   #補助線
                   go.Scatter(yaxis='y4', x=df.index, y=df['30'],
                              name='30', line={'color': 'black', 'width':0.5}),
                   go.Scatter(yaxis='y4', x=df.index, y=df['70'],
                              name='70', line={'color': 'black', 'width': 0.5}),
                   #スキャスティクス
                   go.Scatter(yaxis='y5', x=df.index, y=df['slowK'],
                              name='slowK', line={'color': 'magenta', 'width':1}),
                   go.Scatter(yaxis='y5', x=df.index, y=df['slowD'],
                              name='slowD', line={'color': 'green', 'width': 1}),
                   #補助線
                   go.Scatter(yaxis='y5', x=df.index, y=df['20'],
                              name='20', line={'color': 'black', 'width':0.5}),
                   go.Scatter(yaxis='y5', x=df.index, y=df['80'],
                              name='80', line={'color': 'black', 'width': 0.5}),
                   #出来高
                   go.Bar(yaxis='y6', x=df.index, y=df['Volume'], name='Volume',
                          marker={'color': 'slategray'})
]

#グラフの描画
fig = go.Figure(data=data, layout=go.Layout(layout))

#日付のレイアウトをチューニング
fig.update_layout({
    'xaxis':{
        #日付を1/10で表示する
        'tickvals':df.index[::10]
    }
})

#表示
fig.show()

#チャートの保存
# fig.write_image('chart_data/{}_{}_{}.jpg'.format(dt.date.today(), brand_name, code), engine="kaleido")
fig.write_html('chart_data/{}_{}_{}.html'.format(dt.date.today(), brand_name, code))