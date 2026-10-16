from flask import Flask, request, jsonify
import os, requests
from groq import Groq

app = Flask(__name__)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "nextlevel123").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

processed_ids = set()

# TUMHARA BUSINESS PROMPT
SYSTEM_PROMPT = """
You are NextLevel-Bot, sales agent for NextLevel Digital.

Business:
1. We sell Professional Websites (Business, E-commerce, Portfolio) - Starting Rs 15k
2. We sell AI WhatsApp Chatbots like yourself for businesses.

Your Goal: User ko client banana.
- User agar 'Helo / Hi' kahe to: 'Salam! Main NextLevel Bot hun. Hum professional websites aur AI chatbots banate hain jo aapki sales 10x kar dete hain. Aapko kis cheez me interest hai? 1. Website 2. AI Bot'
- Price puche to packages batao, cheap mat bolo, value batao.
- Hamesha Urdu Roman / English mix me short, friendly, sales tone me jawab do.
- Kabhi bhi user ka same word repeat mat karo.
- Last me hamesha CTA do: 'Kya apko demo dikhaun?'
"""

def ask_ai(user_msg):
    client = Groq(api_key=GROQ_API_KEY)
    chat = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.7
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
                    if msg.get("type") != "text": continue
                    
                    phone = msg.get("from")
                    text = msg.get("text", {}).get("body", "")
                    
                    reply = ask_ai(text)
                    send_whatsapp(phone, reply)
    except Exception as e:
        print(e)
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home(): return "NextLevel Sales Bot Running", 200
