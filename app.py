from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.route("/")
def helo():
  return "Webhook On"

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
                            mid = msg.get("mid", "")
                            if mid and not _adquirir_lock(f"webhook:fb:{mid}", 120):
                                logger.info(f"Webhook FB duplicado ignorado: {mid}")
                                continue
                            message_text = msg.get("text")
                            print(f"Texto da Mensagem: {message_text}")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
