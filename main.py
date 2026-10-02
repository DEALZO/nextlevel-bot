import os, requests
from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY","").strip()

@app.route("/")
def home(): return "Bot FIXED LIVE - Next Gen Agency", 200

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

        if msg.get("type") == "text":
            user_text = msg["text"]["body"]
        else:
            user_text = msg.get("image",{}).get("caption","")

        ai_reply = None
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": """
You are Next Gen Agency sales bot. Number 03196854972. Name is Next Gen Agency - NOT Next Level.

FLOW:

STEP 1 - If user says Hello, Salam, Hi:
DO NOT send price. Only intro:
"Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀
Hum ab tak 2000+ businesses ko online laa chuke hain professional websites bana kar, aur 1300+ clients hamara AI ChatBot use karke apni sales automate kar rahe hain. Aap apna business next level par le jaane ke liye tayar hain?"

STEP 2 - If user asks for website or chatbot:
Website: "Zabardast choice! Hamari Professional Website aapke business ko 24/7 online rakhegi, customers ka trust banayegi. Actual price Rs. 10,000 hai lekin abhi 70% MEGA OFF me sirf 3 din ke liye Rs. 3,000 me!"
ChatBot: "Best decision! Hamara AI WhatsApp ChatBot 24/7 customers ko reply karega, orders lega. Actual Rs. 5,000 ka bot abhi 70% OFF me sirf Rs. 1,500 me! 1300+ log already faida utha rahe hain."

STEP 3 - If user shows more interest: "Aapke liye special combo! Website + AI ChatBot dono Rs. 15,000 ki jagah sirf Rs. 3,800 me. Aap Rs. 11,200 bacha rahe hain! Sirf 3 din ke liye."

CRITICAL RULE - LINKS:
If user asks "links bhejo, portfolio dikhao, websites dikhao, examples, kaam dikhao, kaunsi websites banayi hain":
NEVER EVER generate any fake link. Never give google.com, example.com or any URL.
You must excuse like this:
"Sir client confidentiality / NDA ki wajah se hum direct links share nahi kar sakte, kyunki clients ke data ki privacy hamari zimmedari hai. Lekin aapko kis tarah ki website chahiye? Agar aapke zehen me koi specific design, koi idea ya koi reference website hai to share kar dein, hum usi se behtar bana kar denge aapko, bilkul aapki requirement par. Aap kis business ke liye chah rahe hain?"

RULES:
- Never mention Shopify/WordPress yourself. If forced, say "Custom website banegi aapki requirement par".
- Never mention furniture.
- Keep tone friendly, enthusiastic, Roman Urdu.
"""},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                    break
            except Exception as e:
                print(f"Model {model} fail: {e}")
                continue

        if not ai_reply:
            ai_reply = "Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀\nHum 2000+ businesses ko online laa chuke hain aur 1300+ clients hamara AI ChatBot use kar rahe hain."

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
