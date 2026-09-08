from flask import Flask, request
import requests
import os
from supabase import create_client

app = Flask(__name__)

# ====== RAILWAY VARIABLES SE KEYS LO ======
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_ID")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
# ==========================================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/webhook', methods=['GET'])
def verify():
    """Meta webhook verification ke liye"""
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge')
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Jab customer message karega ye chalega"""
    data = request.get_json()
    if data.get('object') == 'whatsapp_business_account':
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if 'messages' in change['value']:
                    message = change['value']['messages'][0]
                    from_number = message['from']
                    
                    # Sirf text message ka reply
                    if message['type'] == 'text':
                        text = message['text']['body']
                        
                        # 1. Log in Supabase
                        try:
                            supabase.table('bot_logs').insert({
                                "from_phone": from_number, 
                                "message": text
                            }).execute()
                            
                            # 2. Customer save/update
                            supabase.table('customers').upsert({
                                "phone": from_number, 
                                "status": "lead"
                            }).execute()
                        except Exception as e:
                            print("Supabase Error:", e)
                        
                        # 3. Auto Reply
                        reply = f"Assalamualaikum! 👋\nAapka message mil gaya: '{text}'.\nHumari team jald rabta karegi. Shukriya!"
                        send_whatsapp_message(from_number, reply)
    return "ok", 200

def send_whatsapp_message(to, text):
    """WhatsApp pe message bhejta hai"""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print("WhatsApp Send Error:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
