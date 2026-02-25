#!/usr/bin/env python3
"""
register_telegram_webhook.py — Registra o webhook do Mentor Digital no Telegram

Uso (após deploy no Railway):
    TELEGRAM_BOT_TOKEN=123456:ABCdef... \
    WEBHOOK_URL=https://seu-app.up.railway.app \
    WEBHOOK_SECRET=seu-token-secreto \
    python apps/bot/scripts/register_telegram_webhook.py

O script:
  1. Valida token chamando getMe
  2. Registra /webhook/telegram como callback via setWebhook
  3. Confirma o registro chamando getWebhookInfo
  4. Imprime instruções de curl manual como fallback

Variáveis de ambiente necessárias:
  TELEGRAM_BOT_TOKEN   Token do BotFather (ex: 123456789:ABCdef...)
  WEBHOOK_URL          URL pública do bot (ex: https://xxx.up.railway.app)
  WEBHOOK_SECRET       Token secreto para X-Telegram-Bot-Api-Secret-Token
"""

import os
import sys

try:
    import httpx
except ImportError:
    print("Erro: httpx não instalado. Execute: pip install httpx")
    sys.exit(1)

TELEGRAM_API = "https://api.telegram.org"


def _check_env() -> dict:
    required = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "WEBHOOK_URL": os.getenv("WEBHOOK_URL", ""),
        "WEBHOOK_SECRET": os.getenv("WEBHOOK_SECRET", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌ Variáveis de ambiente não definidas: {', '.join(missing)}")
        print("\nDefina-as antes de executar o script:")
        for k in missing:
            print(f"  export {k}=...")
        sys.exit(1)
    return required


def _bot_url(token: str, method: str) -> str:
    return f"{TELEGRAM_API}/bot{token}/{method}"


def validate_token(token: str) -> dict:
    """Chama getMe para confirmar que o token é válido."""
    print("\n→ Validando token do bot...")
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(_bot_url(token, "getMe"))

    if not resp.is_success or not resp.json().get("ok"):
        print(f"❌ Token inválido ({resp.status_code}): {resp.text[:200]}")
        sys.exit(1)

    bot_info = resp.json()["result"]
    print(f"✅ Token válido — bot: @{bot_info.get('username')} (id={bot_info.get('id')})")
    return bot_info


def set_webhook(token: str, webhook_url: str, secret: str) -> bool:
    """Registra o endpoint /webhook/telegram via setWebhook."""
    callback_url = webhook_url.rstrip("/") + "/webhook/telegram"
    print(f"\n→ Registrando webhook:")
    print(f"  Callback  : {callback_url}")
    print(f"  Secret    : {'*' * min(len(secret), 8)}...")

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            _bot_url(token, "setWebhook"),
            json={
                "url": callback_url,
                "secret_token": secret,
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True,
            },
        )

    data = resp.json()
    if resp.is_success and data.get("ok"):
        print(f"✅ Webhook registrado: {data.get('description', 'ok')}")
        return True
    else:
        print(f"❌ Falha ao registrar webhook ({resp.status_code}): {resp.text[:300]}")
        return False


def get_webhook_info(token: str) -> None:
    """Confirma o registro e imprime detalhes do webhook ativo."""
    print("\n→ Confirmando registro...")
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(_bot_url(token, "getWebhookInfo"))

    if not resp.is_success:
        print(f"⚠️  Não foi possível confirmar ({resp.status_code})")
        return

    info = resp.json().get("result", {})
    print(f"  URL             : {info.get('url', '—')}")
    print(f"  Pending updates : {info.get('pending_update_count', 0)}")
    print(f"  Last error      : {info.get('last_error_message', '—')}")
    if info.get("url"):
        print("✅ Webhook ativo e confirmado.")
    else:
        print("⚠️  Webhook URL vazia — algo pode ter falhado.")


def print_curl_fallback(token: str, webhook_url: str, secret: str) -> None:
    callback_url = webhook_url.rstrip("/") + "/webhook/telegram"
    print("\n── Fallback via curl ───────────────────────────────────────────────────")
    print("Execute manualmente se o script falhar:")
    print(f"""
curl -X POST "https://api.telegram.org/bot{token}/setWebhook" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "url": "{callback_url}",
    "secret_token": "{secret}",
    "allowed_updates": ["message", "callback_query"],
    "drop_pending_updates": true
  }}'
""")


def main() -> None:
    env = _check_env()
    token = env["TELEGRAM_BOT_TOKEN"]
    webhook_url = env["WEBHOOK_URL"]
    secret = env["WEBHOOK_SECRET"]

    # 1. Valida token
    validate_token(token)

    # 2. Registra webhook
    success = set_webhook(token, webhook_url, secret)
    if not success:
        print_curl_fallback(token, webhook_url, secret)
        sys.exit(1)

    # 3. Confirma registro
    get_webhook_info(token)

    print("\n✅ Mentor Digital Telegram configurado!")
    print(f"   Endpoint ativo: {webhook_url.rstrip('/')}/webhook/telegram")
    print("\nPróximo passo: envie /start ao bot para testar.")


if __name__ == "__main__":
    main()
