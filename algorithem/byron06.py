from exchanger.binance import *
from binance.enums import *
from appConfig import discordWebhookConfig
from database.update import get_entry_list, get_compass_list



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


def isModeCorrection(compass_time_frame_data, mode):
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
        return True
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
        return True

    return False


def updatePosition(TimeFrameData, TradingGroupData, pair, db, Stats, version):
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
    if isUpwardPressure(compass_tf_list) and isGoodLongEntry(entry_tf_list):
        if trading_pair.pos != "L":
            # there is no long pos trade
            profit_loss_percent = 0
            if trading_pair.pos_price is not None:
                profit_loss_percent = (trading_pair.pos_price - trading_pair.price) / trading_pair.pos_price
                trading_pair.captured_price_movement += profit_loss_percent
                if profit_loss_percent < 0:
                    trading_pair.win += 1
                else:
                    trading_pair.loss += 1

            # flip position
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
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(trading_pair.trading_symbol))
            trading_pair.pos_price = trading_pair.price
            trading_pair.pos = "L"
            discordUpdate(pair, trading_pair, version, profit_loss_percent)
            db.session.commit()

    elif isDownwardPressure(compass_tf_list) and isGoodShortEntry(entry_tf_list):
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
            else:
                discordWebhookConfig.debug_hook.send("{} trade trigger is off".format(trading_pair.trading_symbol))
            trading_pair.pos_price = trading_pair.price
            trading_pair.pos = "S"
            discordUpdate(pair, trading_pair, version, profit_loss_percent)
            db.session.commit()

    return {'Error': 'ERROR_OK'}
