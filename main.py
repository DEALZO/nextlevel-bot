from flask import Flask, request, jsonify
import os, requests, base64
from groq import Groq

app = Flask(__name__)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN","").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID","").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN","nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY","").strip()

processed = set()

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text[:4000]}}
    r = requests.post(url, headers=headers, json=payload)
    print(f"[SEND] to {to} status {r.status_code} resp {r.text[:500]}")
    return r.status_code

def ask_text(q):
    client = Groq(api_key=GROQ_API_KEY)
    # YE MODELS 100% GROQ FREE PE WORK KARTE HAIN
    for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        try:
            print(f"Trying text model {model}")
            c = client.chat.completions.create(
                model=model,
                messages=[
                    {"role":"system","content":"You are NextLevel sales bot. You sell websites and AI WhatsApp chatbots. Reply in Roman Urdu, short, sales tone. Never repeat user text as is."},
                    {"role":"user","content":q}
                ]
            )
            print(f"[TEXT SUCCESS {model}]")
            return c.choices[0].message.content
        except Exception as e:
            print(f"[TEXT FAIL {model}] {e}")
            continue
    return None

def ask_vision(b64, caption):
    client = Groq(api_key=GROQ_API_KEY)
    for model in ["meta-llama/llama-3.2-11b-vision-preview", "meta-llama/llama-3.2-90b-vision-preview"]:
        try:
            print(f"Trying vision model {model}")
            c = client.chat.completions.create(
                model=model,
                messages=[{
                    "role":"user",
                    "content":[
                        {"type":"text","text": f"Describe this image and sell website/chatbot service in Roman Urdu. Caption: {caption}"},
                        {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                    ]
                }]
            )
            print(f"[VISION SUCCESS {model}]")
            return c.choices[0].message.content
        except Exception as e:
            print(f"[VISION FAIL {model}] {e}")
            continue
    return "Is pic jaisi website hum bana sakte hain Rs 20k me. Detail batao?"

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"WEBHOOK DATA {data}")
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("id") in processed: 
                        print("Duplicate, skip")
                        continue
                    processed.add(msg.get("id"))
                    
                    phone = msg.get("from")
                    print(f"NEW MSG type={msg.get('type')} from={phone}")

                    if msg.get("type") == "text":
                        txt = msg.get("text",{}).get("body","")
                        ans = ask_text(txt)
                        if ans:
                            send_whatsapp(phone, ans)
                        else:
                            send_whatsapp(phone, f"Groq Error: Model not found. Check GROQ_API_KEY. Your text: {txt}")

                    elif msg.get("type") == "image":
                        send_whatsapp(phone, "Pic mil gayi, check kar raha hun...")
                        try:
                            mid = msg.get("image",{}).get("id")
                            cap = msg.get("image",{}).get("caption","")
                            # download
                            h = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
                            r1 = requests.get(f"https://graph.facebook.com/v20.0/{mid}", headers=h, timeout=30).json()
                            media_url = r1.get("url")
                            r2 = requests.get(media_url, headers=h, timeout=30)
                            b64 = base64.b64encode(r2.content).decode('utf-8')
                            ans = ask_vision(b64, cap)
                            send_whatsapp(phone, ans)
                        except Exception as e:
                            print(f"IMAGE ERR {e}")
                            send_whatsapp(phone, f"Image download error: {e}")
    except Exception as e:
        print(f"MAIN WEBHOOK ERR {e}")
    return jsonify({"status":"ok"}), 200

@app.route('/')
def home(): return "NextLevel Bot - Text+Image Fixed", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8000)))
