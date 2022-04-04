import math
from binance.client import Client
from binance.enums import *
from appConfig import binanceAPIConfig, discordWebhookConfig

client = Client(binanceAPIConfig.API_KEY, binanceAPIConfig.API_SECRET)


# ----------------------------------------BINANCE API----------------------------------------

# Close Pair Opened Position
def close_pair_position_with_opposite_side(symbol, trade_type, side, pair_pos_info):
    quantity = abs(float(pair_pos_info['positionAmt']))
    if quantity != 0:
        try:
            client.futures_create_order(symbol=symbol,
                                        side=side,
                                        type=trade_type,
                                        quantity=quantity)
            discordWebhookConfig.trading_signal_hook.send(
                "Successfully | CLOSE | %s | Quantity-> %f" % (symbol, quantity))
        except Exception as e:
            discordWebhookConfig.trading_signal_hook.send(
                "Failed | CLOSE | %s | Quantity-> %f: %s" % (symbol, quantity, e))


def get_next_order_quantity(precision, price, trading_leverage, usd):
    # TODO verify USD * Trade percent
    quantity = (usd/ price) * trading_leverage
    # quantity = (usd / price) * trading_leverage * trade_percent
    if precision == 0:
        quantity = int(quantity)
    else:
        quantity = (math.floor(quantity * 10 ** precision) / 10 ** precision)
    return quantity


def get_wallet_balance():
    return client.futures_account()["totalWalletBalance"]


def openPositionOnFuture(symbol, side, trade_type, precision, trading_leverage, trade_percent, pair_price):

    posInfo = client.futures_position_information(symbol=symbol)[0]
    close_pair_position_with_opposite_side(symbol, trade_type, side, posInfo)

    accountInfo = client.futures_account()
    usd = float(accountInfo['totalWalletBalance']) * trade_percent
    price = float(posInfo['markPrice'])
    freeBalance = float(accountInfo["availableBalance"])

    # TODO price == 0??
    if price == 0:
        price = float(pair_price)

    changeLeverage(symbol, trading_leverage)
    quantity = get_next_order_quantity(precision, price, trading_leverage, usd)

    try:
        margin_type = "ISOLATED"
        client.futures_change_margin_type(symbol=symbol,marginType= margin_type)
    except Exception as e:
        pass

    try:
        client.futures_create_order(symbol=symbol,
                                    side=side,
                                    type=trade_type,
                                    quantity=quantity)
        discordWebhookConfig.trading_signal_hook.send(
            "Successfully | %s | %s | Quantity-> %f" % (side, symbol, quantity))
    except Exception as e:
        try:
            discordWebhookConfig.trading_signal_hook.send(
                "OPEN %s position FAILED :%s, Changing Calculation Method!" % (symbol, e))
            quantity = get_next_order_quantity(precision, price, trading_leverage, freeBalance * 0.9)
            if precision == 0:
                quantity = int(quantity)
            client.futures_create_order(symbol=symbol,
                                        side=side,
                                        type=trade_type,
                                        quantity=quantity)
            discordWebhookConfig.trading_signal_hook.send(
                "AutoFix Successfully | %s | %s | Quantity-> %f" % (side, symbol, quantity))
        except Exception as e:
            discordWebhookConfig.trading_signal_hook.send("Final: OPEN %s position FAILED %s" % (symbol, e))




def changeMarginType(symbol, margin_type):
    client.futures_change_margin_type(symbol=symbol, marginType=margin_type)


def changeLeverage(symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol,
                                       leverage=leverage)
    except Exception as e:
        discordWebhookConfig.debug_hook.send("change %s leverage failed %s" % (symbol, e))


def isPositionOpenAtSymbol(symbol):
    try:
        if float(client.futures_position_information(symbol="adausdt")[0]['positionAmt']) != 0:
            return True
        else:
            return False
    except Exception as e:
        discordWebhookConfig.debug_hook.send("ERROR isPositionOpenAtSymbol %s" % symbol)
        return True
