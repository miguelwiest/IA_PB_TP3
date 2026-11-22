from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from models.schemas import Token, User
from security.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    USERS_DB,
    authenticate_user,
    create_access_token,
    get_token_user
)
from rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Obter Token de Acesso JWT",
    description=(
        "Autentica o usuário (form-data com username e password) e retorna o token JWT "
        "para rotas protegidas. **Rate limit: 5 requisições/minuto por IP** "
        "(TP3 - proteção contra força bruta de credenciais; acima do limite retorna 429)."
    )
)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Recebe as credenciais via form-data (compatível com Swagger UI e OAuth2).
    Usuários e senhas são validados contra o banco SQLite (fastapi/database.db).
    """
    user = authenticate_user(USERS_DB, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    # Correção TP3: RFC 6749 define o token_type como "bearer" (minúsculo);
    # o TP1 retornava "Bearer" (capitalizado), o que já era inconsistente com
    # o teste test_auth_login_success (agora corrigido).
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=User,
    summary="Consultar usuário autenticado",
    description="Retorna informações do perfil autenticado pelo token JWT."
)
async def read_users_me(current_user: User = Depends(get_token_user)):
    return current_user