from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# === CONFIG - Railway Variables se ===
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "") # Isko Railway Variables me add karna
OLLAMA_URL = "https://api.ollama.com/v1/chat/completions"

user_memory = {}

def ask_ollama(prompt):
    if not OLLAMA_API_KEY:
        return "Ollama API Key set nahi hai. Railway Variables me OLLAMA_API_KEY add karo."
    
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3.2",  # llava ki jagah ye tez aur sasta hai, image ke liye llava use karna
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        r = requests.post(OLLAMA_URL, headers=headers, json=payload, timeout=30)
        data = r.json()
        # Ollama Cloud API ka response
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        return data.get('response', str(data))
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "Sorry, AI thoda busy hai, dobara koshish karo."

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
        "text": {"body": text[:4000]}  # WhatsApp limit
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        print(f"WhatsApp Send Status: {r.text}")
    except Exception as e:
        print(f"Send Error: {e}")

# 1. Verification ke liye - Meta ye call karta hai
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

# 2. Messages ke liye
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
                        text = "[User sent a voice note, transcription currently disabled for Railway]"
                    elif msg_type == "image":
                        text = "[User sent an image] Describe it friendly."
                    else:
                        text = f"User sent {msg_type}"

                    if not text:
                        continue

                    # Memory + Ollama
                    user_memory[phone].append(text)
                    if len(user_memory[phone]) > 5:
                        user_memory[phone] = user_memory[phone][-5:]
                    
                    context = " ".join(user_memory[phone])
                    
                    # Wikipedia check
                    if "wikipedia" in text.lower():
                        import wikipedia
                        try:
                            q = text.lower().replace("wikipedia","").strip()
                            reply = wikipedia.summary(q, sentences=2)
                        except:
                            reply = ask_ollama(f"Chat history: {context}\nNew: {text}\nReply as friendly WhatsApp bot in same language user used.")
                    elif len(text) > 300:
                        reply = ask_ollama(f"Summarize this in 2 lines: {text}")
                    else:
                        reply = ask_ollama(f"Chat history: {context}\nNew message: {text}\nReply as friendly WhatsApp support bot. Keep it short.")

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
