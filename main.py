import os, requests, threading
from flask import Flask, request

app = Flask(__name__)

# Groq AI Function
def get_ai_reply(user_msg):
    try:
        groq_key = os.getenv("GROQ_API_KEY","").strip()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are NextLevel Furniture assistant for M. Ahmed in Chiniot. We sell only High Quality Sheesham wood furniture. Beds, Sofa, Dining, Almari. Prices: Single Bed 35k, Double Bed 65k-85k, Sofa 5 seater 70k. Delivery all Pakistan. Showroom Chiniot. Owner M. Ahmed. Talk in mix Urdu/Hinglish friendly. Always give price and ask to visit showroom or order."},
                {"role": "user", "content": user_msg}
            ]
        }
        r = requests.post(url, headers=headers, json=data, timeout=15)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq Error: {e}")
        return "Ji M. Ahmed bolen! Sheesham furniture me kia chahiye aap ko? Bed, Sofa ya Dining?"

@app.route("/")
def home(): return "NextLevel Bot Live with AI", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == os.getenv("VERIFY_TOKEN","").strip():
        return request.args.get("hub.challenge")
    return "fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" in value:
            phone_id = value["metadata"]["phone_number_id"]
            from_num = value["messages"][0]["from"]
            user_text = value["messages"][0]["text"]["body"]

            def reply_thread():
                ai_text = get_ai_reply(user_text)
                url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
                headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN','').strip()}", "Content-Type": "application/json"}
                payload = {"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_text}}
                requests.post(url, headers=headers, json=payload, timeout=10)

            threading.Thread(target=reply_thread).start()

    except Exception as e:
        print(e)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
