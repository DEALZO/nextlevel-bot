from flask import Flask, request, jsonify
import os, requests, base64
from groq import Groq

app = Flask(__name__)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# SIRF +92 WALA NUMBER CHALEGA, +1 IGNORE
ALLOWED_PHONE_ID = "1698117262719279"  # Tumhari photo wala ID

processed_ids = set()

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:3500]}}
    requests.post(url, headers=headers, json=payload)

def get_image_data(media_id):
    try:
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        r1 = requests.get(f"https://graph.facebook.com/v20.0/{media_id}", headers=headers, timeout=30)
        print(f"[MEDIA URL RESP] {r1.status_code} {r1.text[:500]}")
        if r1.status_code != 200:
            return None, f"Media URL Error: {r1.text}"
        media_url = r1.json().get("url")
        r2 = requests.get(media_url, headers=headers, timeout=30)
        print(f"[MEDIA DOWNLOAD] {r2.status_code} Size: {len(r2.content)}")
        if r2.status_code != 200:
            return None, f"Download Error: {r2.status_code}"
        b64 = base64.b64encode(r2.content).decode('utf-8')
        return b64, "ok"
    except Exception as e:
        print(f"[IMAGE FUNC ERROR] {e}")
        return None, str(e)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # +1 WALA KHATAM KARNE WALA FILTER
                meta = value.get("metadata", {})
                incoming_id = meta.get("phone_number_id")
                if incoming_id and incoming_id != ALLOWED_PHONE_ID:
                    print(f"[IGNORED] Test Number ID {incoming_id} - Only +92 allowed")
                    continue

                for msg in value.get("messages", []):
                    if msg.get("id") in processed_ids: continue
                    processed_ids.add(msg.get("id"))
                    phone = msg.get("from")

                    if msg.get("type") == "text":
                        client = Groq(api_key=GROQ_API_KEY)
                        user_text = msg.get("text", {}).get("body", "")
                        # WORKING MODEL
                        chat = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are NextLevel sales bot. Sell websites & AI chatbots in Roman Urdu."},
                                {"role": "user", "content": user_text}
                            ]
                        )
                        send_whatsapp(phone, chat.choices[0].message.content)

                    elif msg.get("type") == "image":
                        print(f"[GOT IMAGE] from {phone}")
                        send_whatsapp(phone, "Pic receive hui, check kar raha hun...")
                        media_id = msg.get("image", {}).get("id")
                        caption = msg.get("image", {}).get("caption", "Is pic me kya hai detail se batao")
                        b64, status = get_image_data(media_id)
                        if not b64:
                            send_whatsapp(phone, f"Pic download fail: {status}")
                            continue
                        try:
                            client = Groq(api_key=GROQ_API_KEY)
                            chat = client.chat.completions.create(
                                model="meta-llama/llama-3.2-11b-vision-preview",
                                messages=[{
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": f"SYSTEM: You are NextLevel sales bot. User sent image. Caption: {caption}. Describe image and pitch website/bot service in Roman Urdu. \n USER: {caption}"},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                                    ]
                                }],
                                max_tokens=1024
                            )
                            reply = chat.choices[0].message.content
                            print(f"[VISION SUCCESS] {reply[:100]}")
                            send_whatsapp(phone, reply)
                        except Exception as e:
                            print(f"[VISION ERROR] {e}")
                            send_whatsapp(phone, f"Vision Error: {e}. Lekin is jaisi website hum Rs 20k me bana denge.")
                            
    except Exception as e:
        print(f"Webhook Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route('/')
def home(): return "Image Debug Bot - Only +92", 200
