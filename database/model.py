from flask_sqlalchemy import SQLAlchemy

# 數據庫

db = SQLAlchemy()


class Users(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, userName, email):
        self.userName = userName
        self.email = email


class TimeFrameData(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    green = db.Column(db.FLOAT)
    red = db.Column(db.FLOAT)
    blue = db.Column(db.FLOAT)
    white = db.Column(db.FLOAT)
    pair = db.Column(db.String(100))
    timeframe = db.Column(db.String(100))

    def __init__(self, green, red, blue, white, pair, timeframe):
        self.white = white
        self.blue = blue
        self.red = red
        self.green = green
        self.pair = pair
        self.timeframe = timeframe


class TradingGroupData(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    precision = db.Column(db.Integer)
    trading_symbol = db.Column(db.String(100), unique=True)
    price = db.Column(db.Float)
    loss = db.Column(db.Integer)
    win = db.Column(db.Integer)
    captured_price_movement = db.Column(db.Float)
    leverage = db.Column(db.Integer)
    pos_price = db.Column(db.Float)
    pos = db.Column(db.String(10))
    trade_trigger = db.Column(db.BOOLEAN)
    pair = db.Column(db.String(100), unique=True)
    trade_percent = db.Column(db.Float)

    def __init__(self, precision, trading_symbol, price, loss, win, captured_price_movement, leverage, pos_price,
                 pos, trade_trigger, pair, trade_percent):
        self.captured_price_movement = captured_price_movement
        self.leverage = leverage
        self.pos = pos
        self.price = price
        self.loss = loss
        self.pos_price = pos_price
        self.trade_trigger = trade_trigger
        self.trading_symbol = trading_symbol
        self.precision = precision
        self.win = win
        self.pair = pair
        self.trade_percent = trade_percent


class Stats(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    total_pnl = db.Column(db.Float)
    total_captured_movement = db.Column(db.Float)
    version = db.Column(db.String(100))

    def __init__(self, total_pnl, total_captured_movement, version):
        self.total_captured_movement = total_captured_movement
        self.total_pnl = total_pnl
        self.version = version


class Trades(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    tradeNo = db.Column(db.Integer)
    account_balance = db.Column(db.Float)
    pair = db.Column(db.String(100))
    time = db.Column(db.String(100))

    def __init__(self, tradeNo, time, pair, account_balance):
        self.tradeNo = tradeNo
        self.time = time
        self.pair = pair
        self.account_balance = account_balance

