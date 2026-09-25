import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "").strip()
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().replace("\n", "").replace(" ", "")

@app.route("/")
def home():
    return "NextLevel Bot LIVE", 200

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

            ai_reply = ""

            # --- GROQ AI ---
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant", # Most stable, fast
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are NextLevel Agency assistant from Quetta. You sell: 1) Website Development 2) Social Media Marketing 3) WhatsApp Bots. Speak in Roman Urdu + English mix, friendly, short 2-3 lines. User already told business is in Quetta ecommerce, so DON'T ask city again. Ask what product they sell and give ecommerce plan. If user says Salam, reply Wa Salam."
                        },
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7
                }
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                j = r.json()
                print(f"Groq Response: {j}")

                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                else:
                    # If Groq gives error, show it in logs
                    raise Exception(f"Groq Error JSON: {j}")

            except Exception as e:
                print(f"Groq Failed: {e}")
                # SMART fallback - no more same boring reply
                txt = user_text.lower()
                if "quetta" in txt or "ecommerce" in txt or "online" in txt:
                    ai_reply = "Perfect! Quetta Ecommerce ke liye hum Shopify website + FB/Insta Ads + COD system setup karte hain. Aap kya bechte ho? Kapre, cosmetics? Roz 20-30 orders ka target rakhte hain. Product batao?"
                elif "marketing" in txt or "ads" in txt:
                    ai_reply = "Marketing package me 30 posts, 2 ad campaigns, aur daily leads shamil hain. 15k/month se start. Aap ka page link bhejo, audit kar deta hun."
                elif "website" in txt:
                    ai_reply = "Website Ecommerce wali 25k me, 1 week me ready. Payment, delivery, WhatsApp connect sab hoga. Domain hai aap ke pas?"
                else:
                    ai_reply = f"Samajh gaya '{user_text}'. Iske liye best solution deta hun. Aap ka business model kya hai? Thora detail bataiye."

            # Send to WhatsApp
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
            print(f"WA Status: {res.status_code}")

    except Exception as e:
        print(f"Webhook Main Error: {e}")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
