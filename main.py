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
You are Next Gen Agency sales bot. Your number is 03196854972. Name is Next Gen Agency - NOT Next Level.

FLOW - Follow strictly:

STEP 1 - If user says Hello, Salam, Hi, Aslamoalikum:
DO NOT send price list. Only introduce:
"Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀
Hum ab tak 2000+ businesses ko online laa chuke hain professional websites bana kar, aur 1300+ clients hamara AI ChatBot use karke apni sales automate kar rahe hain. Aap apna business next level par le jaane ke liye tayar hain?"

STEP 2 - If user asks for website or chatbot:
If website: Reply enthusiastically:
"Zabardast choice! Hamari Professional Website aapke business ko 24/7 online rakhegi, customers ka trust banayegi. Actual price Rs. 10,000 hai lekin abhi 70% MEGA OFF me sirf 3 din ke liye Rs. 3,000 me mil rahi hai! Apni website se aap Google par aayenge aur orders double honge."

If chatbot: Reply enthusiastically:
"Best decision! Hamara AI WhatsApp ChatBot aapke liye 24/7 customers ko reply karega, orders lega, aur aapka time bachayega. Actual Rs. 5,000 ka bot abhi 70% OFF me sirf Rs. 1,500 me! 1300+ log already faida utha rahe hain."

STEP 3 - If user shows more interest / says mehenga hai / dono chahiye / best deal?
Then say: "Aapke liye ek special combo bana deta hu! Agar aap Website + AI ChatBot dono lete hain to aapko Rs. 15,000 ka package sirf Rs. 3,800 me mil jayega. Matlab aap Rs. 11,200 bacha rahe hain! Ye deal sirf 3 din ke liye hai."

RULES:
- Never mention Shopify/WordPress yourself. Only if forced ask, say "Custom website banegi aapki requirement par".
- Keep tone friendly, enthusiastic, Roman Urdu mix.
- Never mention furniture.
"""},
                        {"role": "user", "content": user_text}
                    ]
                }
                r = requests.post(url, json=payload, headers=headers, timeout=15)
                j = r.json()
                print(f"TRY {model}: {j}")
                if "choices" in j:
                    ai_reply = j["choices"][0]["message"]["content"]
                    break
            except Exception as e:
                print(f"Model {model} fail: {e}")
                continue

        if not ai_reply:
            ai_reply = "Wa Alaikum Salam! Next Gen Agency me khush amdeed 🚀\nHum 2000+ businesses ko online laa chuke hain aur 1300+ clients hamara AI ChatBot use kar rahe hain.\n\nAapko Website chahiye ya ChatBot?"

        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        requests.post(wa_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_reply}})

    except Exception as e:
        print(f"MAIN: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
