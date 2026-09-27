import os, requests, threading
from flask import Flask, request

app = Flask(__name__)

def get_ai_reply(user_msg):
    try:
        groq_key = os.getenv("GROQ_API_KEY","").strip()
        print(f"GROQ KEY FOUND: {groq_key[:10]}...")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are NextLevel Furniture Chiniot assistant for owner M. Ahmed. Sell Pure Sheesham wood furniture. Single Bed 35000, Double Bed 70000-85000, 5-Seater Sofa 70000. Delivery all Pakistan. Reply in friendly Roman Urdu mix. Keep short."},
                {"role": "user", "content": user_msg}
            ]
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"GROQ STATUS: {r.status_code} - {r.text[:300]}")
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return f"Groq API Error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        print(f"GROQ EXCEPTION: {e}")
        return f"Error: {e}"

@app.route("/")
def home(): return "Bot Live with Groq AI", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == os.getenv("VERIFY_TOKEN","").strip():
        return request.args.get("hub.challenge")
    return "fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print(f"WEBHOOK DATA: {data}")
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" in value:
            phone_id = value["metadata"]["phone_number_id"]
            from_num = value["messages"][0]["from"]
            user_text = value["messages"][0]["text"]["body"]
            print(f"USER SAID: {user_text}")
            def do_reply():
                ai_text = get_ai_reply(user_text)
                print(f"AI REPLY: {ai_text}")
                url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
                headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN','').strip()}", "Content-Type": "application/json"}
                body = {"messaging_product":"whatsapp","to":from_num,"text":{"body":ai_text}}
                resp = requests.post(url, headers=headers, json=body, timeout=10)
                print(f"WA SEND STATUS: {resp.text}")
            threading.Thread(target=do_reply).start()
    except Exception as e: print(f"WEBHOOK ERROR: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
