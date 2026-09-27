import os
import requests
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is Live", 200

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    my_token = os.getenv("VERIFY_TOKEN", "").strip()
    if token == my_token:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            phone_id = entry["metadata"]["phone_number_id"]
            from_number = entry["messages"][0]["from"]

            # Simple test reply
            url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN','').strip()}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "text": {"body": "Ji M. Ahmed bolen! Bot ab Live hai. Test OK!"}
            }
            requests.post(url, headers=headers, json=payload, timeout=10)
            print("Reply sent!")
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
