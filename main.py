import os, requests
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

@app.route("/")
def home(): return "Bot LIVE", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg = entry["messages"][0]
            from_num = msg["from"]
            user_text = msg["text"]["body"]
            phone_number_id = entry["metadata"]["phone_number_id"]

            print(f"IN: {user_text} FROM {from_num} KEY_LEN {len(GROQ_API_KEY)}")

            # GROQ CALL
            ai_reply = ""
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.3-70b-versatile", # Sab se stable
                    "messages": [
                        {"role": "system", "content": "You are NextLevel Agency, Quetta. Helpful ecommerce assistant. Reply short, in Roman Urdu. Don't repeat same line, be smart."},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7
                }
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                j = r.json()
                print(f"GROQ RAW: {j}")
                if "choices" not in j:
                    raise Exception(f"Groq error: {j}")
                ai_reply = j["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"GROQ FAIL: {e}")
                # Agar fail bhi ho to alag alag reply, same nahi
                low = user_text.lower()
                if "hello" in low:
                    ai_reply = "Wa Alaikum Salam! Kya haal hai? Ecommerce store ka kya plan hai?"
                elif "info" in low:
                    ai_reply = "Bilkul! Hum Website (25k), Marketing (15k/month), WhatsApp Bot (10k) dete hain. Aap ko kis me info chahiye?"
                else:
                    ai_reply = f"Samajh gaya! {user_text} ke liye best ye hai ke hum pehle product dekh lete hain. Kya bechte ho aap?"

            wa_url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
            wa_headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
            wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply}}
            res = requests.post(wa_url, json=wa_payload, headers=wa_headers)
            print(f"WA OUT: {res.status_code}")
    except Exception as e:
        print(f"MAIN ERR: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
