from flask import Flask, request, jsonify
import os, requests, base64
from groq import Groq

app = Flask(__name__)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

processed_ids = set()

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000]}}
    requests.post(url, headers=headers, json=payload)

def get_image_b64(media_id):
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r1 = requests.get(f"https://graph.facebook.com/v20.0/{media_id}", headers=headers, timeout=30)
    media_url = r1.json().get("url")
    r2 = requests.get(media_url, headers=headers, timeout=30)
    return base64.b64encode(r2.content).decode('utf-8')

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

                    # TEXT
                    if msg.get("type") == "text":
                        client = Groq(api_key=GROQ_API_KEY)
                        txt = msg.get("text", {}).get("body", "")
                        chat = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[{"role": "user", "content": txt}]
                        )
                        send_whatsapp(phone, chat.choices[0].message.content)

                    # IMAGE - FIXED MODEL
                    elif msg.get("type") == "image":
                        media_id = msg.get("image", {}).get("id")
                        caption = msg.get("image", {}).get("caption", "Is pic ko describe karo")
                        send_whatsapp(phone, "Pic mil gayi, analysis kar raha hun 2 sec...")
                        try:
                            b64 = get_image_b64(media_id)
                            client = Groq(api_key=GROQ_API_KEY)
                            # YEHI MODEL ABHI GROQ FREE PE WORK KARTA HAI
                            chat = client.chat.completions.create(
                                model="meta-llama/llama-3.2-11b-vision-preview",
                                messages=[{
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": f"You are NextLevel sales bot. Sell websites & AI chatbots. Caption: {caption}. Describe this image in Roman Urdu and pitch our service."},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                                    ]
                                }],
                                max_tokens=1024
                            )
                            send_whatsapp(phone, chat.choices[0].message.content)
                        except Exception as e:
                            print(f"[VISION ERROR FIXED] {e}")
                            send_whatsapp(phone, f"Pic ka analysis fail: {e}")
                            
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route('/')
def home(): return "Bot Image Fixed", 200
