import os, requests
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

            # --- GROQ AI (Smart) ---
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are NextLevel Agency assistant from Quetta. You sell Website Development, Social Media Marketing, and WhatsApp Bots. Be friendly, helpful, speak in Roman Urdu + English mix. Keep reply short (2-3 lines). If user says marketing, explain your marketing package: Facebook Ads, Content, Leads. Always ask about their business."},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7
                }
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                ai_reply = j["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Groq Error: {e} {r.text if 'r' in locals() else ''}")
                ai_reply = "Zabardast! Marketing ke liye hum Facebook/Instagram Ads, daily posts, aur leads generation karte hain. Aap ka business kis city me hai aur kis cheez ka hai?"

            wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply[:4000]}}
            requests.post(wa_url, json=wa_payload, headers=headers)

    except Exception as e:
        print(f"Webhook Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
