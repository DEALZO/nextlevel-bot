from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# === CONFIG - Railway Variables se ===
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
# FIX 1: Sahi URL
OLLAMA_URL = "https://ollama.com/v1/chat/completions"

user_memory = {}

def ask_ollama(prompt):
    if not OLLAMA_API_KEY:
        return "Ollama API Key set nahi hai. Railway Variables me OLLAMA_API_KEY add karo."
    
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3.1",  # FIX 2: llama3.2 ki jagah llama3.1
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        r = requests.post(OLLAMA_URL, headers=headers, json=payload, timeout=60)
        print(f"Ollama Status: {r.status_code}")
        print(f"Ollama Response: {r.text[:500]}") # Logs me response dekho
        
        data = r.json()
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        elif 'message' in data:
            return data['message'].get('content', str(data))
        else:
            return f"Ollama Error: {data}"
    except Exception as e:
        print(f"Ollama Exception: {e}")
        return f"Sorry, AI error: {e}"

def send_whatsapp(to, text):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("WHATSAPP_TOKEN / PHONE_NUMBER_ID missing")
        return
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4000]}
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        print(f"WhatsApp Send Status: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Send Error: {e}")

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED")
        return challenge, 200
    else:
        return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Incoming: {data}")

    try:
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if not messages:
                        continue
                    
                    msg = messages[0]
                    phone = msg.get("from")
                    msg_type = msg.get("type", "")

                    if phone not in user_memory:
                        user_memory[phone] = []

                    text = ""
                    if msg_type == "text":
                        text = msg.get("text", {}).get("body", "")
                    elif msg_type == "audio":
                        text = "User sent a voice note, reply that you got voice note"
                    elif msg_type == "image":
                        text = "User sent an image, reply friendly"
                    else:
                        text = f"User sent {msg_type}"

                    if not text:
                        continue

                    user_memory[phone].append(text)
                    if len(user_memory[phone]) > 5:
                        user_memory[phone] = user_memory[phone][-5:]
                    
                    context = " ".join(user_memory[phone])
                    reply = ask_ollama(f"Chat history: {context}\nNew message: {text}\nReply as friendly WhatsApp bot in same language user used (Urdu/Hindi/English). Keep it short.")
                    
                    send_whatsapp(phone, reply)

    except Exception as e:
        print(f"Webhook Error: {e}")

    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
def home():
    return "NextLevel Bot is Running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
