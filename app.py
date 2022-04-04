import json
from datetime import timedelta
from json import JSONDecodeError
from flask import Flask, request, render_template
from flask import redirect, url_for, flash, session
from database.update import *
from database.model import *
from algorithem.shelley07 import *
from appConfig.tradingViewConfig import password
from appConfig.databaseConfig import *
# ---------Flask Basic Setting---------
app = Flask(__name__)
app.secret_key = 'SECRET_KEYYY'
app.permanent_session_lifetime = timedelta(minutes=5)
version = 'Beta v0.7.2 - FLIP'
# --------- Binance API---------
client = Client(binanceAPIConfig.API_KEY, binanceAPIConfig.API_SECRET)

# ---------Database config---------
ENV = ''
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = LOCAL_DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = HEROKU_DATABASE_URL
    version = "TESTING"

else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = HEROKU_DATABASE_URL


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def init_db():
    db.init_app(app)
    db.app = app
    db.create_all()

# version = "DEBUG"
init_db()

discordWebhookConfig.\
    debug_hook.\
    send("```EnvisionPlus - %s Successfully Deploy!!```" % version)
# ---------頁面---------
@app.route('/', methods=['GET', 'POST'])
def logindef():
    # if post method
    if request.method == "POST":
        userName = request.form['userName']
        session["userName"] = userName

        # Check whether user is in database
        found_user = Users.query.filter_by(userName=userName).first()
        if found_user:
            session["email"] = found_user.email
        else:
            usr = Users(userName, "")
            db.session.add(usr)
            db.session.commit()
        return redirect(url_for("user"))


    else:
        # if user is in database
        if "userName" in session:
            flash('already login')
            return redirect(url_for("user"))

        return render_template('login.html')
# def home():
#     return render_template('index.html')
@app.route('/index', methods=['GET', 'POST'])
def home():

    if request.method == "POST":
        try:
            email = request.form['email']
            session["email"] = email
        except KeyError:
            return redirect(url_for("home"))

        found_user = Users.query.filter_by(email=email).first()
        if found_user:
            session["email"] = found_user.email
        else:
            usr = Users("NONE", email)
            db.session.add(usr)
            db.session.commit()
        return redirect(url_for("home"))

    else:
        return render_template('home.html', version=version)

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # post
    if request.method == "POST":
        userName = request.form['userName']
        session["userName"] = userName

        # check whether user is in database
        found_user = Users.query.filter_by(userName=userName).first()
        if found_user:
            session["email"] = found_user.email
        else:
            usr = Users(userName, "")
            db.session.add(usr)
            db.session.commit()
        return redirect(url_for("user"))


    else:
        # if user login
        if "userName" in session:
            flash('already login')
            return redirect(url_for("user"))

        return render_template('login.html')


# logout
@app.route('/logout')
def logout():
    # if user login
    if "userName" in session:
        session.pop("userName", None)
        session.pop("email", None)
        flash("You have been logged out", "info")

    return redirect(url_for("login"))



@app.route('/trading_account')
def getBinanceFutureBalance():
    account = client.futures_account()
    data = {
        'Total Margin Balance' :account["totalMarginBalance"],
        'Total Wallet Balance' :account["totalWalletBalance"],
        'Unrealized Profit' :account["totalUnrealizedProfit"],
        'Available Balance' :account["availableBalance"]
    }

    return render_template("binancestat.html", data=data)

@app.route('/pairUpdate')
# update each share % by trigger activate
def shareUpdate():
    pairs = TradingGroupData.query.all()
    total_activate_trigger = 0.000
    for pair in pairs:
        if pair.trade_trigger:
            total_activate_trigger += 1
        else:
            pair.trade_percent = None

    if total_activate_trigger != 0:
        trade_percent = (1/total_activate_trigger) - 0.002
        for pair in pairs:
            if pair.trade_trigger:
                pair.trade_percent = trade_percent
    db.session.commit()


@app.route('/tradeMode', methods=['POST'])
def tradeMode():
    dataList = json.loads(request.data)
    found_pair_dataframe = TradingGroupData.query.filter_by(pair=dataList['pair']).first()
    if not found_pair_dataframe:
        return {'Error': 'ERROR_PAIR_NOT_SUPPORT'}
    if found_pair_dataframe.trade_trigger != dataList['tradeMode']:
        found_pair_dataframe.trade_trigger = dataList['tradeMode']
        discordWebhookConfig.debug_hook.send("%s trigger set to %d "
                                             % (found_pair_dataframe.pair,
                                                found_pair_dataframe.trade_trigger))
        db.session.commit()
        shareUpdate()
    return 'TODO'
# ----------------------------------------WebHook---------------------------------------------
@app.route('/tradingviewWH', methods=['POST'])
# Listening port
def process_data():
    try:
        received_datas = json.loads(request.data)
    except JSONDecodeError:
        debug_hook.send("Port Received None JSON data %s" % request.data)
        return {'Error': 'ERROR_INVALID_FORMAT'}
    # verifing user password
    if received_datas['Password'] != password:
        debug_hook.send("Server port received unknown request")
        return {'Error': 'ERROR_PASSWORD'}

    err = update_database(received_datas, TimeFrameData, TradingGroupData, db, version, Stats, Trades)['Error']
    if err != 'ERROR_OK':
        return err

    err = updatePosition(TimeFrameData, TradingGroupData, received_datas, db, Stats, version, Trades)
    db.session.commit()
    return err


if __name__ == '__main__':
    init_db()
    app.run()