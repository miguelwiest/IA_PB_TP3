"""
Suíte de testes de segurança do TP3 (PB).

Cobre os 5 aspectos exigidos no enunciado do TP3, item 3:
1. Autenticação (credenciais válidas e inválidas)       -> test_auth_*
2. Autorização / BOLA (dono != solicitante)              -> test_bola_*
3. Validação de entrada (Pydantic)                       -> test_validation_*
4. Rate limiting                                         -> test_rate_limit_*
5. Rota protegida sem token                              -> test_protected_route_*

Cada teste autentica usando o banco SQLite populado por sqlite_populate.py
(usuários "admin" e "cliente_fernanda", cada um dono de um ticket distinto),
o que permite exercitar BOLA de verdade (e não apenas um usuário único como
no TP1/TP2).

Usamos X-Forwarded-For com um valor exclusivo por teste (ver
fastapi/rate_limit.py) para que a cota de rate limiting de um teste não
"vaze" para outro teste que também bate em /auth/token.
"""
import sys
import time
from pathlib import Path

fastapi_dir = Path(__file__).resolve().parent.parent / "fastapi"
if str(fastapi_dir) not in sys.path:
    sys.path.insert(0, str(fastapi_dir))

from fastapi.testclient import TestClient
from main import app
from sqlite_populate import (
    ADMIN_USERNAME,
    ADMIN_PASSWORD_PLAIN,
    CUSTOMER_USERNAME,
    CUSTOMER_PASSWORD_PLAIN,
)

client = TestClient(app)


def _login(username: str, password: str, fwd_for: str) -> str:
    """Faz login e devolve o access_token (helper interno dos testes)."""
    resp = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"X-Forwarded-For": fwd_for},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ------------------------------------------------------------------ #
# 1. Autenticação
# ------------------------------------------------------------------ #
def test_auth_second_user_valid_and_invalid_credentials():
    """Credenciais válidas de um segundo usuário (SQLite) autenticam; senha errada não."""
    ok = client.post(
        "/auth/token",
        data={"username": CUSTOMER_USERNAME, "password": CUSTOMER_PASSWORD_PLAIN},
        headers={"X-Forwarded-For": "10.0.0.1"},
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    bad = client.post(
        "/auth/token",
        data={"username": CUSTOMER_USERNAME, "password": "senha-errada-123"},
        headers={"X-Forwarded-For": "10.0.0.1"},
    )
    assert bad.status_code == 401
    assert "detail" in bad.json()


# ------------------------------------------------------------------ #
# 2. Autorização / BOLA
# ------------------------------------------------------------------ #
def test_bola_user_cannot_access_other_users_ticket():
    """
    Broken Object Level Authorization: o ticket #1 pertence ao "admin" e o
    ticket #2 pertence a "cliente_fernanda". Cada usuário só pode ler o
    próprio ticket; tentar ler o do outro deve retornar 403 (não 200, e não
    vazar o conteúdo do recurso de outro dono).
    """
    admin_token = _login(ADMIN_USERNAME, ADMIN_PASSWORD_PLAIN, "10.0.0.2")
    customer_token = _login(CUSTOMER_USERNAME, CUSTOMER_PASSWORD_PLAIN, "10.0.0.2")

    # admin acessando o próprio ticket (#1) -> 200
    resp_own = client.get("/tickets/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_own.status_code == 200
    assert resp_own.json()["owner_username"] == ADMIN_USERNAME

    # admin tentando acessar o ticket do cliente (#2) -> 403, conteúdo não exposto
    resp_bola = client.get("/tickets/2", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_bola.status_code == 403
    assert "cliente" not in resp_bola.text.lower() or "pertence" in resp_bola.json()["detail"].lower()
    assert "Cobrança duplicada" not in resp_bola.text

    # o cliente tentando acessar o ticket do admin (#1) -> 403
    resp_bola_2 = client.get("/tickets/1", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp_bola_2.status_code == 403

    # o cliente acessando o próprio ticket (#2) -> 200
    resp_own_2 = client.get("/tickets/2", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp_own_2.status_code == 200
    assert resp_own_2.json()["owner_username"] == CUSTOMER_USERNAME


# ------------------------------------------------------------------ #
# 3. Validação de entrada (Pydantic)
# ------------------------------------------------------------------ #
def test_validation_rejects_extra_fields_and_short_text():
    """
    PredictRequest usa model_config(extra="forbid"): campos não previstos no
    schema (ex.: tentativa de injetar "role": "admin") devem ser rejeitados
    com 422, assim como um texto abaixo do min_length=3.
    """
    admin_token = _login(ADMIN_USERNAME, ADMIN_PASSWORD_PLAIN, "10.0.0.3")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Campo extra não permitido pelo schema
    resp_extra = client.post(
        "/predict",
        headers=headers,
        json={"text": "Preciso de ajuda com meu pedido.", "role": "admin"},
    )
    assert resp_extra.status_code == 422

    # Texto abaixo do tamanho mínimo exigido (min_length=3)
    resp_short = client.post("/predict", headers=headers, json={"text": "ab"})
    assert resp_short.status_code == 422

    # Payload sem o campo obrigatório "text"
    resp_missing = client.post("/predict", headers=headers, json={})
    assert resp_missing.status_code == 422


# ------------------------------------------------------------------ #
# 4. Rate limiting
# ------------------------------------------------------------------ #
def test_rate_limit_blocks_after_threshold():
    """
    POST /auth/token está limitado a 5 requisições/minuto por IP
    (slowapi, ver fastapi/rate_limit.py e routes/auth.py). A 6a requisição
    na mesma janela deve retornar 429, mesmo com credenciais corretas.
    """
    fwd_for = "203.0.113.77"  # IP exclusivo deste teste
    statuses = []
    for _ in range(6):
        resp = client.post(
            "/auth/token",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD_PLAIN},
            headers={"X-Forwarded-For": fwd_for},
        )
        statuses.append(resp.status_code)

    assert statuses[:5] == [200] * 5
    assert statuses[5] == 429


# ------------------------------------------------------------------ #
# 5. Rota protegida sem token
# ------------------------------------------------------------------ #
def test_protected_route_rejects_missing_token():
    """GET /tickets/{id} exige JWT; sem Authorization header deve retornar 401."""
    resp = client.get("/tickets/1")
    assert resp.status_code == 401
    assert resp.json()["detail"] != ""

    resp_me = client.get("/auth/me")
    assert resp_me.status_code == 401
