from flask import Flask, request
import requests
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Token galat", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("MESSAGE AYA:", data)

    try:
        # Check karo message hai ya status update
        if 'messages' in data['entry'][0]['changes'][0]['value']:
            msg = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = msg['from']
            text = msg['text']['body']

            url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text", # <- YE ADD KIYA
                "text": {"body": f"Auto Reply: {text}"}
            }
            res = requests.post(url, headers=headers, json=payload)
            print("REPLY STATUS:", res.status_code, res.text) # <- YE LOG ME ERROR BATAYEGA
        else:
            print("Status update, not message")
    except Exception as e:
        print("Error:", e)
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
