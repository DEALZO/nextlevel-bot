import os, requests, json, datetime
from collections import defaultdict
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
        return "<h2 style='text-align:center'>Abhi tak koi chat nahi hui</h2>"
    try:
        with open(CHAT_FILE, "r") as f:
            chats = json.load(f)
    except:
        return "No chats"

    grouped = defaultdict(list)
    for c in chats:
        grouped[c["number"]].append(c)

    selected_num = request.args.get("num")

    # Agar kisi number par click kiya hai to uski puri chat dikhao
    if selected_num:
        if selected_num not in grouped:
            return f"<h3>Number {selected_num} not found</h3><a href='/chats'>Back</a>"

        html = f"""
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body{{margin:0;font-family:Arial;background:#e5ddd5}}
      .header{{background:#075e54;color:white;padding:12px;position:sticky;top:0;display:flex;align-items:center}}
      .header a{{color:white;text-decoration:none;margin-right:15px;font-size:22px}}
      .chat{{padding:10px 15px;padding-bottom:80px}}
      .bubble{{max-width:70%;padding:8px 10px;margin:5px 0;border-radius:8px;font-size:14px;line-height:18px;box-shadow:0 1px 1px rgba(0,0,0,0.2);clear:both;word-wrap:break-word}}
      .user{{float:left;background:white;border-top-left-radius:0}}
      .bot{{float:right;background:#dcf8c6;border-top-right-radius:0}}
      .time{{font-size:10px;color:gray;text-align:right;margin-top:4px}}
      .clr{{clear:both}}
        </style></head><body>
        <div class="header"><a href="/chats">←</a> {selected_num} - Next Gen Agency</div>
        <div class="chat">
        """
        for c in grouped[selected_num]:
            html += f"<div class='bubble user'>{c['user']}<div class='time'>{c['time']}</div></div><div class='clr'></div>"
            html += f"<div class='bubble bot'>{c['bot']}<div class='time'>✓✓ Bot</div></div><div class='clr'></div>"

        html += "</div></body></html>"
        return html

    # Agar koi number select nahi kiya to saare numbers ki list dikhao
    else:
        html = """
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body{margin:0;font-family:Arial;background:white}
      .header{background:#075e54;color:white;padding:15px;font-size:18px;font-weight:bold}
      .contact{padding:15px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;text-decoration:none;color:black}
      .contact:hover{background:#f5f5f5}
      .name{font-weight:bold;font-size:16px}
      .last{color:gray;font-size:13px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px}
      .count{background:#25d366;color:white;border-radius:50%;padding:2px 7px;font-size:12px}
        </style></head><body>
        <div class="header">📱 Next Gen Agency Chats (03196854972) - Total: """ + str(len(grouped)) + """ contacts</div>
        """
        # latest first
        for num, msgs in sorted(grouped.items(), key=lambda x: x[1][-1]['time'], reverse=True):
            last_msg = msgs[-1]['user'][:30]
            html += f"<a class='contact' href='/chats?num={num}'><div><div class='name'>{num}</div><div class='last'>{last_msg}</div></div><div class='count'>{len(msgs)}</div></a>"

        html += "</body></html>"
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
            except:
                continue

        if not ai_reply:
            ai_reply = "Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀"

        save_chat(from_num, user_text, ai_reply)

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
