from flask import Flask, request, jsonify
from binance.client import Client

app = Flask(__name__)

# API-Keys (deine Binance TH Daten)
api_key = "DCD7A79DCB2B96F602758BD960183E90B422ADA8BDF914699F3A4AAD386C8B95"
api_secret = "2FFE68A5CA379904DE5E395A44F6571744735056393B3BBE48AB854B22C399FA"
client = Client(api_key, api_secret, base_url='https://api.binance.th')

@app.route('/')
def home():
    return "Hallo, mein Trading-Roboter ist bereit! (Webhook-Test)"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "Keine Daten empfangen"}), 400
    action = data.get('action')
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    if not all([action, symbol, quantity]):
        return jsonify({"error": "Fehlende Parameter"}), 400
    try:
        if action.lower() == 'buy':
            order = client.order_market_buy(symbol=symbol, quantity=quantity)
        elif action.lower() == 'sell':
            order = client.order_market_sell(symbol=symbol, quantity=quantity)
        else:
            return jsonify({"error": "Ungültige Action"}), 400
        return jsonify({"status": "success", "order_id": order['orderId']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
