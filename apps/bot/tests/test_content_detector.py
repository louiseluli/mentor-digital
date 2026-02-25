"""
test_content_detector.py — Testes para detecção de tipo de conteúdo (Micro-Batch 2.4)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.content_detector import (
    detect_text_type,
    get_acknowledgment,
    CONTENT_ACKNOWLEDGMENTS,
)


# ── detect_text_type ──────────────────────────────────────────────────────────

def test_plain_text_detected_as_text():
    assert detect_text_type("Olha essa notícia sobre saúde!") == "text"


def test_http_url_detected_as_link():
    assert detect_text_type("http://exemplo.com/noticia") == "link"


def test_https_url_detected_as_link():
    assert detect_text_type("https://g1.globo.com/saude/noticia") == "link"


def test_www_url_detected_as_link():
    assert detect_text_type("www.exemplo.com.br/artigo") == "link"


def test_url_embedded_in_text_detected_as_link():
    assert detect_text_type("Vi essa notícia: https://g1.globo.com e quero compartilhar") == "link"


def test_empty_text_is_text_type():
    assert detect_text_type("") == "text"


def test_text_without_url_is_text():
    assert detect_text_type("Recebi essa mensagem no grupo da família") == "text"


def test_url_detection_is_case_insensitive():
    assert detect_text_type("HTTP://EXEMPLO.COM") == "link"


# ── get_acknowledgment ────────────────────────────────────────────────────────

def test_get_acknowledgment_text():
    ack = get_acknowledgment("text")
    assert "Obrigada" in ack
    assert "compartilhar" in ack


def test_get_acknowledgment_link():
    ack = get_acknowledgment("link")
    assert "link" in ack.lower() or "🔗" in ack


def test_get_acknowledgment_image():
    ack = get_acknowledgment("image")
    assert "imagem" in ack.lower() or "🖼️" in ack


def test_get_acknowledgment_video():
    ack = get_acknowledgment("video")
    assert "vídeo" in ack.lower() or "🎥" in ack


def test_get_acknowledgment_audio():
    ack = get_acknowledgment("audio")
    assert "áudio" in ack.lower() or "🎙️" in ack


def test_get_acknowledgment_document():
    ack = get_acknowledgment("document")
    assert "documento" in ack.lower() or "📄" in ack


def test_get_acknowledgment_unknown_type_falls_back_to_text():
    ack = get_acknowledgment("unknowntype")
    assert ack == CONTENT_ACKNOWLEDGMENTS["text"]


def test_all_acknowledgments_under_300_chars():
    for content_type, msg in CONTENT_ACKNOWLEDGMENTS.items():
        assert len(msg) <= 300, f"Ack de '{content_type}' tem {len(msg)} chars"
