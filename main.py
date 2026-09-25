import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
            print(f"User: {user_text}")

            # --- FIXED GEMINI CALL ---
            ai_reply = "Salam! NextLevel me khush amdeed. Aap ko kis service me help chahiye?"
            if GEMINI_API_KEY:
                try:
                    # Sahi model ka naam
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": f"You are NextLevel Agency assistant. User: {user_text}. Reply short, friendly, Roman Urdu/English."}]}],
                        "safetySettings": [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                        ]
                    }
                    r = requests.post(url, json=payload, timeout=15)
                    j = r.json()
                    print(f"Gemini Full Response: {j}")

                    if "candidates" in j:
                        ai_reply = j["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        print("Gemini blocked/error")
                        # Smart fallback, same reply nahi
                        if "buy" in user_text.lower() or "service" in user_text.lower():
                            ai_reply = "Zabardast! Aap ko kaunsi service chahiye? 1) Website 2) Marketing 3) WhatsApp Bot. Bataiye?"
                        else:
                            ai_reply = f"Ji {user_text} ke bare me bataiye, main details deta hun. Aap ka business kis cheez ka hai?"

                except Exception as e:
                    print(f"Gemini Exception: {e}")

            # --- SEND TO WHATSAPP ---
            wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply[:4000]}}
            res = requests.post(wa_url, json=wa_payload, headers=headers)
            print(f"WA Send Status: {res.status_code}")

    except Exception as e:
        print(f"Webhook Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
