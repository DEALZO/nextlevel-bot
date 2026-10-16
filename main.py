from flask import Flask, request, jsonify
import os, requests, base64
from groq import Groq

app = Flask(__name__)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

processed_ids = set()

SYSTEM_PROMPT = """
You are NextLevel-Bot, sales agent for NextLevel Digital.
Business: 1. Professional Websites (Rs 15k se start) 2. AI WhatsApp Chatbots.
Goal: User ko client banana. Agar user pic bheje to us pic ko describe karo aur bolo ke 'Is tarah ki website/bot hum bana sakte hain'. Hamesha Urdu Roman + English mix me short sales reply do.
NEVER repeat same word. Always give helpful full sentence.
"""

def get_image_base64(media_id):
    try:
        # Step 1: Get media URL from WhatsApp
        url = f"https://graph.facebook.com/v20.0/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=20)
        media_url = r.json().get("url")
        if not media_url: return None
        
        # Step 2: Download image
        r2 = requests.get(media_url, headers=headers, timeout=20)
        return base64.b64encode(r2.content).decode('utf-8')
    except Exception as e:
        print(f"Image Download Error: {e}")
        return None

def ask_ai_text(user_msg):
    client = Groq(api_key=GROQ_API_KEY)
    chat = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]
    )
    return chat.choices[0].message.content

def ask_ai_image(image_b64, caption="Is pic me kya hai?"):
    client = Groq(api_key=GROQ_API_KEY)
    # Vision model - pic read kar sakta hai
    chat = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": caption},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ]
    )
    return chat.choices[0].message.content

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000]}}
    requests.post(url, headers=headers, json=payload)

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
                    if msg.get("id") in processed_ids: continue
                    processed_ids.add(msg.get("id"))

                    phone = msg.get("from")
                    
                    # CASE 1: TEXT MESSAGE
                    if msg.get("type") == "text":
                        text = msg.get("text", {}).get("body", "")
                        print(f"TEXT from {phone}: {text}")
                        reply = ask_ai_text(text)
                        send_whatsapp(phone, reply)

                    # CASE 2: IMAGE MESSAGE - YE NAYA HAI
                    elif msg.get("type") == "image":
                        media_id = msg.get("image", {}).get("id")
                        caption = msg.get("image", {}).get("caption", "Is pic ke baare me batao")
                        print(f"IMAGE from {phone}: {media_id}")
                        send_whatsapp(phone, "Pic mil gayi, 2 sec me analysis kar raha hun...")

                        b64 = get_image_base64(media_id)
                        if b64:
                            reply = ask_ai_image(b64, caption)
                        else:
                            reply = "Pic download nahi ho saki, dobara bhejo."
                        send_whatsapp(phone, reply)

    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home(): return "Bot with Image Support Running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
