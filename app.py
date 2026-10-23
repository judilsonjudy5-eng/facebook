import os
import logging

import requests
from dotenv import load_dotenv
from flask import Flask, request
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# --- Configuração (tudo via variáveis de ambiente) ---------------------------
#PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "")
#META_IG_TOKEN = os.environ.get("META_IG_TOKEN", "")
META_API_VERSION = os.environ.get("META_API_VERSION", "v25.0")
FB_VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "testejetur")
IG_VERIFY_TOKEN = os.environ.get("IG_VERIFY_TOKEN", "instagramjetur2026")
#PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "")
PAGE_TOKEN = "EABD9vGanoGYBS9tbZBO5yFQF5IiF3rOWR0SzKMuxIuwoeb1nbN9Kz4O09DY25XbdUoKc77mzsb4s9JAmm3XSyuL1U6aLEZBiqMgvNBsKxJW6ltrieTs9keQp20YRyravNWNktkUTokC0PEIGPEZBRpifs6wP5xbNTuh3BvXx7ebRmBEZC19IhSED16AXZAIRvqgl9WwZDZD"
#META_IG_TOKEN = os.environ.get("META_IG_TOKEN", "")
META_IG_TOKEN = "IGAAYKuDjjophBZAGFCajY5Qy1fd1NMZAlVUbjYySEhoNkJtUTczR1N5bE01SmZAIc0Q4VmlDQlpPUlVUVVNFWjl2VjdsdnV5RW9RaVM3QVc2N2ljTUJST1Ezd01CdFhhUmFQUFFPYld3VGRubnVsakFnMEEyNWk0bHhTbzBnaDc3bwZDZD"
META_API_VERSION = "v2

APP_NAME = "assistente_online"

app = Flask(__name__)


@app.route("/")
def home():
    return "Webhook On"


# --- Envio de mensagens --------------------------------------------------------
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
        logger.error(f"[meta] falha de rede: {e}")
        return False


def enviar_facebook(recipient_id: str, texto: str) -> bool:
    if not PAGE_TOKEN:
        logger.info(f"[facebook] (sem token) → {recipient_id}: {texto[:80]}")
        return True
    url = f"https://graph.facebook.com/{META_API_VERSION}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": texto},
        "messaging_type": "RESPONSE",
    }
    return _post(url, payload, PAGE_TOKEN)


def enviar_instagram(recipient_id: str, texto: str) -> bool:
    if not META_IG_TOKEN:
        logger.info(f"[instagram] (sem token) → {recipient_id}: {texto[:80]}")
        return True
    url = f"https://graph.instagram.com/{META_API_VERSION}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {"text": texto},
    }
    return _post(url, payload, META_IG_TOKEN)


# --- Agente --------------------------------------------------------------------
agente = Agent(
    name="Assistente_online",
    model="gemini-3.8-flash",  # confirma que este modelo existe na tua conta
    instruction="""
        Use a ferramenta get_dados para pegar os dados do cliente e inserir numa tabela.
        Primeiro use a função get_cliente para pegar os dados dos clientes, depois use a ferramenta get_negocio para inserir dados do negócio para esse cliente e não deves nunca perguntar o id do cliente para o usuário.
        Use a ferramenta get_cliente para pegar o id do cliente.
        Use a ferramenta get_contact para pegar os dados de apenas um cliente
        Primeiro use a função get_cliente para pegar os dados dos clientes, depois use a ferramenta get_nota uma nota para esse cliente e não deves nunca perguntar o id do cliente para o usuário.
        Use a ferramenta get_listarnegocios para listar todos os negócios no crm
        Use a ferramenta get_listarnotas para listar todos as notas no crm
        Primeiro use a função get_contact para pegar o id do cliente, depois use a ferramenta del_cliente para deletar o cliente do crm e não deves nunca perguntar o id do cliente para o usuário
        Primeiro use a função get_listarnegocios para pegar o id do negócio, depois use a ferramenta del_negocio para deletar o negócio do crm e não deves nunca perguntar o id do cliente para o usuário
        Primeiro use a função get_cliente para pegar os dados do cliente, depois use a ferramenta patch_dados para editar os dados do cliente no crm
        Primeiro use a função get_listarnegocios para pegar os dados do negócio no crm, depois use a ferramenta patch_negocios para editar os dados desse negócio
        Use a ferramenta get_resumo para fazer um funil ou resumo de totais e valor por etapa
    """,
    # TODO: adicionar aqui as funções Python (get_cliente, get_negocio, ...)
    tools=[],
)

session_service = InMemorySessionService()
runner = Runner(agent=agente, app_name=APP_NAME, session_service=session_service)


async def garantir_sessao(user_id: str, session_id: str):
    sessao = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if sessao is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )


async def perguntar_ao_agente(user_id: str, pergunta: str):
    await garantir_sessao(user_id, user_id)
    mensagem = types.Content(role="user", parts=[types.Part(text=pergunta)])

    resposta = None
    async for ev in runner.run_async(
        user_id=user_id, session_id=user_id, new_message=mensagem
    ):
        if ev.is_final_response() and ev.content and ev.content.parts:
            resposta = ev.content.parts[0].text
    return resposta


# --- Webhook do Facebook Messenger ---------------------------------------------
@app.route("/facebook", methods=["GET", "POST"])
async def facebook_webhook():
    # 1. Validação (GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and verify_token == FB_VERIFY_TOKEN:
            logger.info("Facebook webhook verificado com sucesso.")
            return challenge, 200
        logger.warning("Falha na verificação do Facebook webhook.")
        return "Token de verificação inválido", 403

    # 2. Receber mensagens (POST)
    body = request.get_json(silent=True)
    if not body or body.get("object") != "page":
        return "Not Found", 404

    try:
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                msg = event.get("message", {})

                if not sender_id or msg.get("is_echo") or not msg.get("text"):
                    continue

                logger.info(f"Facebook msg de {sender_id}: {msg['text']}")
                resposta = await perguntar_ao_agente(sender_id, msg["text"])

                if resposta:
                    enviar_facebook(sender_id, resposta)
    except Exception as e:
        logger.error(f"Erro no webhook do Facebook: {e}")

    # Responde sempre 200 para a Meta não reenviar o mesmo evento
    return "EVENT_RECEIVED", 200


# --- Webhook do Instagram ------------------------------------------------------
@app.route("/webhook/instagram", methods=["GET", "POST"])
def instagram_webhook():
    # 1. Validação (GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and verify_token == IG_VERIFY_TOKEN:
            logger.info("Instagram webhook verificado com sucesso.")
            return challenge, 200
        logger.warning("Falha na verificação do Instagram webhook.")
        return "Token de verificação inválido", 403

    # 2. Receber mensagens (POST)
    body = request.get_json(silent=True)
    logger.info(f"Instagram webhook payload: {body}")

    if not body or body.get("object") not in ("instagram", "page"):
        return "Not Found", 404

    try:
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                sender_igsid = event.get("sender", {}).get("id")
                msg = event.get("message", {})

                if not sender_igsid or msg.get("is_echo") or not msg.get("text"):
                    continue

                logger.info(f"Instagram msg de {sender_igsid}: {msg['text']}")
                enviar_instagram(sender_igsid, "Tudo bem?")
    except Exception as e:
        logger.error(f"Erro ao processar POST do Instagram: {e}")

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
