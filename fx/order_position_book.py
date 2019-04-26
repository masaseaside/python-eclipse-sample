# ==============================================================================
# brief        ローソク足チャートの描写
#
# author       たっきん
#
# 事前準備 :
#     oandapyV20のインストール (pip install oandapyV20)
#     Bokehのインストール（conda install bokeh）
# ==============================================================================

import copy
import datetime
from math import pi
import json
from bokeh.layouts import Column
from bokeh.models import RangeTool
from bokeh.plotting import figure, show, output_file
from oandapyV20 import API
from bokeh.layouts import gridplot

from bokehlib import bokeh_common as bc
from fx import oanda_common as oc
from fx import your_account as ya
import oandapyV20.endpoints.instruments as instruments
import pandas as pd


class OrderBook(object):
    """ OrderBook - オーダーブック定義クラス。"""

    def __init__(self, granularity):
        """"コンストラクタ
        引数:
            dt (str): datetime formatted by DT_FMT.
        戻り値:
            tf_dt (str): changed datetime.
        """

        self.__ORDERBOOK = "orderBook"
        self.__BUCKETS = "buckets"
        self.__PRICE = "price"
        self.__LONG = "longCountPercent"
        self.__SHORT = "shortCountPercent"

        self.__TIME = "time"
        self.__CUR_PRICE = "price"
        self.__BUCKET_WIDTH = "bucketWidth"

        self.__WIDE = 12 * 60 * 60 * 1000  # half day in ms
        self.__WIDE_SCALE = 0.2

        self.__DT_FMT = "%Y-%m-%dT%H:%M:00Z"
        self.__GRANULARITY = granularity

        self.__CUT_TH = 50  # 現レートから上下何本残すか
        self.__X_AXIS_MAX = 2.5  # X軸レンジ

        self.__BG_COLOR = "#2e2e2e"

        self.__df = []
        self.__hbar_height = 0
        self.__cur_price = 0

        self.__api = API(access_token=ya.access_token,
                         environment=oc.OandaEnv.PRACTICE)

    def getInstrumentsOrderBook(self, instrument, dt):

        params = {
            "time": dt.strftime(self.__DT_FMT),
        }

        # APIへ過去データをリクエスト
        ic = instruments.InstrumentsOrderBook(instrument=instrument,
                                              params=params)
        self.__api.request(ic)

        self.__data = []
        for raw in ic.response[self.__ORDERBOOK][self.__BUCKETS]:
            self.__data.append([float(raw[self.__PRICE]),
                                float(raw[self.__LONG]),
                                float(raw[self.__SHORT])])

        # リストからデータフレームへ変換
        df = pd.DataFrame(self.__data)
        df.columns = [self.__PRICE,
                      self.__LONG,
                      self.__SHORT]
        df = df.set_index(self.__PRICE).sort_index(ascending=False)
        # date型を整形する
        time = pd.to_datetime(self.__changeDateTimeFmt(ic.response[self.__ORDERBOOK][self.__TIME]))
        cur_price = float(ic.response[self.__ORDERBOOK][self.__CUR_PRICE])
        bucket_width = float(ic.response[self.__ORDERBOOK][self.__BUCKET_WIDTH])

        print(time)
        print(cur_price)
        idx_th = bucket_width * self.__CUT_TH
        self.__df = df[(df.index > cur_price - idx_th) & (df.index < cur_price + idx_th)]
        self.__hbar_height = bucket_width
        self.__cur_price = cur_price

    def drawOrderBook(self, fig_width=500):

        df = copy.copy(self.__df)

        set_tools = bc.ToolType.gen_str(bc.ToolType.XPAN,
                                        bc.ToolType.WHEEL_ZOOM,
                                        bc.ToolType.BOX_ZOOM,
                                        bc.ToolType.RESET,
                                        bc.ToolType.SAVE)

        # --------------- メインfigure ---------------
        plt1 = figure(
            plot_height=500,
            plot_width=fig_width,
            x_range=(-self.__X_AXIS_MAX, self.__X_AXIS_MAX),
            tools=set_tools,
            title="Order Book example",
            background_fill_color=self.__BG_COLOR
        )
        plt1.grid.grid_line_alpha = 0.3

        print(df)

        #df[(df.index > cur_price - idx_th) & (df.index < cur_price + idx_th)]

        print("aaaaaaaaaaaaaa")
        df_up = df[self.__LONG][(df.index > self.__cur_price)]
        df_lo = -df[self.__SHORT][(df.index < self.__cur_price)]
        df_right = pd.concat([df_up, df_lo])
        print(df_right)

        df_up = -df[self.__SHORT][(df.index > self.__cur_price)]
        df_lo = df[self.__LONG][(df.index < self.__cur_price)]
        df_left = pd.concat([df_up, df_lo])
        print(df_left)

        plt1.hbar(y=df.index, height=0.03, left=df_right, right=0, color="#00A4BD")
        plt1.hbar(y=df.index, height=0.03, left=df_left, right=0, color="#FF8400")
        plt1.line(x=[-self.__X_AXIS_MAX, self.__X_AXIS_MAX],
                 y=[self.__cur_price, self.__cur_price],
                 color="#7DA900", line_width=3)

        # make a grid
        grid = gridplot([[None, plt1]])

        show(grid)


    def __changeDateTimeFmt(self, dt):
        """"日付フォーマットの変換メソッド
        引数:
            dt (str): DT_FMT形式でフォーマットされた日付
        戻り値:
            tf_dt (str): 変換後の日付
        """
        tdt = datetime.datetime.strptime(dt, self.__DT_FMT)

        return tdt


if __name__ == "__main__":
    cs = OrderBook(oc.OandaGrn.D)

    instrument = oc.OandaIns.USD_JPY

    dt = datetime.datetime(year=2017, month=2, day=1, hour=12, minute=0, second=0)
    cs.getInstrumentsOrderBook(instrument, dt)
    cs.drawOrderBook()
