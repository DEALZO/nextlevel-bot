import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "NextLevel Bot is LIVE!", 200

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
            print(f"User {from_num}: {user_text}")

            # --- AI REPLY LOGIC (Fixed) ---
            ai_reply = get_ai_reply(user_text)

            # --- SEND BACK TO WHATSAPP ---
            wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {
                "messaging_product": "whatsapp",
                "to": from_num,
                "text": {"body": ai_reply[:4000]}
            }
            res = requests.post(wa_url, json=wa_payload, headers=headers)
            print(f"WA Send Status: {res.status_code}")

    except Exception as e:
        print(f"Webhook Error: {e}")

    return "OK", 200

def get_ai_reply(user_text):
    # Agar Gemini Key nahi hai to simple reply
    if not GEMINI_API_KEY:
        return "Salam! NextLevel Agency me khush amdeed. Aap ko kis cheez me help chahiye?"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

        # Safety settings ke saath payload - taake 'candidates' error na aaye
        payload = {
            "contents": [{"parts": [{"text": f"You are NextLevel Agency's helpful assistant. Reply in same language user used (Urdu/English mix). Be friendly and short. User: {user_text}"}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        r = requests.post(url, json=payload, timeout=20)
        j = r.json()

        # Check if candidates exist
        if "candidates" in j and len(j["candidates"]) > 0:
            return j["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # Agar Gemini ne block kiya to ye default reply jayega, error nahi dikhega
            print(f"Gemini Blocked Response: {j}")
            return "Assalam-o-Alaikum! Main NextLevel ka assistant hun. Bataiye aap ko Web Development, Marketing ya Automation me se kis service me help chahiye?"

    except Exception as e:
        print(f"Gemini Error: {e}")
        # Ab yahan error wala text customer ko nahi jayega
        return "Hello! NextLevel Agency me welcome. Aap apna sawal dobara bhej sakte hain?"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
