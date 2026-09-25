import os, requests
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

            # --- AI CALL via REST (100% working) ---
            ai_reply = None
            if GEMINI_API_KEY:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    payload = {"contents": [{"parts": [{"text": f"Reply in same language as user, friendly: {user_text}"}]}]}
                    r = requests.post(url, json=payload, timeout=15)
                    j = r.json()
                    ai_reply = j["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"Gemini OK: {ai_reply}")
                except Exception as e:
                    print(f"Gemini API Error: {e} - Full response: {r.text if 'r' in locals() else ''}")
                    ai_reply = f"Bot ON hai! (Gemini Error: {e}) You said: {user_text}"
            else:
                ai_reply = f"Bot ON! You said: {user_text}. (Add GEMINI_API_KEY in Railway to enable AI)"

            # --- SEND BACK TO WHATSAPP ---
            wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply[:4000]}}
            res = requests.post(wa_url, json=wa_payload, headers=headers)
            print(f"WA Send Status: {res.status_code} {res.text}")

    except Exception as e:
        print(f"Webhook Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
