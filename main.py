import os, requests
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

@app.route("/")
def home(): return "Bot LIVE", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg = entry["messages"][0]
            from_num = msg["from"]
            user_text = msg["text"]["body"]

            # YEH LINE SAB THEEK KAREGI - Jis number pe msg aaya usi ka ID use karo
            phone_number_id = entry["metadata"]["phone_number_id"]

            print(f"MSG from {from_num} on {phone_number_id}: {user_text}")

            ai_reply = ""
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "You are NextLevel Agency from Quetta. You sell Website, Marketing, WhatsApp Bot. Reply in short Roman Urdu. Don't copy user msg, give helpful answer."},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                j = r.json()
                print(f"GROQ: {j}")
                ai_reply = j["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Groq fail: {e}")
                ai_reply = "Quetta ecommerce ke liye hum Shopify store + FB Ads + COD setup karte hain. Aap kya sell karte ho?"

            # Usi number se reply jahan se msg aaya
            wa_url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
            wa_headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply}}
            res = requests.post(wa_url, json=wa_payload, headers=wa_headers)
            print(f"WA {phone_number_id} Status: {res.status_code} {res.text[:200]}")

    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
