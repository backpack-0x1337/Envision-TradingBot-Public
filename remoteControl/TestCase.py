import requests
website1 = "https://bag-pack.herokuapp.com/tradingviewWH"
website2 = "http://127.0.0.1:5000/tradingviewWH"

timeframes = [
    "6",
    "12",
    "23",
    "45",
    "90",
    "180"
]
def get_pay_load(tfs):
    return {
        "Password": "123",
        "Pair": "UNIUSDT",
        "TF": tfs,
        "Event": "RU",
        "Price": "1.2",
        "Time": "2021-03-04T09:08:14Z",
        "G": "60.31832799784352",
        "R": "60.3923530467188",
        "B": "23.138846905422973",
        "W": "60.19330085116248"
    }

headers = {"Content-Type": "application/json"}
for tf in timeframes:
    jsonFile = get_pay_load(tf)
    response = requests.request("POST", website2, json=jsonFile, headers=headers)
    print(response.text)



