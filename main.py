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

# YE NAYA PAGE HAI JAHAN SAARI CHATS DEKHOGE
@app.route("/chats")
def view_chats():
    if not os.path.exists(CHAT_FILE):
        return "Abhi tak koi chat nahi hui"
    with open(CHAT_FILE, "r") as f:
        chats = json.load(f)
    html = "<h1>Next Gen Agency - Chat History (03196854972)</h1><hr>"
    for c in reversed(chats):
        html += f"<b>{c['time']} - {c['number']}</b><br>User: {c['user']}<br>Bot: {c['bot']}<br><hr>"
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
