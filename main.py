import os, requests, threading
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

def reply_later(phone_id, to, user_text):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role":"system","content":"You are NextLevel Agency Quetta, wooden furniture website expert. Reply in short Roman Urdu. If user says talk to human, say 'Zaroor, team ko inform kar diya hai, 10 min me call ayegi, apna naam/number de dein'. Never say you are AI."},
                {"role":"user","content": user_text}
            ],
            "max_tokens": 250
        }
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        j = r.json()
        if "choices" in j:
            ai_reply = j["choices"][0]["message"]["content"]
        else:
            print(f"GROQ ERROR: {j}")
            ai_reply = "Bhai thora network busy hai, 2 min me reply deta hun. Aap apna naam bhej dein?"

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        wa_headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        wa_data = {"messaging_product":"whatsapp","to":to,"text":{"body":ai_reply}}
        requests.post(wa_url, headers=wa_headers, json=wa_data, timeout=10)
        print(f"Sent to {to}: {ai_reply}")

    except Exception as e:
        print(f"Reply thread error: {e}")

@app.route("/", methods=["GET"])
def home(): return "Bot STABLE v3 LIVE", 200

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
        user_text = msg["text"]["body"] if msg.get("type")=="text" else "image"

        # IMPORTANT: Pehle OK bhejo, phir background me reply karo
        threading.Thread(target=reply_later, args=(phone_id, from_num, user_text)).start()

    except Exception as e:
        print(f"Webhook error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
