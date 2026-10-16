from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

user_memory = {}

def ask_ai(prompt):
    # TRY 1: Ollama Cloud - Free plan wala model (Logs me isi ka naam aaya hai)
    if OLLAMA_API_KEY:
        try:
            url = "https://ollama.com/api/chat"
            headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}
            # FIX: Free plan ke liye gemma3:4b
            payload = {"model": "gemma3:4b", "messages": [{"role": "user", "content": prompt}], "stream": False}
            r = requests.post(url, headers=headers, json=payload, timeout=45)
            print(f"[OLLAMA] {r.status_code} - {r.text[:500]}")
            if r.status_code == 200:
                data = r.json()
                return data.get("message", {}).get("content")
        except Exception as e:
            print(f"Ollama Error: {e}")

    # TRY 2: Groq - Naya model jo abhi working hai
    if GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            # FIX: llama-3.3-70b-versatile - ye Groq pe abhi active hai
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[{"role": "user", "content": prompt}]
            )
            print("[GROQ] Success")
            return chat.choices[0].message.content
        except Exception as e:
            print(f"Groq Error: {e}")
            # Second try with older model
            try:
                client = Groq(api_key=GROQ_API_KEY)
                chat = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": prompt}])
                return chat.choices[0].message.content
            except Exception as e2:
                print(f"Groq 2nd Error: {e2}")
    
    return "Bhai AI thoda busy hai, 1 minute baad try karo."

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": str(text)[:4000]}}
    r = requests.post(url, headers=headers, json=payload)
    print(f"[WHATSAPP SEND] {r.status_code} {r.text}")

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Incoming: {data}")
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    phone = msg.get("from")
                    if msg.get("type") != "text": continue
                    text = msg.get("text", {}).get("body", "")
                    
                    if phone not in user_memory: user_memory[phone] = []
                    user_memory[phone].append(text)
                    user_memory[phone] = user_memory[phone][-5:]
                    
                    reply = ask_ai(f"History: {' '.join(user_memory[phone])}\nUser: {text}\nReply in same language short.")
                    send_whatsapp(phone, reply)
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "Bot Running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
