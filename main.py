import os, requests, json, datetime
from flask import Flask, request, jsonify
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

# File me chats save hogi
CHAT_FILE = "chat_history.json"

def save_chat(number, user_msg, bot_reply):
    data = []
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r") as f:
                data = json.load(f)
        except: data = []
    data.append({
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "number": number,
        "user": user_msg,
        "bot": bot_reply
    })
    with open(CHAT_FILE, "w") as f:
        json.dump(data[-500:], f, indent=2) # last 500 chats

@app.route("/")
def home(): return "Bot FIXED LIVE - Next Gen Agency", 200

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
        except: data = []
    data.append({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"number": number,"user": user_msg,"bot": bot_reply})
    with open(CHAT_FILE, "w") as f:
        json.dump(data[-500:], f, indent=2)

@app.route("/")
def home(): return "Bot FIXED LIVE - Next Gen Agency", 200

@app.route("/chats")
def view_chats():
    if not os.path.exists(CHAT_FILE):
        return "<h2 style='font-family:sans-serif;text-align:center;margin-top:50px'>Abhi tak koi chat nahi hui</h2>"
    with open(CHAT_FILE, "r") as f:
        chats = json.load(f)
    grouped = defaultdict(list)
    for c in chats:
        grouped[c['number']].append(c)
    html = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Segoe UI,sans-serif;background:#111b21;margin:0}.header{background:#202c33;color:white;padding:15px;font-size:18px;font-weight:bold;position:sticky;top:0}.container{display:flex;height:calc(100vh - 53px)}.sidebar{width:30%;background:#111b21;border-right:1px solid #2a3942;overflow-y:auto}.contact{padding:12px 15px;color:#e9edef;border-bottom:1px solid #2a3942;cursor:pointer}.contact:hover{background:#2a3942}.contact.active{background:#2a3942}.chat-area{width:70%;background:#0b141a url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');display:flex;flex-direction:column}.messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:8px}.bubble{max-width:60%;padding:8px 12px;border-radius:8px;font-size:14.2px;line-height:19px;box-shadow:0 1px 0.5px rgba(0,0,0,0.13)}.user{background:#202c33;color:#e9edef;align-self:flex-start;border-top-left-radius:0}.bot{background:#005c4b;color:#e9edef;align-self:flex-end;border-top-right-radius:0}.time{font-size:11px;color:#8696a0;margin-top:4px;text-align:right}</style></head><body><div class="header">📱 Next Gen Agency - Live Chats (03196854972)</div><div class="container"><div class="sidebar" id="sidebar"></div><div class="chat-area"><div class="messages" id="messages"><p style='color:#8696a0;text-align:center;margin-top:100px'>Kisi number par click karo chat dekhne ke liye 👈</p></div></div></div><script>const data = """ + json.dumps(dict(grouped)) + """;const sidebar=document.getElementById('sidebar');const messagesDiv=document.getElementById('messages');Object.keys(data).forEach((num,idx)=>{const div=document.createElement('div');div.className='contact'+(idx==0?' active':'');const last=data[num][data[num].length-1];div.innerHTML=`<b>${num}</b><br><small style='color:#8696a0'>${last.user.slice(0,25)}...</small>`;div.onclick=()=>{document.querySelectorAll('.contact').forEach(c=>c.classList.remove('active'));div.classList.add('active');showChat(num)};sidebar.appendChild(div);});function showChat(num){messagesDiv.innerHTML='';data[num].forEach(c=>{messagesDiv.innerHTML+=`<div class="bubble user">${c.user}<div class="time">${c.time}</div></div><div class="bubble bot">${c.bot}<div class="time">✓✓ ${c.time.split(' ')[1]}</div></div>`;});messagesDiv.scrollTop=messagesDiv.scrollHeight;}if(Object.keys(data).length>0)showChat(Object.keys(data)[0]);</script></body></html>"""
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
        if "messages" not in entry: return "OK", 200
        msg = entry["messages"][0]
        from_num = msg["from"]
        phone_id = entry["metadata"]["phone_number_id"]
        user_text = msg["text"]["body"] if msg.get("type") == "text" else msg.get("image",{}).get("caption","")
        ai_reply = None
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {"model": model, "messages": [{"role": "system", "content": "You are Next Gen Agency bot 03196854972. INTRO on Hello: Wa Alaikum Salam! Next Gen Agency me khush amdeed, hum 2000+ businesses ko online laa chuke hain aur 1300+ clients hamara AI ChatBot use kar rahe hain. DO NOT give price on hello. If website asked: 10k -> 3k in 70% OFF. If bot asked: 5k -> 1.5k. Combo both 3800. If links asked: excuse NDA/privacy, no fake links, ask their idea/design. Never mention Shopify/WordPress unless forced then say Custom website. Never furniture."}, {"role": "user", "content": user_text}]}
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                    break
            except: continue
        if not ai_reply:
            ai_reply = "Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀 Hum 2000+ businesses ko online laa chuke hain."
        save_chat(from_num, user_text, ai_reply)
        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})
    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

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

        ai_reply = None
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Next Gen Agency... (yahan tumhara wala hi prompt rahega jo pehle diya tha)"},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                    break
            except: continue

        if not ai_reply:
            ai_reply = "Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀 Hum 2000+ businesses ko online laa chuke hain."

        # Chat save karo
        save_chat(from_num, user_text, ai_reply)
        print(f"CHAT {from_num}: {user_text} -> {ai_reply}")

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
