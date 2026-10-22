from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def helo():
  return "Webhook On"

token_fb = "EABD9vGanoGYBS046QAVTYPgu6XXExEboAgIXfreFqrZCLbyqZAlGEbvZCLZCgasklrlstyLGxySIkaWdASr5omFDvzdRMXFiRjB4xmucp9vZAwitRTjaCiskNjfyZBeKSqUzDEchX9KlZAQBgZB9fvZCPcoW8KCrDZCKJROXSpNwOMUzvBrSJG0j1Qo9jd7wWRX0ts3sPblwZDZD"
META_API_VERSION = "v25.0"

def enviar_facebook(recipient_id: str, texto: str, token_fb: str, META_API_VERSION: str) -> bool:
    if not META_PAGE_TOKEN:
        logger.info(f"[facebook] (sem token) → {recipient_id}: {texto[:80]}")
        return True
    
    # Montagem de URL ultra-segura com barras explícitas
    url = f"https://graph.facebook.com/{META_API_VERSION}/me/messages"
    return _post(url, {"recipient": {"id": recipient_id}, "message": {"text": texto}, "messaging_type": "RESPONSE"}, token_fb)


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
              enviar_facebook(send_id, "Tas bom", token_fb, META_API_VERSION)

      return "EVENT_RECEIVED", 200

    except Exception as e:
      print(f"Erro no webhook: {e}")
      return "Erro interno", 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
