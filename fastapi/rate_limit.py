"""
Limiter compartilhado (slowapi) para controle de rate limiting.

Definido em módulo próprio (em vez de dentro de main.py) para evitar import
circular: main.py precisa registrá-lo em app.state, e routes/auth.py precisa
decorar a rota de login com ele.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def rate_limit_key(request: Request) -> str:
    """
    Chave de rate limiting por cliente.

    Usa X-Forwarded-For quando presente (cenário comum atrás de proxy/load
    balancer) e cai para o IP remoto da conexão caso contrário. Isso também
    permite que os testes automatizados (TestClient, que sempre reporta o
    mesmo IP "testclient") isolem a janela de limite de cada teste enviando
    um X-Forwarded-For próprio, sem que um teste "gaste" a cota de outro.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded if forwarded else get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)
