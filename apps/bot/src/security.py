import hashlib
import os


def pseudonymize(identifier: str) -> str:
    """Converte telefone ou user ID em pseudônimo irreversível.

    Usa SHA-256 com pepper — one-way, consistente entre sessões.
    NUNCA armazenar o identificador original (LGPD Art. 12).
    """
    pepper = _get_pepper("PSEUDONYMIZATION_PEPPER")
    salted = f"{pepper}:{identifier}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def pseudonymize_for_analytics(identifier: str) -> str:
    """Pseudônimo separado para analytics — impede cruzamento com banco operacional.

    Dois peppers diferentes = dois namespaces isolados.
    """
    pepper = _get_pepper("ANALYTICS_PEPPER")
    salted = f"{pepper}:{identifier}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def _get_pepper(env_var: str) -> str:
    pepper = os.environ.get(env_var)
    if not pepper:
        raise ValueError(f"Variável de ambiente obrigatória não definida: {env_var}")
    return pepper
