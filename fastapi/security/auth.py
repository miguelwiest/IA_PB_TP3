import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from models.schemas import User, UserInDB
from sqlite_database import DB_PATH, get_user_by_username

# Configurações de Segurança do JWT
#
# ZAP FIX (TP3 - "segredo previsível/hardcoded" apontado na 1a rodada de scan):
# o literal abaixo só é usado como fallback de desenvolvimento quando a env
# var JWT_SECRET_KEY não está definida. Em qualquer ambiente real, o segredo
# deve vir de uma variável de ambiente/secret manager. Ver zap/scan_passivo_zap_TP3.md.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pb_infnet_super_secret_jwt_key_2026_x9a8b7c6")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Esquema de autenticação OAuth2PasswordBearer
# O tokenUrl aponta para a rota POST /auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_password_hash(password: str) -> str:
    """Gera o hash seguro de uma senha usando bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))


# ==============================================================================
# BASE DE USUÁRIOS (TP3: migrada do dicionário in-code do TP1/TP2 para SQLite)
# ==============================================================================
# Mantido apenas para compatibilidade/documentação (ex.: testes que validam
# a senha de referência do usuário admin, populada por sqlite_populate.py).
ADMIN_PASSWORD_PLAIN = "AdminInfnet2026!"

# "USERS_DB" deixou de ser um dicionário in-code: agora é o caminho do banco
# SQLite (fastapi/database.db), criado por sqlite_database.py e populado por
# sqlite_populate.py. O parâmetro `db` é mantido em get_user/authenticate_user
# por compatibilidade com as rotas existentes (routes/auth.py), mas passa a
# ser ignorado em favor da consulta real ao SQLite.
USERS_DB = DB_PATH


def get_user(db, username: str) -> Optional[UserInDB]:
    """Recupera os dados de um usuário a partir do banco SQLite."""
    row = get_user_by_username(username, db_path=DB_PATH)
    if row is None:
        return None
    return UserInDB(
        username=row["username"],
        email=row["email"],
        full_name=row["full_name"],
        disabled=bool(row["disabled"]),
        hashed_password=row["hashed_password"],
    )


def authenticate_user(db, username: str, password: str) -> Optional[UserInDB]:
    """Autentica o usuário validando login e senha contra o SQLite."""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um novo token JWT codificado com expiração."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now_utc})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Decodifica, valida e extrai 'sub' presente no header do token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except jwt.PyJWTError:
        return None


async def get_token_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependência FastAPI que extrai e valida o usuário a partir do token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado/ausente",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = verify_token(token)
    if username is None:
        raise credentials_exception
    user = get_user(USERS_DB, username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled
    )