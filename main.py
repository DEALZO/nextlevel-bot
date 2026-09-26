import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "").strip()
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().replace("\n", "").replace("\r", "").replace(" ", "")

@app.route("/")
def home():
    return "Bot LIVE", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" in value:
            msg = value["messages"][0]
            from_num = msg["from"]
            user_text = msg["text"]["body"]
            print(f"USER MSG: {user_text}")

            ai_reply = ""
            try:
                # Sahi Model Name
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama3-8b-8192", # <-- Ye wala 100% chalega
                    "messages": [
                        {"role": "system", "content": "You are NextLevel Agency from Quetta. Sell Website, Marketing, WhatsApp Bot. Reply in short Roman Urdu, friendly. Don't ask city again if user said Quetta ecommerce."},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                j = r.json()
                print(f"GROQ OK: {j}")
                ai_reply = j["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Groq Fail, using fallback: {e}")
                ai_reply = f"Samajh gaya '{user_text}'! Quetta ecommerce ke liye Shopify + Ads best hai. Product kya hai aapka?"

            # WhatsApp Send
            wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            wa_headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply}}
            res = requests.post(wa_url, json=wa_payload, headers=wa_headers)
            print(f"WA Send Status: {res.status_code} - {res.text}")

    except Exception as e:
        print(f"Main Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
