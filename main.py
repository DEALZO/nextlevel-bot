from flask import Flask, request, jsonify
import os, requests
from groq import Groq

app = Flask(__name__)

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

user_memory = {}
processed_ids = set() # Duplicate message rokne ke liye

def ask_ai(prompt):
    client = Groq(api_key=GROQ_API_KEY)
    # System prompt se same reply khatam hoga
    chat = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are NextLevel-Bot, a friendly helpful assistant. NEVER repeat the user's exact word. If user says 'Helo', reply 'Helo! Kese ho? Batao kya help chahiye?'. Always give a full helpful sentence, not just one word. Reply in same language as user."},
            {"role": "user", "content": prompt}
        ]
    )
    reply = chat.choices[0].message.content
    # Agar phir bhi same hua to force change
    if reply.strip().lower() == prompt.strip().lower():
        return "Hi! Batao kya haal hai? Main NextLevel Bot hun, kese madad karun?"
    return reply

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": str(text)[:4000]}}
    r = requests.post(url, headers=headers, json=payload)
    print(f"[WHATSAPP SEND to {to}] {r.status_code}")

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
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    # Duplicate webhook rokna
                    msg_id = msg.get("id")
                    if msg_id in processed_ids: continue
                    processed_ids.add(msg_id)
                    if len(processed_ids) > 100: processed_ids.clear()

                    phone = msg.get("from")
                    if msg.get("type") != "text": continue
                    text = msg.get("text", {}).get("body", "")

                    print(f"User {phone} says: {text}")
                    reply = ask_ai(text)
                    send_whatsapp(phone, reply)
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home(): return "Bot Running - Same Reply Fixed", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
