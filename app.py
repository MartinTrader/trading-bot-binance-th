import os
import hmac
import hashlib
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Deine Binance TH API-Daten (sicherer: später in Render-Env-Variablen)
API_KEY = "DCD7A79DCB2B96F602758BD960183E90B422ADA8BDF914699F3A4AAD386C8B95"
API_SECRET = "2FFE68A5CA379904DE5E395A44F6571744735056393B3BBE48AB854B22C399FA"
BASE_URL = "https://api.binance.th"

def create_signature(query_string):
    return hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def binance_request(method, endpoint, params=None):
    if params is None:
        params = {}
    params['timestamp'] = int(time.time() * 1000)
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = create_signature(query_string)
    params['signature'] = signature
    url = f"{BASE_URL}{endpoint}?{query_string}"
    headers = {'X-MBX-APIKEY': API_KEY}
    response = requests.request(method, url, headers=headers)
    return response.json()

@app.route('/')
def home():
    return "Hallo, mein Trading-Roboter ist bereit! (Webhook-Test mit Binance TH)"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Keine Daten empfangen"}), 400
        action = data.get('action')
        symbol = data.get('symbol')
        quantity = float(data.get('quantity', 0))
        if not all([action, symbol, quantity]):
            return jsonify({"error": "Fehlende Parameter"}), 400

        if action.lower() == 'buy':
            endpoint = "/api/v3/order"
            params = {'symbol': symbol, 'side': 'BUY', 'type': 'MARKET', 'quantity': quantity}
            order = binance_request('POST', endpoint, params)
        elif action.lower() == 'sell':
            endpoint = "/api/v3/order"
            params = {'symbol': symbol, 'side': 'SELL', 'type': 'MARKET', 'quantity': quantity}
            order = binance_request('POST', endpoint, params)
        else:
            return jsonify({"error": "Ungültige Action"}), 400

        if 'orderId' in order:
            return jsonify({"status": "success", "order_id": order['orderId']}), 200
        else:
            return jsonify({"error": str(order)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
