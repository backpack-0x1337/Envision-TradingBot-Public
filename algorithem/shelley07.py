from exchanger.binance import *
from binance.enums import *
from appConfig import discordWebhookConfig
from database.update import get_entry_list, get_compass_list
from database import shelleyplus_update
from exchanger.binance import get_wallet_balance


# ----------------------------------------Communication----------------------------------------
def discordUpdate(pair, data, version, profit_loss):
    if data.win + data.loss == 0:
        discordWebhookConfig.trading_signal_hook.send("```"
                                                      "%s\n"
                                                      "Pair: %s \n"
                                                      "Position Update: %s \n"
                                                      "Current price: %f\n"
                                                      "Captured Movement: %f\n"
                                                      "Win Rate: %f\n"
                                                      "```" % (
                                                          version, pair, data.pos, data.price,
                                                          profit_loss,
                                                          0))

        return 0
    discordWebhookConfig.trading_signal_hook.send("```"
                                                  "%s \n"
                                                  "Pair: %s \n"
                                                  "Position Update: %s \n"
                                                  "Current price: %f\n"
                                                  "Captured Movement: %f\n"
                                                  "Win Rate: %f\n"
                                                  "```" % (
                                                      version, pair, data.pos, data.price,
                                                      profit_loss,
                                                      data.win / (data.win + data.loss)))
    return 0


# ----------------------------------------ALGO---------------------------------------------


def isGoodShortEntry(entry_time_frame_data):
    count = 0
    for tf_data in entry_time_frame_data:
        if tf_data.white < 50:
            count += 1
    if count >= 4:
        return True
    return False


def isGoodLongEntry(entry_time_frame_data):
    count = 0
    for tf_data in entry_time_frame_data:
        if tf_data.white > 50:
            count += 1
    if count >= 4:
        return True
    return False

def isUpwardPressure(compass_time_frame_data):
    upward_tf = 0
    downward_tf = 0
    counter = 1

    for tf_data in compass_time_frame_data:
        if tf_data.red >= 50 and tf_data.white >= 50:
            upward_tf = counter
        if tf_data.red <= 50 and tf_data.white <= 50:
            downward_tf = counter
        counter += 1

    if upward_tf > downward_tf:
        return True

    if downward_tf == upward_tf:
        return True
    return False


def isDownwardPressure(compass_time_frame_data):
    upward_tf = 0
    downward_tf = 0
    counter = 1
    for tf_data in compass_time_frame_data:
        if tf_data.red >= 50 and tf_data.white >= 50:
            upward_tf = counter

        if tf_data.red <= 50 and tf_data.white <= 50:
            downward_tf = counter
        counter += 1

    if downward_tf > upward_tf:
        return True

    if downward_tf == upward_tf:
        return True
    return False


def updatePosition(TimeFrameData, TradingGroupData, received_datas, db, Stats, version, Trades):
    pair = received_datas['Pair']
    time = received_datas['Time']
    if pair == "ADAUSDT":
        entry_tf_list = shelleyplus_update.get_entry_list(TimeFrameData, pair)
        compass_tf_list = shelleyplus_update.get_compass_list(TimeFrameData, pair)
    else:
        entry_tf_list = get_entry_list(TimeFrameData, pair)
        compass_tf_list = get_compass_list(TimeFrameData, pair)

    for data in entry_tf_list:
        if data is None:
            return {'Error': 'ERROR_NOT_ENOUGH_INFO'}

    for data in compass_tf_list:
        if data is None:
            return {'Error': 'ERROR_NOT_ENOUGH_INFO'}
    version_stat = Stats.query.filter_by(version=version).first()
    trading_pair = TradingGroupData.query.filter_by(pair=pair).first()

    # if isUpwardPressure(compass_tf_list) and isUpwardPressure(entry_tf_list) and isGoodLongEntry(entry_tf_list):
    if isDownwardPressure(compass_tf_list) and isDownwardPressure(entry_tf_list) and isGoodShortEntry(entry_tf_list):
        if trading_pair.pos != "L":
            # there is no long pos trade
            profit_loss_percent = 0
            if trading_pair.pos_price is not None:
                profit_loss_percent = (trading_pair.pos_price - trading_pair.price) / trading_pair.pos_price
                trading_pair.captured_price_movement += profit_loss_percent
                if profit_loss_percent > 0:
                    trading_pair.win += 1
                else:
                    trading_pair.loss += 1

            # if trade trigger for pair == True
            if trading_pair.trade_trigger:
                version_stat.total_captured_movement += profit_loss_percent
                openPositionOnFuture(
                    trading_pair.trading_symbol,
                    SIDE_BUY,
                    ORDER_TYPE_MARKET,
                    trading_pair.precision,
                    trading_pair.leverage,
                    trading_pair.trade_percent,
                    trading_pair.price
                )
                found_last_trade_no = Trades.query.order_by(Trades.tradeNo.desc()).first().tradeNo
                new_trade_info = Trades(found_last_trade_no+1, time, pair, float(get_wallet_balance()))
                db.session.add(new_trade_info)
                db.session.commit()
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(trading_pair.trading_symbol))
            trading_pair.pos_price = trading_pair.price
            trading_pair.pos = "L"
            discordUpdate(pair, trading_pair, version, profit_loss_percent)
            db.session.commit()
    elif isUpwardPressure(compass_tf_list) and isUpwardPressure(entry_tf_list) and isGoodLongEntry(entry_tf_list):
    # elif isDownwardPressure(compass_tf_list) and isDownwardPressure(entry_tf_list) and isGoodShortEntry(entry_tf_list):
        if trading_pair.pos != "S":
            profit_loss_percent = 0
            if trading_pair.pos_price is not None:
                profit_loss_percent = (trading_pair.price - trading_pair.pos_price) / trading_pair.pos_price
                trading_pair.captured_price_movement += profit_loss_percent
                if profit_loss_percent > 0:
                    trading_pair.win += 1
                else:
                    trading_pair.loss += 1

            # flip position
            if trading_pair.trade_trigger:
                version_stat.total_captured_movement += profit_loss_percent
                openPositionOnFuture(
                    trading_pair.trading_symbol,
                    SIDE_SELL,
                    ORDER_TYPE_MARKET,
                    trading_pair.precision,
                    trading_pair.leverage,
                    trading_pair.trade_percent,
                    trading_pair.price
                )
                found_last_trade_no = Trades.query.order_by(Trades.tradeNo.desc()).first().tradeNo
                new_trade_info = Trades(found_last_trade_no + 1, time, pair, float(get_wallet_balance()))
                db.session.add(new_trade_info)
                db.session.commit()
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(trading_pair.trading_symbol))
            trading_pair.pos_price = trading_pair.price
            trading_pair.pos = "S"
            discordUpdate(pair, trading_pair, version, profit_loss_percent)
            db.session.commit()

    return {'Error': 'ERROR_OK'}
