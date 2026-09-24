import os, requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini optional import
model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("Gemini Model Loaded")
    except Exception as e:
        print(f"Gemini Load Error: {e}")

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

            if model:
                ai = model.generate_content(f"Reply in same language: {user_text}")
                reply = ai.text
            else:
                reply = f"Bot is ON! You said: {user_text}. (Add GEMINI_API_KEY for AI reply)"

            url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {"messaging_product":"whatsapp","to":from_num,"text":{"body":reply}}
            requests.post(url, json=payload, headers=headers)
            print(f"Sent: {reply}")
    except Exception as e:
        print(f"Webhook Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
