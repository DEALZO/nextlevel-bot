import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Keys - space/enter auto clean
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "").strip()
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().replace("\n", "").replace("\r", "").replace(" ", "")

@app.route("/")
def home():
    return "NextLevel Bot LIVE - main.py OK", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification Failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" in value:
            msg = value["messages"][0]
            from_num = msg["from"]
            user_text = msg["text"]["body"]

            print(f"USER: {user_text} | KEY OK: {bool(GROQ_API_KEY)}")
            ai_reply = ""

            # --- GROQ AI ---
            try:
                if not GROQ_API_KEY:
                    raise Exception("GROQ_API_KEY is empty")

                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are NextLevel Agency assistant from Quetta. You sell: 1) Website Development 2) Social Media Marketing 3) WhatsApp Bots. Speak in Roman Urdu + English mix, friendly, short 2-3 lines. User business is in Quetta ecommerce, so DON'T ask city again. Ask product and give plan."
                        },
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7
                }
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                j = r.json()
                print(f"GROQ: {j}")

                if "choices" in j and len(j["choices"]) > 0:
                    ai_reply = j["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Groq Error: {j}")

            except Exception as e:
                print(f"Groq Fail: {e}")
                txt = user_text.lower()
                if "quetta" in txt or "ecommerce" in txt or "online" in txt:
                    ai_reply = "Perfect! Quetta Ecommerce ke liye hum Shopify + FB/Insta Ads + COD setup karte hain. Aap kya bechte ho? Kapre, cosmetics? Roz 20-30 orders ka target rakhte hain."
                elif "marketing" in txt or "ads" in txt:
                    ai_reply = "Marketing package 15k/month se start: 30 posts, 2 campaigns, daily leads. Aap ka page link bhejo?"
                elif "website" in txt:
                    ai_reply = "Ecommerce Website 25k me, 1 week me ready. Payment, delivery, WhatsApp sab connect. Domain hai?"
                else:
                    ai_reply = f"Samajh gaya '{user_text}'. Iske liye best solution deta hun. Product kya hai aapka?"

            # Send back to WhatsApp
            wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            wa_headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            wa_payload = {
                "messaging_product": "whatsapp",
                "to": from_num,
                "text": {"body": ai_reply[:4000]}
            }
            res = requests.post(wa_url, json=wa_payload, headers=wa_headers)
            print(f"WA Status: {res.status_code} - {res.text[:200]}")

    except Exception as e:
        print(f"Main Error: {e}")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
