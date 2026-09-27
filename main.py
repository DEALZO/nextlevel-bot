# webhook wala part same, sirf ye function change karo
def reply_later(phone_id, to, user_text):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY.strip()}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile", # zyada stable model
            "messages": [
                {"role":"system","content":"You are NextLevel Saas Quetta furniture salesman. Reply in short helpful Roman Urdu. Client: M Ahmed."},
                {"role":"user","content": user_text}
            ],
            "max_tokens": 200
        }
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        j = r.json()
        print(f"GROQ FULL RESPONSE: {j}") # ye Railway logs me nazar ayega
        ai_reply = j["choices"][0]["message"]["content"] if "choices" in j else "Salam M. Ahmed! Aap ko kis cheez ki info chahiye? Bed, Chair?"
        # send whatsapp...
        wa_url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        wa_headers = {"Authorization": f"Bearer {ACCESS_TOKEN.strip()}", "Content-Type": "application/json"}
        wa_data = {"messaging_product":"whatsapp","to":to,"text":{"body":ai_reply}}
        requests.post(wa_url, headers=wa_headers, json=wa_data, timeout=10)
    except Exception as e:
        print(f"Error: {e}")
