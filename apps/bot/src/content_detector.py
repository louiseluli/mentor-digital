"""
content_detector.py — Detecção de tipo de conteúdo (Micro-Batch 2.4)

Identifica se o input é texto livre, link, imagem, vídeo, áudio ou documento.
Também fornece as mensagens de reconhecimento por tipo para o fluxo do bot.
"""

import re

# Regex para detectar URLs (http/https ou www.)
_URL_RE = re.compile(
    r'https?://[^\s]+|www\.[^\s]+',
    re.IGNORECASE,
)

# Mensagem de reconhecimento exibida antes da pergunta de motivação
CONTENT_ACKNOWLEDGMENTS: dict[str, str] = {
    "text":     "Obrigada por compartilhar! 🙏",
    "link":     "Obrigada pelo link! 🔗",
    "image":    "Obrigada pela imagem! 🖼️",
    "video":    "Obrigada pelo vídeo! 🎥",
    "audio":    "Obrigada pelo áudio! 🎙️",
    "document": "Obrigada pelo documento! 📄",
}


def detect_text_type(text: str) -> str:
    """Retorna 'link' se o texto contiver uma URL, caso contrário 'text'."""
    return "link" if _URL_RE.search(text) else "text"


def get_acknowledgment(content_type: str) -> str:
    """Retorna a mensagem de reconhecimento para o tipo de conteúdo."""
    return CONTENT_ACKNOWLEDGMENTS.get(content_type, CONTENT_ACKNOWLEDGMENTS["text"])
