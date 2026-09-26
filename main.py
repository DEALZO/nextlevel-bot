import os, requests
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

@app.route("/", methods=["GET"])
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
        if "messages" not in entry: return "OK", 200

        msg = entry["messages"][0]
        from_num = msg["from"]
        phone_id = entry["metadata"]["phone_number_id"]

        # Text ya Image ka caption dono handle
        if msg.get("type") == "text":
            user_text = msg["text"]["body"]
        elif msg.get("type") == "image":
            user_text = msg.get("image", {}).get("caption", "Yeh wooden product ki image hai")
        else:
            user_text = "Customer ne kuch bheja hai"

        print(f"IN: {user_text} KEY:{len(GROQ_API_KEY)}")

        ai_reply = ""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are NextLevel Agency Quetta. You sell wooden furniture websites. Customer sells wooden products (images given). Reply in friendly Roman Urdu, short. Never say 'Samajh gaya!... Kya bechte ho'. Give real price: Website 25k, Marketing 15k/month. If customer sends image, praise the design."},
                    {"role": "user", "content": user_text}
                ]
            }
            r = requests.post(url, json=payload, headers=headers, timeout=25)
            j = r.json()
            print(f"GROQ_RES: {j}")
            if "choices" not in j:
                raise Exception(str(j))
            ai_reply = j["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"GROQ_ERR: {e}")
            # Ab fallback bhi smart hai, same line nahi
            ai_reply = f"Wooden products ka kaam zabardast hai! '{user_text}' ke liye Shopify website 25k me bana dete hain jisme COD + WhatsApp order ayega. Aap Quetta se ho ya bahar bhejte ho?"

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        wa_headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        wa_payload = {"messaging_product": "whatsapp", "to": from_num, "text": {"body": ai_reply}}
        requests.post(wa_url, json=wa_payload, headers=wa_headers)

    except Exception as e:
        print(f"MAIN_ERR: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
