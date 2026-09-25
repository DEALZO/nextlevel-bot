def get_ai_reply(user_text):
    if not GEMINI_API_KEY:
        return "Salam! NextLevel me khush amdeed."

    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
    ]

    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": f"You are NextLevel Agency sales assistant. User wants: {user_text}. Reply helpfully in Roman Urdu/English mix, ask about their business."}]}],
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ],
                "generationConfig": {"temperature": 0.7}
            }
            r = requests.post(url, json=payload, timeout=20)
            j = r.json()

            if "candidates" in j and j["candidates"]:
                return j["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Model {model_name} blocked: {j}")
                continue # next model try karo

        except Exception as e:
            print(f"Model {model_name} Error: {e}")
            continue

    # Agar dono model fail ho jayen to ye intelligent reply
    if "buy" in user_text.lower() or "service" in user_text.lower() or "price" in user_text.lower():
        return "Zabardast! Aap kaunsa package lena chahte hain? \n\n1. Website Development\n2. Social Media Marketing\n3. WhatsApp Automation Bot (jaisa ye hai)\n\nApna business name bataiye, main details bhej deta hun."

    return "Shukriya message ka! Aap thora detail me bataiye, aap ko kis service me help chahiye taake main price aur demo bhej sakun."
