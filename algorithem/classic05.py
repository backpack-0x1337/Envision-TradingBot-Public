from exchanger.binance import *
from binance.enums import *
from appConfig import discordWebhookConfig
from database.update import get_entry_list, get_compass_list


version = "{BETA v0.5}"


# ----------------------------------------Communication----------------------------------------
def discordUpdate(pair, data):
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
                                                          data.captured_price_movement,
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
                                                      version, pair, data.pos, data.price, data.captured_price_movement,
                                                      data.win / (data.win + data.loss)))
    return 0


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


def updatePosition(TimeFrameData, TradingGroupData, pair, db):
    entry_tf_list = get_entry_list(TimeFrameData, pair)
    compass_tf_list = get_compass_list(TimeFrameData, pair)

    for data in entry_tf_list:
        if data is None:
            return {'Error': 'ERROR_NOT_ENOUGH_INFO'}

    for data in compass_tf_list:
        if data is None:
            return {'Error': 'ERROR_NOT_ENOUGH_INFO'}

    trading_pair = TradingGroupData.query.filter_by(pair=pair).first()
    if isUpwardPressure(compass_tf_list) and isGoodLongEntry(entry_tf_list):
        if trading_pair.pos != "L":
            # there is open short pos trade
            if trading_pair.pos_price is not None:
                trading_pair.captured_price_movement += \
                    (trading_pair.pos_price - trading_pair.price) / trading_pair.pos_price
                if (trading_pair.price - trading_pair.pos_price) < 0:
                    trading_pair.win += 1
                else:
                    trading_pair.loss += 1

            # flip position
            if trading_pair.trade_trigger:
                openPositionOnFuture(
                    trading_pair.trading_symbol,
                    SIDE_BUY,
                    ORDER_TYPE_MARKET,
                    trading_pair.precision,
                    trading_pair.leverage,
                    trading_pair.trade_percent,
                    trading_pair.price
                )
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(trading_pair.trading_symbol))
            trading_pair.pos_price = trading_pair.price
            trading_pair.pos = "L"
            discordUpdate(pair, trading_pair)
            db.session.commit()

    if not isUpwardPressure(compass_tf_list) and isGoodShortEntry(entry_tf_list):
        if trading_pair.pos != "S":

            if trading_pair.pos_price is not None:
                trading_pair.captured_price_movement += \
                    (trading_pair.price - trading_pair.pos_price) / trading_pair.pos_price
                if (trading_pair.price - trading_pair.pos_price) > 0:
                    trading_pair.win += 1
                else:
                    trading_pair.loss += 1
            # flip position
            if trading_pair.trade_trigger:
                openPositionOnFuture(
                    trading_pair.trading_symbol,
                    SIDE_SELL,
                    ORDER_TYPE_MARKET,
                    trading_pair.precision,
                    trading_pair.leverage,
                    trading_pair.trade_percent,
                    trading_pair.price
                )
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(trading_pair.trading_symbol))
            trading_pair.pos_price = trading_pair.price
            trading_pair.pos = "S"
            discordUpdate(pair, trading_pair)
            db.session.commit()

    return {'Error': 'ERROR_OK'}
