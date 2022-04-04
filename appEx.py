import json, os.path
import math
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.exceptions import *
from binance.enums import *
from appConfig import binanceAPIConfig,discordWebhookConfig,flaskConfig

client = Client(binanceAPIConfig.API_KEY, binanceAPIConfig.API_SECRET)
app = Flask(__name__)
app.config.from_object(flaskConfig.Config)
app.config['SQLACHEMY_DATABASE_URL'] = ''
app.config['SQLACHEMY_TRACK_MODIFICATIONS'] = False

# -------------------DB-------------------------



# -------------------SETUP----------------------

class TimeFrameData:
    def __init__(self, pair, green, red, blue, white):
        self.pair = pair
        self.white = white
        self.blue = blue
        self.red = red
        self.green = green


class TradeData:
    def __init__(self, pos, price, pos_price, leverage,captured_price_movement, win, loss, symbol,precision,tradeMode):
        self.precision = precision
        self.symbol = symbol
        self.price = price
        self.loss = loss
        self.win = win
        self.captured_price_movement = captured_price_movement
        self.leverage = leverage
        self.pos_price = pos_price
        self.pos = pos
        self.tradeMode = tradeMode


trading_leverage = 4
total_pair = 2
each_share = 0.49

version = "Beta v0.4"
pair1 = "BTC/USDT|ST"
pair2 = "ADA/USDT|ST"
pair_list = [pair1,pair2]
password = "123"

btc_st_entry_tf_list = []
btc_st_compass_tf_list = []
btc_trade_data = []

ada_st_entry_tf_list = []
ada_st_compass_tf_list = []
ada_trade_data = []

for i in range(4):
    btc_st_entry_tf_list.append(TimeFrameData(pair1, None, None, None, None, None))
    btc_st_compass_tf_list.append(TimeFrameData(pair1, None, None, None, None, None))
    ada_st_entry_tf_list.append(TimeFrameData(pair2, None, None, None, None, None))
    ada_st_compass_tf_list.append(TimeFrameData(pair2, None, None, None, None, None))


for i in range(3):
    btc_trade_data.append(TradeData(None, None, None,trading_leverage, 0, 0, 0,'btcusdt',3,False))
    ada_trade_data.append(TradeData(None, None, None,trading_leverage, 0, 0, 0,'adausdt',0,False))

discordWebhookConfig.debug_hook.send("```TradingAlgo -{} Successfully Deploy!!\nBy default trade trigger will be set to 0```".format(version))

# ----------------------------------------UPDATE ARRAY----------------------------------------

def roundStringToDecimal(string, decimal_places):
    return round(float(string), decimal_places)


def updateData(tf_data,trade_data):
    dataList = json.loads(request.data)
    if dataList['Password'] != password:
        return {
            'Error': 'ERROR_PASSWORD'
        }

    trade_data.price = float(dataList['Price'])
    tf_data.green = roundStringToDecimal(dataList['G'], 2)
    tf_data.red = roundStringToDecimal(dataList['R'], 2)
    tf_data.blue = roundStringToDecimal(dataList['B'], 2)
    tf_data.white = roundStringToDecimal(dataList['W'], 2)
    return {
        'Error': 'ERROR_OK'
    }
# ----------------------------------------Communication----------------------------------------
def discordUpdate(pair,data):
    if data.win + data.loss == 0:
        discordWebhookConfig.trading_signal_hook.send("```"
                  "%s\n"
                  "Pair: %s \n"
                  "Position Update: %s \n"
                  "Current price: %f\n"
                  "Captured Movement: %f\n"
                  "Win Rate: %f\n"
                  "```" % (version,pair, data.pos, data.price,data.captured_price_movement,0))
        return 0
    discordWebhookConfig.trading_signal_hook.send("```"
              "%s \n"
              "Pair: %s \n"
              "Position Update: %s \n"
              "Current price: %f\n"
              "Captured Movement: %f\n"
              "Win Rate: %f\n"
              "```"% (version,pair, data.pos, data.price,data.captured_price_movement,data.win/(data.win + data.loss)))
    return 0
# ----------------------------------------BINANCE API----------------------------------------

def openPositionOnFuture(symbol,side,trade_type,precision):
    accountInfo = client.futures_account()
    posInfo = client.futures_position_information(symbol = symbol)[0]
    usd = float(accountInfo['totalWalletBalance']) - float(accountInfo['totalUnrealizedProfit'])
    quantity = abs(float(posInfo['positionAmt']))
    price = float(posInfo['markPrice'])
    freeBalance = float(accountInfo["totalCrossWalletBalance"])
    changeLeverage(symbol, trading_leverage)
    if quantity != 0:
        try:
            client.futures_create_order(symbol=symbol,
                                        side=side,
                                        type=trade_type,
                                        quantity=quantity)
            discordWebhookConfig.trading_signal_hook.send("Successfully | CLOSE | %s | Quantity-> %f" %(symbol,quantity))
        except Exception as e:
            discordWebhookConfig.trading_signal_hook.send("Failed | CLOSE | %s | Quantity-> %f: %s" %(symbol,quantity,e))

    # margin_type = "ISOLATED"
    quantity = (usd/price) * trading_leverage * each_share
    quantity = (math.floor(quantity * 10 ** precision) / 10 ** precision)
    if precision == 0:
        quantity = int(quantity)
    try:
        # changeMarginType(symbol, margin_type)
        client.futures_create_order(symbol=symbol,
                                    side=side,
                                    type=trade_type,
                                    quantity=quantity)
        discordWebhookConfig.trading_signal_hook.send("Successfully | %s | %s | Quantity-> %f" %(side,symbol,quantity))
    except Exception as e:
        try:
            discordWebhookConfig.trading_signal_hook.send("OPEN %s position FAILED :%s, Changing Calculation Method!" % (symbol , e))
            quantity = (math.floor(((freeBalance*0.9)/price) * 10 ** precision) / 10 ** precision) * trading_leverage
            if precision == 0:
                quantity = int(quantity)
            client.futures_create_order(symbol=symbol,
                                        side=side,
                                        type=trade_type,
                                        quantity=quantity)
            discordWebhookConfig.trading_signal_hook.send("AutoFix Successfully | %s | %s | Quantity-> %f" %(side,symbol,quantity))
        except Exception as e:
            discordWebhookConfig.trading_signal_hook.send("Final: OPEN %s position FAILED %s" % (symbol , e))


def changeMarginType(symbol, margin_type):
    client.futures_change_margin_type(symbol=symbol,marginType= margin_type)

def changeLeverage(symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol,
                                               leverage= leverage)
    except Exception as e:
        discordWebhookConfig.debug_hook.send("change %s leverage failed %s" % (symbol , e))

def isPositionOpenAtSymbol(symbol):
    try:
        if float(client.futures_position_information(symbol ="adausdt")[0]['positionAmt']) != 0:
            return True
        else:
            return False
    except Exception as e:
        discordWebhookConfig.debug_hook.send("ERROR isPositionOpenAtSymbol %s" %symbol)
        return True


# ----------------------------------------ALGO---------------------------------------------

def isGoodShortEntry(time_frame_data):
    for tf_data in time_frame_data:
        if tf_data.white > 50:
            return False
    return True

def isGoodLongEntry(time_frame_data):
    for tf_data in time_frame_data:
        if tf_data.white < 50:
            return False
    return True

def isUpwardPressure(compass_tf_data):
    upward_tf = 0
    downward_tf = 0
    counter = 0

    for tf_data in compass_tf_data:
        if tf_data.white >= 50 and tf_data.red >= 50:
            upward_tf = counter

        if tf_data.white <= 50 and tf_data.red <= 50:
            downward_tf = counter
        counter += 1

    if upward_tf > downward_tf:
        return True
    elif downward_tf < upward_tf:
        return False

def updatePosition(tf):

    entry_tf_list = []
    compass_tf_list = []
    temp_data = TradeData(None,None,None,None,None,None,None,None,None,None)
    if tf.pair == pair1:
        entry_tf_list = btc_st_entry_tf_list
        compass_tf_list = btc_st_compass_tf_list
        temp_data = btc_trade_data[0]
    elif tf.pair == pair2:
        entry_tf_list = ada_st_entry_tf_list
        compass_tf_list = ada_st_compass_tf_list
        temp_data = ada_trade_data[0]

    for data in entry_tf_list:
        if data.white is None:
            return {'Error': 'ERROR_NOT_ENOUGH_INFO'}

    for data in compass_tf_list:
        if data.white is None:
            return {'Error': 'ERROR_NOT_ENOUGH_INFO'}

    if isUpwardPressure(compass_tf_list) and isGoodLongEntry(entry_tf_list):
        if temp_data.pos != "L":
            # not the first trade
            if temp_data.pos_price is not None:
                temp_data.captured_price_movement += (temp_data.pos_price - temp_data.price) / temp_data.pos_price
                if (temp_data.price - temp_data.pos_price) < 0:
                    temp_data.win = 1
                else:
                    temp_data.loss = 1

            # flip position
            if temp_data.tradeMode:
                openPositionOnFuture(temp_data.symbol,SIDE_BUY,ORDER_TYPE_MARKET,temp_data.precision)
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(temp_data.symbol))
            temp_data.pos_price = temp_data.price
            temp_data.pos = "L"
            discordUpdate(tf.pair,temp_data)

    if not isUpwardPressure(compass_tf_list) and isGoodShortEntry(entry_tf_list):
        if temp_data.pos != "S":

            if temp_data.pos_price is not None:
                temp_data.captured_price_movement += (temp_data.price - temp_data.pos_price) / temp_data.pos_price
                if (temp_data.price - temp_data.pos_price) > 0:
                    temp_data.win = 1
                else:
                    temp_data.loss = 1
             # flip position
            if temp_data.tradeMode:
                openPositionOnFuture(temp_data.symbol,SIDE_SELL,ORDER_TYPE_MARKET,temp_data.precision)
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(temp_data.symbol))
            temp_data.pos_price = temp_data.price
            temp_data.pos = "S"
            discordUpdate(tf.pair,temp_data)

    if tf.pair == pair1:
        btc_trade_data[0].pos = temp_data.pos
        btc_trade_data[0].pos_price = temp_data.pos_price
        btc_trade_data[0].captured_price_movement = temp_data.captured_price_movement
        btc_trade_data[0].win = temp_data.win
        btc_trade_data[0].loss = temp_data.loss
    if tf.pair == pair2:
        ada_trade_data[0].pos = temp_data.pos
        ada_trade_data[0].pos_price = temp_data.pos_price
        ada_trade_data[0].captured_price_movement = temp_data.captured_price_movement
        ada_trade_data[0].win = temp_data.win
        ada_trade_data[0].loss = temp_data.loss
    return {
        'Error': 'ERROR_OK'
    }

# ----------------------------------------WebPage---------------------------------------------


# @app.route('/test')
# def test():
#     return {
#         'test': client.futures_account()['totalCrossWalletBalance']
#     }
@app.route('/')
def home1():
    return render_template("index.html", page = "HOME" , pair_list = pair_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return routes.login()

@app.route('/collections')
def collection():
    return render_template('collections.html')

@app.route('/binance/balance')
def getBinanceFutureBalance():
    return {
        "Asset": client.futures_account()['assets'][0]['asset'],
        "Unrealized Profit": client.futures_account()["totalUnrealizedProfit"],
        "Total Wallet Balance": client.futures_account()["totalWalletBalance"],
        "Available Balance": client.futures_account()['availableBalance']
    }


@app.route('/debug', methods=['GET'])
def debug():
    return {
        'BTC_E_1' :btc_st_entry_tf_list[0].green,
        'BTC_E_2' :btc_st_entry_tf_list[1].green,
        'BTC_E_3' :btc_st_entry_tf_list[2].green,
        'BTC_E_4' :btc_st_entry_tf_list[3].green,
        'BTC_C_1' :btc_st_compass_tf_list[0].green,
        'BTC_C_2' :btc_st_compass_tf_list[1].green,
        'BTC_C_3' :btc_st_compass_tf_list[2].green,
        'BTC_C_4' :btc_st_compass_tf_list[3].green,

        'ADA_E_1' :ada_st_entry_tf_list[0].green,
        'ADA_E_2' :ada_st_entry_tf_list[1].green,
        'ADA_E_3' :ada_st_entry_tf_list[2].green,
        'ADA_E_4' :ada_st_entry_tf_list[3].green,
        'ADA_C_1' :ada_st_compass_tf_list[0].green,
        'ADA_C_2' :ada_st_compass_tf_list[1].green,
        'ADA_C_3' :ada_st_compass_tf_list[2].green,
        'ADA_C_4' :ada_st_compass_tf_list[3].green,
    }

@app.route('/tradeMode', methods=['GET', 'POST'])
def tradeMode():
    dataList = json.loads(request.data)
    if dataList['pair'] == 'btcusdtst':
        btc_trade_data[0].tradeMode = dataList['tradeMode']
    if dataList['pair'] == 'adausdtst':
        ada_trade_data[0].tradeMode = dataList['tradeMode']

    discordWebhookConfig.debug_hook.send("%s trigger set to %d " % (dataList['pair'] , dataList['tradeMode']))
    return {
        'btc': btc_trade_data[0].tradeMode,
        'ada': ada_trade_data[0].tradeMode
    }
# ----------------------------------------WebHook---------------------------------------------
# ----------------------------------------BTC/USD---------------------------------------------
@app.route('/BTCUSD/6', methods=['POST'])
def st_btc_e1():
    response = updateData(btc_st_entry_tf_list[0],btc_trade_data[0])
    if updatePosition(btc_st_entry_tf_list[0])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_entry_tf_list[0])

    return response


@app.route('/BTCUSD/12', methods=['POST'])
def st_btc_e2():
    response = updateData(btc_st_entry_tf_list[1],btc_trade_data[0])
    if updatePosition(btc_st_entry_tf_list[1])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_entry_tf_list[1])
    return response


@app.route('/BTCUSD/23', methods=['POST'])
def st_btc_e3():
    response = updateData(btc_st_entry_tf_list[2],btc_trade_data[0])
    if updatePosition(btc_st_entry_tf_list[2])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_entry_tf_list[2])
    return response

@app.route('/BTCUSD/45', methods=['POST'])
def st_btc_e4():
    response = updateData(btc_st_entry_tf_list[3],btc_trade_data[0])
    if updatePosition(btc_st_entry_tf_list[3])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_entry_tf_list[3])
    return response


@app.route('/BTCUSD/90', methods=['POST'])
def st_btc_c1():
    response = updateData(btc_st_compass_tf_list[0],btc_trade_data[0])
    if updatePosition(btc_st_compass_tf_list[0])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_compass_tf_list[0])
    return response

@app.route('/BTCUSD/3h', methods=['POST'])
def st_btc_c2():
    response = updateData(btc_st_compass_tf_list[1],btc_trade_data[0])
    if updatePosition(btc_st_compass_tf_list[1])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_compass_tf_list[1])
    return response


@app.route('/BTCUSD/6h', methods=['POST'])
def st_btc_c3():
    response = updateData(btc_st_compass_tf_list[2],btc_trade_data[0])
    if updatePosition(btc_st_compass_tf_list[2])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_compass_tf_list[2])
    return response


@app.route('/BTCUSD/12h', methods=['POST'])
def st_btc_c4():
    response = updateData(btc_st_compass_tf_list[3],btc_trade_data[0])
    if updatePosition(btc_st_compass_tf_list[3])['Error'] != "ERROR_OK":
        return updatePosition(btc_st_compass_tf_list[3])
    return response
# -------------------------------ADA/USD------------------------------------
@app.route('/ADAUSD/6', methods=['POST'])
def st_ada_e1():
    response = updateData(ada_st_entry_tf_list[0],ada_trade_data[0])
    if updatePosition(ada_st_entry_tf_list[0])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_entry_tf_list[0])

    return response


@app.route('/ADAUSD/12', methods=['POST'])
def st_ada_e2():
    response = updateData(ada_st_entry_tf_list[1],ada_trade_data[0])
    if updatePosition(ada_st_entry_tf_list[1])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_entry_tf_list[1])
    return response


@app.route('/ADAUSD/23', methods=['POST'])
def st_ada_e3():
    response = updateData(ada_st_entry_tf_list[2], ada_trade_data[0])
    if updatePosition(ada_st_entry_tf_list[2])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_entry_tf_list[2])
    return response

@app.route('/ADAUSD/45', methods=['POST'])
def st_ada_e4():
    response = updateData(ada_st_entry_tf_list[3], ada_trade_data[0])
    if updatePosition(ada_st_entry_tf_list[3])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_entry_tf_list[3])
    return response


@app.route('/ADAUSD/90', methods=['POST'])
def st_ada_c1():
    response = updateData(ada_st_compass_tf_list[0], ada_trade_data[0])
    if updatePosition(ada_st_compass_tf_list[0])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_compass_tf_list[0])
    return response

@app.route('/ADAUSD/3h', methods=['POST'])
def st_ada_c2():
    response = updateData(ada_st_compass_tf_list[1], ada_trade_data[0])
    if updatePosition(ada_st_compass_tf_list[1])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_compass_tf_list[1])
    return response


@app.route('/ADAUSD/6h', methods=['POST'])
def st_ada_c3():
    response = updateData(ada_st_compass_tf_list[2], ada_trade_data[0])
    if updatePosition(ada_st_compass_tf_list[2])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_compass_tf_list[2])
    return response


@app.route('/ADAUSD/12h', methods=['POST'])
def st_ada_c4():
    response = updateData(ada_st_compass_tf_list[3], ada_trade_data[0])
    if updatePosition(ada_st_compass_tf_list[3])['Error'] != "ERROR_OK":
        return updatePosition(ada_st_compass_tf_list[3])
    return response
