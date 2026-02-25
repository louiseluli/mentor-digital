#!/usr/bin/env python3
"""
register_whatsapp_webhook.py — Registra o webhook do Mentor Digital na Meta

Uso (após deploy no Railway):
    WEBHOOK_URL=https://seu-app.up.railway.app \
    WHATSAPP_APP_ID=123456789 \
    WHATSAPP_ACCESS_TOKEN=EAAxxxxx \
    WHATSAPP_VERIFY_TOKEN=seu-token \
    python apps/bot/scripts/register_whatsapp_webhook.py

O script:
  1. Registra o endpoint /webhook/whatsapp como callback da Meta
  2. Inscreve o app para receber o campo "messages"
  3. Imprime instruções para confirmar no Developer Portal se necessário

Variáveis de ambiente necessárias:
  WEBHOOK_URL              URL pública do bot (ex: https://...railway.app)
  WHATSAPP_APP_ID          ID do app Meta (App Settings → Basic)
  WHATSAPP_ACCESS_TOKEN    System User Token (Meta Business Suite → System Users)
  WHATSAPP_VERIFY_TOKEN    Token de verificação (mesmo do .env do Railway)
"""

import os
import sys

try:
    import httpx
except ImportError:
    print("Erro: httpx não instalado. Execute: pip install httpx")
    sys.exit(1)

GRAPH_API_URL = "https://graph.facebook.com/v22.0"


def _check_env() -> dict:
    required = {
        "WEBHOOK_URL": os.getenv("WEBHOOK_URL", ""),
        "WHATSAPP_APP_ID": os.getenv("WHATSAPP_APP_ID", ""),
        "WHATSAPP_ACCESS_TOKEN": os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
        "WHATSAPP_VERIFY_TOKEN": os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌ Variáveis de ambiente não definidas: {', '.join(missing)}")
        print("\nDefina-as antes de executar o script:")
        for k in missing:
            print(f"  export {k}=...")
        sys.exit(1)
    return required


def register_webhook(env: dict) -> bool:
    """Registra o callback URL via Graph API App Subscriptions."""
    callback_url = env["WEBHOOK_URL"].rstrip("/") + "/webhook/whatsapp"
    url = f"{GRAPH_API_URL}/{env['WHATSAPP_APP_ID']}/subscriptions"

    print(f"\n→ Registrando webhook:")
    print(f"  App ID  : {env['WHATSAPP_APP_ID']}")
    print(f"  Callback: {callback_url}")

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            url,
            data={
                "object": "whatsapp_business_account",
                "callback_url": callback_url,
                "verify_token": env["WHATSAPP_VERIFY_TOKEN"],
                "fields": "messages",
                "access_token": env["WHATSAPP_ACCESS_TOKEN"],
            },
        )

    if resp.is_success and resp.json().get("success"):
        print(f"✅ Webhook registrado: {resp.json()}")
        return True
    else:
        print(f"❌ Falha ao registrar webhook ({resp.status_code}): {resp.text}")
        return False


def verify_webhook_reachable(callback_url: str, verify_token: str) -> bool:
    """Simula a verificação challenge-response da Meta no endpoint local/remoto."""
    challenge = "mentor_digital_e2e_test"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": verify_token,
        "hub.challenge": challenge,
    }
    print(f"\n→ Verificando endpoint: {callback_url}")
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(callback_url, params=params)
        if resp.status_code == 200 and challenge in resp.text:
            print("✅ Endpoint responde corretamente ao challenge da Meta.")
            return True
        else:
            print(
                f"❌ Endpoint não respondeu como esperado "
                f"({resp.status_code}): {resp.text[:200]}"
            )
            return False
    except httpx.ConnectError:
        print("❌ Endpoint inacessível — verifique se o Railway está online.")
        return False


def print_portal_instructions(env: dict) -> None:
    callback_url = env["WEBHOOK_URL"].rstrip("/") + "/webhook/whatsapp"
    print("\n── Instruções alternativas via Developer Portal ───────────────────────")
    print("1. Acesse: https://developers.facebook.com/apps/")
    print(f"2. Selecione o app ID: {env['WHATSAPP_APP_ID']}")
    print("3. WhatsApp → Configuração → Webhooks → Editar")
    print(f"4. URL de callback : {callback_url}")
    print(f"5. Token de verificação: {env['WHATSAPP_VERIFY_TOKEN']}")
    print("6. Campos: marque 'messages'")
    print("7. Clique em 'Verificar e salvar'\n")


def main() -> None:
    env = _check_env()
    callback_url = env["WEBHOOK_URL"].rstrip("/") + "/webhook/whatsapp"

    # 1. Testa se o endpoint está acessível e respondendo ao challenge
    reachable = verify_webhook_reachable(callback_url, env["WHATSAPP_VERIFY_TOKEN"])
    if not reachable:
        print("\n⚠️  Corrija o endpoint antes de registrar na Meta.")
        print_portal_instructions(env)
        sys.exit(1)

    # 2. Registra via Graph API
    success = register_webhook(env)
    if not success:
        print("\n⚠️  Use o Developer Portal como alternativa:")
        print_portal_instructions(env)
        sys.exit(1)

    print("\n✅ Tudo configurado! O Mentor Digital está pronto para receber mensagens WhatsApp.")
    print(f"   Endpoint ativo: {callback_url}")


if __name__ == "__main__":
    main()
