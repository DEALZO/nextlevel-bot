from flask import Flask, request
import requests
import os
from supabase import create_client

app = Flask(__name__)

# ====== APNI KEYS YAHAN DALO ======
VERIFY_TOKEN = "nextlevel123" # ye koi bhi random word rakh lo
WHATSAPP_TOKEN = "EAANh16U4nYYBSTSNwY605ljGeADRl9qaqGzg80lmwpeMIzRR5fZA15WZA92H6gZCau8r4bF88S1wPbeQqq1ripzH8Er7cOEVZCiifmA9ab0Gt4pIvPZCvMpzNoJKZAfLEGlbb312ynrtorO0qVNmbQZCsgZCRAqy8dfidOLksB6nXXJM8Qw0SexuLBZC4BUZApUvKOIZBxZAcB89Jtoram1ZBXo3pJ81EZCIykeirZCTZAwdziyLHZBfg4dUzIseuRZC97sbSx5II1QKartVDDLpoqZBDz8WhXJ70Ht" 
PHONE_NUMBER_ID = "1256713407533438"

SUPABASE_URL = "https://kwlgmlxfoemvnetwvxbl.supabase.co"
SUPABASE_KEY = "sb_publishable_5hrsp4_Kc41nL-brptXKXw_2kqAK84l"
# ===================================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge')
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('entry'):
        for entry in data['entry']:
            for change in entry['changes']:
                if 'messages' in change['value']:
                    message = change['value']['messages'][0]
                    from_number = message['from']
                    text = message['text']['body']
                    
                    # 1. Log in Supabase
                    supabase.table('bot_logs').insert({
                        "from_phone": from_number, 
                        "message": text
                    }).execute()
                    
                    # 2. Customer save/update
                    supabase.table('customers').upsert({
                        "phone": from_number, 
                        "status": "lead"
                    }).execute()
                    
                    # 3. Auto Reply
                    reply = f"Assalamualaikum! Aapka message mil gaya: '{text}'. Hum jald rabta karenge."
                    send_whatsapp_message(from_number, reply)
    return "ok"

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)