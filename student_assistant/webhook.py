from fastapi import FastAPI, Request
from pydantic import BaseModel
import router
import config
import requests

app = FastAPI()


# ---------- LOCAL TEST MODE ----------

class LocalMessage(BaseModel):
    phone: str
    text: str


@app.post("/test-message")
async def test_message(msg: LocalMessage):
    response_text = router.handle_message(msg.phone, msg.text)
    return {
        "phone": msg.phone,
        "input": msg.text,
        "response": response_text
    }


# ---------- WHATSAPP MODE ----------

@app.get("/webhook")
async def verify_webhook(mode: str = None, token: str = None, challenge: str = None):
    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        return int(challenge)
    return {"error": "verification failed"}


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]

        response_text = router.handle_message(phone, text)
        send_message(phone, response_text)

    except Exception as e:
        print("Error:", e)

    return {"status": "ok"}


def send_message(to, text):
    url = f"https://graph.facebook.com/v17.0/{config.PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=payload)