import os, requests, threading
from flask import Flask, request
app = Flask(__name__)

VERIFY = os.getenv("VERIFY_TOKEN","").strip()
TOKEN = os.getenv("ACCESS_TOKEN","").strip()
GROQ = os.getenv("GROQ_API_KEY","").strip()

def do_reply(pid, to, txt):
    try:
        # Groq call
        g = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.1-8b-instant","messages":[{"role":"system","content":"You are furniture shop assistant in Quetta. Reply in short Roman Urdu."},{"role":"user","content":txt}],"max_tokens":150},
            timeout=12).json()
        reply = g["choices"][0]["message"]["content"] if "choices" in g else "Salam! Kis furniture ki info chahiye aap ko?"
        print(f"Groq: {g}")
        requests.post(f"https://graph.facebook.com/v20.0/{pid}/messages",
            headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"},
            json={"messaging_product":"whatsapp","to":to,"text":{"body":reply}}, timeout=10)
    except Exception as e:
        print(f"ERR: {e}")

@app.route("/webhook", methods=["GET"])
def v():
    if request.args.get("hub.verify_token")==VERIFY:
        return request.args.get("hub.challenge")
    return "no",403

@app.route("/webhook", methods=["POST"])
def w():
    try:
        d=request.get_json(); v=d["entry"][0]["changes"][0]["value"]
        if "messages" in v:
            threading.Thread(target=do_reply, args=(v["metadata"]["phone_number_id"], v["messages"][0]["from"], v["messages"][0].get("text",{}).get("body","Hi"))).start()
    except: pass
    return "OK",200 # <-- Ye sab se zaroori hai, foran OK

@app.route("/")
def h(): return "OK",200
