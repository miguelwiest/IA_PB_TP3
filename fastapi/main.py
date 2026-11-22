import sys
import os
from pathlib import Path

# Garante que os módulos locais em fastapi/ sejam encontrados
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from routes import health_router, auth_router, predict_router, tickets_router
from sqlite_populate import populate
from rate_limit import limiter

# TP3: garante que o banco SQLite (usuários + tickets de exemplo de donos
# diferentes) exista e esteja populado antes da API aceitar requisições.
# Idempotente: pode ser chamado a cada subida do processo sem duplicar dados.
populate()

app = FastAPI(
    title="Customer Support Ticket Intelligent API",
    description=(
        "Esta API disponibiliza endpoints para monitoramento de integridade, "
        "autenticação segura via OAuth2 com tokens JWT, inferência simulada "
        "de intenção de tickets de suporte e consulta de tickets individuais "
        "com controle de propriedade (anti-BOLA), baseados no 'Customer "
        "Support Ticket Dataset'."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuração de CORS para permitir requisições de clientes web autorizados
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ZAP FIX (TP3 - item 5): a 1a auditoria (zap/zap_report_run1.html) acusou o
# finding "X-Content-Type-Options Header Missing" (Low). Embora não seja
# Medium/High (únicas severidades de correção obrigatória pelo enunciado),
# corrigimos aqui mesmo assim por boa prática: o header instrui o navegador a
# respeitar o Content-Type declarado em vez de "farejar" (MIME-sniffing) o
# corpo da resposta, mitigando ataques de XSS/execução de conteúdo disfarçado.
# Evidência da correção: zap/zap_report_run2.html (0 alertas) e
# zap/scan_passivo_zap_TP3.md.
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Registro modular de rotas
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(tickets_router)


@app.get("/", tags=["Root"])
async def root():
    """Rota raiz com links para documentação interativa e status."""
    return {
        "message": "Customer Support Ticket Intelligent API está em execução.",
        "docs": "/docs",
        "health": "/health",
        "auth": "/auth/token",
        "predict": "/predict",
        "tickets": "/tickets/{ticket_id}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8089, reload=True)
