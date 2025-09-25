import hmac
import hashlib
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Deine Binance TH API-Daten
API_KEY = "DCD7A79DCB2B96F602758BD960183E90B422ADA8BDF914699F3A4AAD386C8B95"
API_SECRET = "2FFE68A5CA379904DE5E395A44F6571744735056393B3BBE48AB854B22C399FA"
BASE_URL = "https://api.binance.th"

def get_server_time():
    try:
        response = requests.get(f"{BASE_URL}/api/v3/time")
        if response.status_code == 200:
            return response.json()['serverTime']
    except:
        pass
    return int(time.time() * 1000)

def create_signature(query_string):
    return hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def binance_request(method, endpoint, params=None):
    if params is None:
        params = {}
    timestamp = get_server_time()
    params['timestamp'] = timestamp
    params['recvWindow'] = 5000
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    params['signature'] = create_signature(query_string)
    headers = {'X-MBX-APIKEY': API_KEY}
    url = f"{BASE_URL}{endpoint}"
    if method.upper() == 'POST':
        response = requests.post(url, headers=headers, params=params)
    else:
        response = requests.get(url, headers=headers, params=params)
    print(f"Debug: Method={method}, URL={url}, Status={response.status_code}, Response={response.text[:200]}")
    if response.status_code == 401:
        return {"error": f"401 Unauthorized - Response: {response.text}"}
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    return response.json()

def get_available_balance(asset):
    account = binance_request('GET', '/api/v3/account')
    if 'balances' in account:
        for balance in account['balances']:
            if balance['asset'] == asset and float(balance['free']) > 0:
                return float(balance['free'])
    return 0.0

@app.route('/')
def home():
    return "Hallo, mein Trading-Roboter ist bereit! (Webhook-Test mit Binance TH)"

@app.route('/test')
def test_api():
    account = binance_request('GET', '/api/v3/account')
    if 'error' in account:
        return jsonify(account), 500
    return jsonify({"status": "API-Verbindung OK", "balances_count": len(account.get('balances', []))}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Keine Daten empfangen"}), 400
        action = data.get('action')
        symbol = data.get('ticker', 'SOLUSDT')  # Nutzt {{ticker}}, Fallback auf SOLUSDT
        order_size = data.get('order_size', '0%').strip('%')
        if action.lower() == 'buy':
            usdt_balance = get_available_balance('USDT')
            if usdt_balance <= 10:  # Mindestbetrag für Gebühren
                return jsonify({"error": "Nicht genug USDT"}), 400
            # Hole aktuellen Preis (geschätzt, besser via API)
            price = 60.0  # Passe an aktuellen SOL/USDT-Preis an!
            quantity = usdt_balance / price if order_size == '100' else float(data.get('quantity', 0))
            if quantity <= 0:
                return jsonify({"error": "Ungültige Menge"}), 400
            params = {'symbol': symbol, 'side': 'BUY', 'type': 'MARKET', 'quantity': quantity}
            order = binance_request('POST', '/api/v3/order', params)
        elif action.lower() == 'sell':
            asset = symbol.split('USDT')[0]  # z. B. "SOL" aus "SOLUSDT"
            balance = get_available_balance(asset)
            if balance <= 0:
                return jsonify({"error": "Kein " + asset + " verfügbar"}), 400
            quantity = balance if order_size == '100' else float(data.get('quantity', 0))
            params = {'symbol': symbol, 'side': 'SELL', 'type': 'MARKET', 'quantity': quantity}
            order = binance_request('POST', '/api/v3/order', params)
        else:
            return jsonify({"error": "Ungültige Action"}), 400

        if isinstance(order, dict) and 'orderId' in order:
            return jsonify({"status": "success", "order_id": order['orderId']}), 200
        else:
            return jsonify({"error": str(order)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
