from flask import Flask, request, jsonify
import os, requests
from groq import Groq

app = Flask(__name__)

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

user_memory = {}

def ask_ai(prompt):
    if not GROQ_API_KEY:
        return "GROQ_API_KEY missing hai"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        # NEW MODEL - 2026 me ye active hai
        chat = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        print(f"[GROQ SUCCESS] {chat.choices[0].message.content[:100]}")
        return chat.choices[0].message.content
    except Exception as e:
        print(f"[GROQ ERROR 1] {e}")
        try:
            # Backup model
            client = Groq(api_key=GROQ_API_KEY)
            chat = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}]
            )
            return chat.choices[0].message.content
        except Exception as e2:
            print(f"[GROQ ERROR 2] {e2}")
            return f"Error: {e2}"

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": str(text)[:4000]}}
    r = requests.post(url, headers=headers, json=payload)
    print(f"[WHATSAPP SEND] {r.status_code}")

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    phone = msg.get("from")
                    if msg.get("type") != "text": continue
                    text = msg.get("text", {}).get("body", "")
                    
                    if phone not in user_memory: user_memory[phone] = []
                    user_memory[phone].append(text)
                    user_memory[phone] = user_memory[phone][-5:]
                    
                    reply = ask_ai(f"Reply short in same language: {text}")
                    send_whatsapp(phone, reply)
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home(): return "Bot Running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
