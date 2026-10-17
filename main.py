from flask import Flask, request, jsonify
import os, requests, base64
from groq import Groq

app = Flask(__name__)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

processed = set()

def send(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    h = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    p = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000]}}
    requests.post(url, headers=h, json=p)

def get_b64(media_id):
    h = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r1 = requests.get(f"https://graph.facebook.com/v20.0/{media_id}", headers=h, timeout=30).json()
    url = r1.get("url")
    r2 = requests.get(url, headers=h, timeout=30)
    return base64.b64encode(r2.content).decode('utf-8')

def ask_text(q):
    client = Groq(api_key=GROQ_API_KEY)
    models = ["openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama3-8b-8192"]
    for m in models:
        try:
            c = client.chat.completions.create(model=m, messages=[{"role":"user","content":q}])
            print(f"[TEXT OK {m}]")
            return c.choices[0].message.content
        except Exception as e:
            print(f"[TEXT FAIL {m}] {e}")
            continue
    return "Bot busy hai, 1 min baad try karo"

def ask_vision(b64, caption):
    client = Groq(api_key=GROQ_API_KEY)
    models = ["meta-llama/llama-3.2-11b-vision-preview", "meta-llama/llama-3.2-90b-vision-preview"]
    for m in models:
        try:
            c = client.chat.completions.create(
                model=m,
                messages=[{"role":"user","content":[
                    {"type":"text","text": f"You are NextLevel sales bot. Sell websites & AI bots. User caption: {caption}. Describe image in Roman Urdu and pitch service."},
                    {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                ]}]
            )
            print(f"[VISION OK {m}]")
            return c.choices[0].message.content
        except Exception as e:
            print(f"[VISION FAIL {m}] {e}")
            continue
    return "Pic ka analysis nahi ho saka, Groq vision model access nahi de raha. Lekin is jaisi website hum Rs 20k me bana denge."

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(data)
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    if msg.get("id") in processed: continue
                    processed.add(msg.get("id"))
                    phone = msg.get("from")

                    if msg.get("type") == "text":
                        txt = msg.get("text",{}).get("body","")
                        print(f"TEXT {phone}: {txt}")
                        reply = ask_text(f"Reply in Roman Urdu sales tone for website & AI chatbot business: {txt}")
                        send(phone, reply)

                    elif msg.get("type") == "image":
                        print(f"IMAGE {phone}")
                        send(phone, "Pic mil gayi, 3 sec...")
                        try:
                            b64 = get_b64(msg.get("image",{}).get("id"))
                            cap = msg.get("image",{}).get("caption","")
                            reply = ask_vision(b64, cap)
                            send(phone, reply)
                        except Exception as e:
                            print(f"IMG ERR {e}")
                            send(phone, f"Pic error: {e}")

    except Exception as e:
        print(f"MAIN ERR {e}")
    return jsonify({"status":"ok"}), 200

@app.route('/')
def home(): return "Bot Running Final", 200
