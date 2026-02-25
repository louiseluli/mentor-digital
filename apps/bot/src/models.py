import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class ConversationContext:
    """Estado completo de uma conversa — persistido em Redis como JSON.

    LGPD: user_id é SEMPRE pseudonimizado. Nunca armazenar telefone ou nome real.
    """

    user_id: str                                      # ID pseudonimizado
    platform: str                                     # 'whatsapp' | 'telegram' | 'terminal'
    content_type: str = ""                            # 'text' | 'link' | 'image' | 'video' | 'audio'
    content_raw: str = ""                             # Conteúdo original enviado
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    motivation: str = ""                              # Opção selecionada na primeira pergunta
    emotion: str = ""                                 # Emoção detectada ou declarada
    source_trust: str = ""                            # Nível de confiança na fonte
    reflection_answers: list = field(default_factory=list)
    final_decision: str = ""                          # 'share' | 'not_share' | 'investigate'
    analysis_results: dict = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_interaction_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    interaction_count: int = 0

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationContext":
        data = json.loads(json_str)
        return cls(**data)
