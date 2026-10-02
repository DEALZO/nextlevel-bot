import os, requests
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

@app.route("/")
def home(): return "Bot FIXED LIVE", 200

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
        if "messages" not in entry: return "OK", 200
        msg = entry["messages"][0]
        from_num = msg["from"]
        phone_id = entry["metadata"]["phone_number_id"]

        if msg.get("type") == "text":
            user_text = msg["text"]["body"]
        else:
            user_text = msg.get("image",{}).get("caption","")

        # Try 2 models - pehla fail to dusra
        ai_reply = None
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": """
You are Next Gen Agency Sales Bot for 03196854972.

OFFER: MEGA OFFER 70% OFF - Sirf 3 Din Ke Liye!

Services & Price:
1. Professional Website: Actual Rs. 10,000 -> Now Rs. 3,000 Only
2. AI WhatsApp ChatBot: Actual Rs. 5,000 -> Now Rs. 1,500 Only
3. Combo Deal Website + Bot = Rs. 4,500 Only

INTERNAL RULE - IMPORTANT:
- Never mention WordPress, Shopify or any platform by yourself. Khud se platform ka naam mat lena.
- If user forcefully asks 'kis par banao ge? Shopify? WordPress?' tab hi bolna: 'Sir ye Fully Custom Website hogi, aapki requirement ke mutabiq banegi.'
- Reply in Roman Urdu, short, smart.
- Furniture ka zikr kabhi mat karna.
- Always tell to order on 03196854972.
"""},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                print(f"TRY {model}: {j}")
                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                    break
            except Exception as e:
                print(f"Model {model} fail: {e}")
                continue

        if not ai_reply:
            ai_reply = "Salam! Next Gen Agency me khush amdeed 🚀\n\nMEGA OFFER 70% OFF - Sirf 3 Din!\nWebsite: 10,000 -> 3,000 Only\nChatBot: 5,000 -> 1,500 Only\nCombo: 4,500 Only\n\nOrder ke liye apna naam bhejein!"

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
