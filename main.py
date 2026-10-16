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
    # TRY 1: Ollama Cloud - Native API (Most Stable)
    if OLLAMA_API_KEY:
        try:
            url = "https://ollama.com/api/chat"
            headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "llama3.1", "messages": [{"role": "user", "content": prompt}], "stream": False}
            r = requests.post(url, headers=headers, json=payload, timeout=45)
            print(f"[OLLAMA NATIVE] {r.status_code} - {r.text[:400]}")
            if r.status_code == 200:
                data = r.json()
                return data.get("message", {}).get("content") or data.get("response")
        except Exception as e:
            print(f"Ollama Native Error: {e}")

        # TRY 2: Ollama Cloud - OpenAI Compatible
        try:
            url = "https://ollama.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "llama3.1", "messages": [{"role": "user", "content": prompt}]}
            r = requests.post(url, headers=headers, json=payload, timeout=45)
            print(f"[OLLAMA OPENAI] {r.status_code} - {r.text[:400]}")
            if r.status_code == 200:
                data = r.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Ollama OpenAI Error: {e}")

    # TRY 3: Groq (Backup - 100% Working)
    if GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            chat = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
            print("[GROQ] Success")
            return chat.choices[0].message.content
        except Exception as e:
            print(f"Groq Error: {e}")
    
    return "Bhai API keys ka masla hai. Railway me OLLAMA_API_KEY ya GROQ_API_KEY sahi se lagao."

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
                    text = msg.get("text", {}).get("body", "") if msg.get("type") == "text" else f"User sent {msg.get('type')}"
                    
                    if phone not in user_memory: user_memory[phone] = []
                    user_memory[phone].append(text)
                    user_memory[phone] = user_memory[phone][-5:]
                    
                    context = " ".join(user_memory[phone])
                    reply = ask_ai(f"History: {context}\nNew: {text}\nReply short in same language (Urdu/Hindi/English) as friendly bot.")
                    send_whatsapp(phone, reply)
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "Bot Running - Ollama + Groq Ready", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
