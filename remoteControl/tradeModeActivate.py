import requests

url = "https://bag-pack.herokuapp.com/tradeMode"

payload = {
    "pair": "btcusdtst",
    "tradeMode": True
}
payload2 = {
    "pair": "btcusdtst",
    "tradeMode": True
}
headers = {"Content-Type": "application/json"}
for i in range(2):
    response = requests.request("POST", url, json=payload, headers=headers)
    print(response.text)
    response = requests.request("POST", url, json=payload2, headers=headers)
    print(response.text)
