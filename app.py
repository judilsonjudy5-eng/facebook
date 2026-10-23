from flask import Flask, request, jsonify
import os
import logging
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "")
PAGE_TOKEN = "EABD9vGanoGYBS9tbZBO5yFQF5IiF3rOWR0SzKMuxIuwoeb1nbN9Kz4O09DY25XbdUoKc77mzsb4s9JAmm3XSyuL1U6aLEZBiqMgvNBsKxJW6ltrieTs9keQp20YRyravNWNktkUTokC0PEIGPEZBRpifs6wP5xbNTuh3BvXx7ebRmBEZC19IhSED16AXZAIRvqgl9WwZDZD"
#META_IG_TOKEN = os.environ.get("META_IG_TOKEN", "")
META_IG_TOKEN = "IGAAYKuDjjophBZAGFCajY5Qy1fd1NMZAlVUbjYySEhoNkJtUTczR1N5bE01SmZAIc0Q4VmlDQlpPUlVUVVNFWjl2VjdsdnV5RW9RaVM3QVc2N2ljTUJST1Ezd01CdFhhUmFQUFFPYld3VGRubnVsakFnMEEyNWk0bHhTbzBnaDc3bwZDZD"
META_API_VERSION = "v25.0"


app = Flask(__name__)


@app.route("/")
def helo():
  return "Webhook On"

def _post(url: str, payload: dict, token: str) -> bool:
    try:
        r = requests.post(
            url,
            params={"access_token": token},
            json=payload,
            timeout=10,
        )
        if r.status_code != 200:
            logger.error(f"[meta] erro {r.status_code}: {r.text}")
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"[meta] erro {r.status_code}: {r.text}")
        return False


def enviar_facebook(recipient_id: str, texto: str) -> bool:
    if not PAGE_TOKEN:
        logger.info(f"[facebook] (sem token) → {recipient_id}: {texto[:80]}")
        return True
    url = f"https://graph.facebook.com/{META_API_VERSION}/me/messages"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": texto}, "messaging_type": "RESPONSE"}
    return _post(url, payload, PAGE_TOKEN)


def enviar_instagram(recipient_id: str, texto: str) -> bool:
    if not META_IG_TOKEN:
        logger.info(f"[instagram] (sem token) → {recipient_id}: {texto[:80]}")
        return True
    url = f"https://graph.instagram.com/{META_API_VERSION}/me/messages"
    payload = {"recipient": {"id": recipient_id}, "messaging_type": "RESPONSE", "message": {"text": texto}}
    return _post(url, payload, META_IG_TOKEN)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
  VERIFY_TOKEN = "jeturteste"

  # 1. TRATAMENTO PARA VALIDAÇÃO (GET)
  if request.method == "GET":
    mode = request.args.get("hub.mode")
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
      print("Webhook verificado com sucesso!")
      return challenge, 200
    else:
      print("Falha na verificação do webhook.")
      return "Token de verificação inválido", 403

  # 2. TRATAMENTO PARA RECEBER MENSAGENS (POST)
  if request.method == "POST":
    try:
      body = request.get_json()

      if body and "object" in body and body["object"] == "page":
        for entry in body.get("entry", []):
          if "messaging" in entry and len(entry["messaging"]) > 0:
            messaging_event = entry["messaging"][0]
            print(f"Evento de Mensagem Recebido: {messaging_event}")

            sender_id = messaging_event["sender"]["id"]
            print(f"ID do Remetente (PSID): {sender_id}")

            if "message" in messaging_event:
              msg = messaging_event["message"]
              if msg.get("is_echo"):
                continue
              message_text = msg.get("text")
              print(f"Texto da Mensagem: {message_text}")
              enviar_facebook(sender_id, "Tas bom")

      return "EVENT_RECEIVED", 200

    except Exception as e:
      print(f"Erro no webhook: {e}")
      return "Erro interno", 500


@app.route("/webhook/instagram", methods=["GET", "POST"])
def instagram_webhook():
    VERIFY_TOKEN = "instagramjetur2026"

    # 1. VALIDAÇÃO DO WEBHOOK (GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and verify_token == VERIFY_TOKEN:
            logger.info("Instagram webhook verificado com sucesso.")
            return challenge, 200
        logger.warning("Falha na verificação do Instagram webhook.")
        return "Token de verificação inválido", 403

    # 2. RECEBER MENSAGENS (POST)
    if request.method == "POST":
        try:
            body = request.get_json()
            logger.info(f"Instagram webhook payload: {body}")

            # A Meta envia object="instagram" para eventos da plataforma Instagram
            if body and body.get("object") in ("instagram", "page"):
                for entry in body.get("entry", []):

                    # ── Mensagens directas (DMs) ──────────────────────────────
                    for event in entry.get("messaging", []):
                        sender_igsid = event.get("sender", {}).get("id")

                        # Ignora eco das próprias mensagens enviadas pelo bot
                        msg = event.get("message", {})
                        if msg.get("is_echo"):
                            continue


                        texto = msg.get("text")
                        if not sender_igsid or not texto:
                            continue
                        texto = f"{texto} \ncanal de contato: *instagram*"
                        #if sender_igsid and texto:
                        logger.info(f"Instagram msg de {sender_igsid}: {texto}")
                        enviar_instagram(sender_igsid, "Tudo bem?")

            return "EVENT_RECEIVED", 200
        except Exception as e:
            logger.error(f"Erro ao processar POST do Instagram: {e}")
            return "Erro interno", 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
