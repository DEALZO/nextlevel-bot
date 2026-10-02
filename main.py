import os, requests, json, datetime
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()
CHAT_FILE = "chat_history.json"

def save_chat(number, user_msg, bot_reply):
    data = []
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r") as f:
                data = json.load(f)
        except:
            data = []
    data.append({
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "number": number,
        "user": user_msg,
        "bot": bot_reply
    })
    try:
        with open(CHAT_FILE, "w") as f:
            json.dump(data[-500:], f, indent=2)
    except:
        pass

@app.route("/")
def home():
    return "Bot FIXED LIVE - Next Gen Agency", 200

@app.route("/chats")
def view_chats():
    if not os.path.exists(CHAT_FILE):
        return "<h2 style='text-align:center;margin-top:50px'>Abhi tak koi chat nahi hui</h2>"
    try:
        with open(CHAT_FILE, "r") as f:
            chats = json.load(f)
    except:
        return "File error"

    html = """
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{margin:0;font-family:Arial;background:#efeae2}
   .header{background:#008069;color:white;padding:15px;font-size:18px;font-weight:bold;text-align:center}
   .msg{max-width:80%;margin:10px;padding:10px 15px;border-radius:8px;font-size:15px;clear:both}
   .user{float:left;background:white;color:black;border-radius:0 8px 8px 8px}
   .bot{float:right;background:#d9fdd3;color:black;border-radius:8px 0 8px 8px}
   .meta{font-size:11px;color:gray;margin-top:5px}
   .wrap{padding:10px;overflow:auto}
    </style></head><body>
    <div class="header">Next Gen Agency - Chats (03196854972)</div>
    <div class="wrap">
    """
    for c in reversed(chats):
        html += f"<div class='msg user'><b>{c['number']}</b><br>{c['user']}<div class='meta'>{c['time']}</div></div>"
        html += f"<div class='msg bot'>{c['bot']}<div class='meta'>Bot</div></div><div style='clear:both'><hr style='border:none;border-top:1px solid #ddd;margin:15px 0'></div>"

    html += "</div></body></html>"
    return html

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
        if "messages" not in entry:
            return "OK", 200
        msg = entry["messages"][0]
        from_num = msg["from"]
        phone_id = entry["metadata"]["phone_number_id"]
        user_text = msg["text"]["body"] if msg.get("type") == "text" else msg.get("image",{}).get("caption","")

        ai_reply = None
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Next Gen Agency bot 03196854972. INTRO on Hello: Wa Alaikum Salam! Next Gen Agency me khush amdeed, hum 2000+ businesses ko online laa chuke hain aur 1300+ clients hamara AI ChatBot use kar rahe hain. DO NOT give price on hello. If website asked: 10k -> 3k in 70% OFF. If bot asked: 5k -> 1.5k. Combo both 3800. If links asked: excuse NDA/privacy, no fake links, ask their idea/design. Never mention Shopify/WordPress unless forced then say Custom website. Never furniture. Reply Roman Urdu."},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                    break
            except Exception as e:
                print(f"Model fail {e}")
                continue

        if not ai_reply:
            ai_reply = "Wa Alaikum Salam! Next Gen Agency me khush amdeed. Hum 2000+ businesses ko online laa chuke hain aur 1300+ log hamara ChatBot use kar rahe hain. Aapko Website chahiye ya ChatBot?"

        save_chat(from_num, user_text, ai_reply)

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
