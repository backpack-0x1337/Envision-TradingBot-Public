from appConfig.discordWebhookConfig import debug_hook
from util.convertors import roundStringToDecimal
from exchanger.binance import get_wallet_balance

# Update Data Base R G B W
def update_timeframe_data(received_datas, timeframe_data):
    timeframe_data.green = roundStringToDecimal(received_datas['G'], 2)
    timeframe_data.red = roundStringToDecimal(received_datas['R'], 2)
    timeframe_data.blue = roundStringToDecimal(received_datas['B'], 2)
    timeframe_data.white = roundStringToDecimal(received_datas['W'], 2)
    timeframe_data.price = float(received_datas['Price'])


def update_database(received_datas, TimeFrameData, TradingGroupData, db, version, Stats, Trades):
    pair = received_datas['Pair']
    timeframe = received_datas['TF']
    found_version_stat = Stats.query.filter_by(version=version).first()
    found_tf_dataframe = TimeFrameData.query.filter_by(pair=pair, timeframe=timeframe).first()
    found_pair_dataframe = TradingGroupData.query.filter_by(pair=pair).first()
    found_trade = Trades.query.first()
    if not found_trade:
        new_trade_info = Trades(0, "0", pair, float(get_wallet_balance()))
        db.session.add(new_trade_info)
        db.session.commit()
    # 如果沒有找到已經存在的時間段數據
    if not found_version_stat:
        new_version_stat = Stats(0, 0, version)
        found_version_stat = new_version_stat
        db.session.add(found_version_stat)
        db.session.commit()
        debug_hook.send("Created new version Stats: %s" % version)
    if not found_tf_dataframe:
        new_tf_dataframe = TimeFrameData(None, None, None, None, pair=pair, timeframe=timeframe)
        found_tf_dataframe = new_tf_dataframe
        db.session.add(found_tf_dataframe)
        db.session.commit()
        debug_hook.send("Created new timeframe dataframe for pair: %s TimeFrame: %s" % (pair, timeframe))
    if not found_pair_dataframe:
        new_pair_dataframe = TradingGroupData(precision=None, trading_symbol=None, price=None, loss=0, win=0,
                                              captured_price_movement=0, leverage=None, pos_price=None,
                                              pos='N', trade_trigger=False, pair=pair, trade_percent=None)
        default_leverage = 3
        if pair == 'BTCUSDT':
            new_pair_dataframe.precision = 3

        elif pair == 'ADAUSDT':
            new_pair_dataframe.precision = 0

        elif pair == 'LINKUSDT':
            new_pair_dataframe.precision = 2

        elif pair == 'BNBUSDT':
            new_pair_dataframe.precision = 2

        elif pair == 'SOLUSDT':
            new_pair_dataframe.precision = 0

        elif pair == 'ENJUSDT':
            new_pair_dataframe.precision = 0

        elif pair == 'ETHUSDT':
            new_pair_dataframe.precision = 3

        elif pair == 'THETAUSDT':
            new_pair_dataframe.precision = 1

        elif pair == 'FILUSDT':
            new_pair_dataframe.precision = 2

        elif pair == 'CAKEUSDT':
            new_pair_dataframe.precision = 3

        elif pair == 'AAVEUSDT':
            new_pair_dataframe.precision = 1

        elif pair == 'LUNAUSDT':
            new_pair_dataframe.precision = 3

        elif pair == 'UNIUSDT':
            new_pair_dataframe.precision = 2

        elif pair == 'SUSHIUSDT':
            new_pair_dataframe.precision = 0

        elif pair == 'KSMUSDT':
            new_pair_dataframe.precision = 1

        elif pair == 'DOTUSDT':
            new_pair_dataframe.precision = 1

        elif pair == 'LTCUSDT':
            new_pair_dataframe.precision = 3

        elif pair == 'XRPUSDT':
            new_pair_dataframe.precision = 1

        elif pair == 'XLMUSDT':
            new_pair_dataframe.precision = 0

        elif pair == 'VETUSDT':
            new_pair_dataframe.precision = 0

        elif pair == 'DOGEUSDT':
            new_pair_dataframe.precision = 0

        else:
            debug_hook.send("ERROR_PAIR_NOT_SUPPORT %s" % pair)
            return {'Error': 'ERROR_INVALID_PAIR'}

        new_pair_dataframe.leverage = default_leverage
        new_pair_dataframe.trading_symbol = pair.lower()
        found_pair_dataframe = new_pair_dataframe
        db.session.add(found_pair_dataframe)
        db.session.commit()
        debug_hook.send("Created new pair dataframe for pair: %s" % pair)
    # 如果找到數據庫就更新
    if found_tf_dataframe and found_pair_dataframe:
        found_pair_dataframe.price = float(received_datas['Price'])
        update_timeframe_data(received_datas, found_tf_dataframe)
        db.session.commit()
        return {'Error': "ERROR_OK"}
    else:
        debug_hook.send("line 237: something went wrong.")
        return {'Error': "ERROR_UNKNOWN"}


# return entry timeframe as a list for the given pair
def get_entry_list(TimeFrameData, pair):
    entry_tf_list = [
        TimeFrameData.query.filter_by(pair=pair, timeframe='6').first(),
        TimeFrameData.query.filter_by(pair=pair, timeframe='12').first(),
        TimeFrameData.query.filter_by(pair=pair, timeframe='23').first(),
        TimeFrameData.query.filter_by(pair=pair, timeframe='45').first()
    ]
    return entry_tf_list


# return compass timeframe as a list for the given pair
def get_compass_list(TimeFrameData, pair):
    compass_tf_list = [
        TimeFrameData.query.filter_by(pair=pair, timeframe='90').first(),
        TimeFrameData.query.filter_by(pair=pair, timeframe='180').first(),
        TimeFrameData.query.filter_by(pair=pair, timeframe='360').first(),
        TimeFrameData.query.filter_by(pair=pair, timeframe='720').first()
    ]
    return compass_tf_list
