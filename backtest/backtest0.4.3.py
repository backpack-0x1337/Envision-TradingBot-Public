from os import path
from time import sleep

import pandas as pd
import matplotlib.pyplot as plt

class Backtest:

    def __init__(self, start_time, end_time, time_frame_paths, win, loss):
        self.loss = loss
        self.win = win
        self.time_frame_paths = time_frame_paths
        self.end_time = end_time
        self.start_time = start_time

    # ------------------------------------------------------GET------------------------------------------------------
    def getLose(self):
        return self.loss

    def getWin(self):
        return self.win

    def getStartTime(self):
        return self.start_time

    def getEndTime(self):
        return self.end_time

    # ------------------------------------------------------CLASS FUNCTION----------------------------------------------
    def getProfitPercentage(self):
        return (self.getWin()) / (self.getWin() + self.getLose())

    def getTotalTime(self):
        return self.getEndTime() - self.getStartTime()


# ------------------------------------------------------CLASS FUNCTION----------------------------------------------

pair = 'BTCUSDT'
# return the file path for the given timeframe
def getFilePathByTimeFrame(time_frame):
    return "./backtest_data/BINANCE_%s, %s.csv" % (pair,time_frame)


# validate path accessibility
def validate_path(f_path):
    if not path.exists(f_path):
        print("path not found")
        return False
    return True


# return array which contain file paths
def getPathArray():
    testing_time_frame = ["6", "12", "24", "48", "96", "192", "384", "768"]
    temp_path_array = []
    # get time frame from testing time frame group and load file path to our class
    for tf in testing_time_frame:
        temp_path_array.append(getFilePathByTimeFrame(tf))
    for f_path in temp_path_array:
        if not validate_path(f_path):
            print("%s not found, terminating program" % f_path)
            exit(1)

    return temp_path_array


class TimeFrameData:
    def __init__(self, time, green, red, blue, white):
        self.white = white
        self.blue = blue
        self.red = red
        self.green = green
        self.time = time


def isGoodShortEntry(entry_time_frame_data):
    for tf_data in entry_time_frame_data:
        if tf_data.white > 50:
            return False
    return True


def isGoodLongEntry(entry_time_frame_data):
    for tf_data in entry_time_frame_data:
        if tf_data.white < 50:
            return False
    return True

def isModeCorrection(compass_time_frame_data,mode):
    counter = 0
    for tf_data in compass_time_frame_data:

        if tf_data.white > 50 and mode == 'U':
            counter += 1
        if tf_data.white < 50 and mode == 'D':
            counter += 1

    if counter >= 3:
        return True
    return False

def isUpwardPressure(compass_time_frame_data):
    upward_tf = 0
    downward_tf = 0
    counter = 0

    for tf_data in compass_time_frame_data:
        if tf_data.red >= 50 and tf_data.white >= 50:
            upward_tf = counter
        if tf_data.red <= 50 and tf_data.white <= 50:
            downward_tf = counter
        counter += 1

    if upward_tf > downward_tf:
        return True

    if downward_tf == upward_tf:
        return isModeCorrection(compass_time_frame_data,'U')
    return False


def isDownwardPressure(compass_time_frame_data):
    upward_tf = 0
    downward_tf = 0
    counter = 0
    for tf_data in compass_time_frame_data:
        if tf_data.red >= 50 and tf_data.white >= 50:
            upward_tf = counter

        if tf_data.red <= 50 and tf_data.white <= 50:
            downward_tf = counter
        counter += 1

    if downward_tf > upward_tf:
        return True

    if downward_tf == upward_tf:
        return isModeCorrection(compass_time_frame_data,'D')

    return False


# Error 1 file not found
def main():
    btc = Backtest(1609459200, 1615639680, getPathArray(), 0, 0)

    time = 1609459200

    chart_data_list = [TimeFrameData(time, None, None, None, None), TimeFrameData(time, None, None, None, None),
                       TimeFrameData(time, None, None, None, None), TimeFrameData(time, None, None, None, None),
                       TimeFrameData(time, None, None, None, None), TimeFrameData(time, None, None, None, None),
                       TimeFrameData(time, None, None, None, None), TimeFrameData(time, None, None, None, None)]

    # load dataframe
    chart_csv = []
    for f_path in btc.time_frame_paths:
        chart_csv.append(pd.read_csv(f_path))

    pos = "N"
    pos_price = -1
    init_invest = 1000
    leverage = 3
    max_down = 0
    max_up = 0
    profit_percent = 0
    win = 0
    loss = 0
    tradeNo = 1
    fee = 0.005
    tradeno_array = []
    account_balance_array = []
    price_array = []
    entry_time_frame_data = chart_data_list[:4]
    compass_time_frame_data = chart_data_list[4:]

    while chart_data_list[0].time < btc.end_time:

        total_entry_time_frame = 8
        for i in range(total_entry_time_frame):
            chart_data_list[i].green = \
                (chart_csv[i].loc[chart_csv[i].time == chart_data_list[i].time])['Green Line'].values[0]
            chart_data_list[i].red = (chart_csv[i].loc[chart_csv[i].time == chart_data_list[i].time])['Red RSI'].values[
                0]
            chart_data_list[i].blue = (chart_csv[i].loc[chart_csv[i].time == chart_data_list[i].time])['LSMA'].values[0]
            chart_data_list[i].white = \
                (chart_csv[i].loc[chart_csv[i].time == chart_data_list[i].time])['Energy'].values[0]

        price = (chart_csv[0].loc[chart_csv[0].time == chart_data_list[0].time])['close'].values[0]
        # -------------------------------------------------ALGO----------------------------------------------------------

        if isUpwardPressure(compass_time_frame_data) :
            if pos != "L" and isGoodLongEntry(entry_time_frame_data):
                if pos_price != -1:
                    profit_percent += (pos_price - price) / pos_price
                    # max draw
                    if ((pos_price - price) / pos_price) > 0 and ((pos_price - price) / pos_price) > max_up:
                        max_up = (pos_price - price) / pos_price
                    elif ((pos_price - price) / pos_price) < 0 and ((pos_price - price) / pos_price) < max_down:
                        max_down = (pos_price - price) / pos_price
                    init_invest = init_invest * (1 - fee)
                    init_invest += init_invest * (((pos_price - price) / pos_price) * leverage)
                    print("tradeNo = {} LastPos = {}, profit = {}, Account balance = {}, UnixTime = {}"
                          .format(tradeNo, pos, (pos_price - price) / pos_price, init_invest, chart_data_list[0].time))
                    tradeno_array.append(tradeNo)
                    account_balance_array.append(init_invest)
                    price_array.append(price)
                    tradeNo += 1

                if (price - pos_price) < 0:
                    win += 1
                else:
                    loss += 1
                pos = "L"
                pos_price = price

        elif isDownwardPressure(compass_time_frame_data) :
            if pos != "S" and isGoodShortEntry(entry_time_frame_data) :
                if pos_price != -1:
                    profit_percent += (price - pos_price) / pos_price
                    # max draw
                    if ((price - pos_price) / pos_price) > 0 and ((price - pos_price) / pos_price) > max_up:
                        max_up = (price - pos_price) / pos_price
                    elif ((price - pos_price) / pos_price) < 0 and ((price - pos_price) / pos_price) < max_down:
                        max_down = (price - pos_price) / pos_price
                    init_invest = init_invest * (1 - fee)
                    init_invest += init_invest * (((price - pos_price) / pos_price) * leverage)
                    print("tradeNo = {} LastPos = {}, profit = {}, Account balance = {}, UnixTime = {}"
                          .format(tradeNo, pos, (price - pos_price) / pos_price, init_invest, chart_data_list[0].time))
                    tradeno_array.append(tradeNo)
                    account_balance_array.append(init_invest)
                    price_array.append(price)
                    tradeNo += 1

                if (price - pos_price) > 0:
                    win += 1
                else:
                    loss += 1
                pos = "S"
                pos_price = price

        # for compass time frame if upward pressure
        # if lower time frame

        chart_data_list[0].time = chart_csv[0].iloc[
            (chart_csv[0].loc[chart_csv[0].time == chart_data_list[0].time].index.values[0]) + 1].time
        for i in range(7):
            # i + 1 because we want to start from the second index
            if chart_data_list[0].time >= \
                    chart_csv[i + 1].iloc[(chart_csv[i + 1].loc[chart_csv[i + 1].time ==
                                                                chart_data_list[i + 1].time].index.values[0]) + 1].time:
                chart_data_list[i + 1].time = \
                    chart_csv[i + 1].iloc[(chart_csv[i + 1].loc[chart_csv[i + 1].time ==
                                                                chart_data_list[i + 1].time].index.values[0]) + 1].time
    total_trade = win + loss
    win_rate = win / total_trade
    print("Final Result")
    print("Leverage = %s" % leverage)
    print("Win rate = %s" % win_rate)
    print("max up = %f" % max_up)
    print("max down = %f" % max_down)
    plt.plot(tradeno_array, price_array, label= "{} price".format(pair))
    plt.plot(tradeno_array, account_balance_array, label= "Account Balance")

    # naming the x axis
    plt.xlabel('No. trades')

    # naming the y axis
    plt.ylabel('Balance')

    # giving a title to my graph
    plt.title(pair)
    plt.legend()
    # function to show the plot
    plt.show()

if __name__ == '__main__':
    main()
