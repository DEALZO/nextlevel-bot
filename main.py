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
            user_text = msg.get("image",{}).get("caption","Wooden product image")

        # Try 2 models - pehla fail to dusra
        ai_reply = None
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are NextLevel Agency Quetta. You sell websites for wooden furniture. Reply in Roman Urdu, short, smart, never repeat same line. If user asks price say Website 25k, FB Ads 15k/month. If image, praise carving."},
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
            ai_reply = "Bhai wooden ka design zabardast hai! Website 25k me bana dunga, Shopify + WhatsApp order + COD. Quetta me delivery hai?"

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
