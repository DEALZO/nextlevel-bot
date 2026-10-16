from flask import Flask, request, jsonify
import whisper
import wikipedia
import requests

app = Flask(__name__)

# === CONFIG ===
OLLAMA_API_KEY = "PASTE_YOUR_KEY_HERE"  # Jo tumne Create API key se li
OLLAMA_URL = "https://api.ollama.com/api/generate"
model = whisper.load_model("base") # Audio ke liye

user_memory = {}

# Ollama se baat karne ka function
def ask_ollama(prompt):
    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    payload = {"model": "llava", "prompt": prompt, "stream": False}
    try:
        r = requests.post(OLLAMA_URL, headers=headers, json=payload)
        return r.json().get('response', 'Error')
    except Exception as e:
        return f"Ollama Error: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    phone = data.get('from')
    msg_type = data.get('type', 'text')
    text = data.get('text', '')

    if phone not in user_memory:
        user_memory[phone] = []

    reply = ""

    # 1. Audio Transcribe
    if msg_type == "audio":
        result = model.transcribe("temp.mp3") # file download logic tumhara
        reply = ask_ollama(f"User said: {result['text']}. Reply in friendly way.")
    
    # 2. Image Understand
    elif msg_type == "image":
        reply = ask_ollama("Describe what you see in this image for a customer support bot.")
    
    # 3. Long text Summarize
    elif len(text) > 200:
        reply = ask_ollama(f"Summarize this long message: {text}")

    # 4. Wikipedia
    elif "wikipedia" in text.lower():
        try:
            reply = wikipedia.summary(text.replace("wikipedia",""), sentences=2)
        except:
            reply = ask_ollama(text)

    # 5. Normal chat + Memory
    else:
        user_memory[phone].append(text)
        context = " ".join(user_memory[phone][-5:])
        reply = ask_ollama(f"Chat history: {context} \n New message: {text} \n Reply as WhatsApp support bot.")

    # Auto Reply
    print(f"Reply to {phone}: {reply}")
    # yahan tumhara whatsapp send wala function ayega
    # send_whatsapp(phone, reply)
    
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(port=5000)
