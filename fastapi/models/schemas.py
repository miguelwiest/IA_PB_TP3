from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Token(BaseModel):
    access_token: str = Field(..., description="Token de acesso JWT")
    token_type: str = Field(default="bearer", description="Tipo de autenticação do token")


class User(BaseModel):
    username: str = Field(..., description="Identificador único do usuário", json_schema_extra={"examples": ["admin"]})
    email: Optional[str] = Field(default=None, description="Email cadastrado", json_schema_extra={"examples": ["admin@infnet.edu.br"]})
    full_name: Optional[str] = Field(default=None, json_schema_extra={"examples": ["Administrador do Sistema"]})
    disabled: Optional[bool] = Field(default=False, description="Indica se o usuário está inativo")


class UserInDB(User):
    hashed_password: str = Field(..., description="Hash seguro da senha do usuário")


class PredictRequest(BaseModel):
    # TP3 - item 3 (validação de entrada): extra="forbid" garante que campos
    # não previstos pelo schema (ex.: "admin": true, "role": "admin") sejam
    # rejeitados com 422 em vez de silenciosamente ignorados.
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "text": "Não consigo conectar ao servidor remoto desde hoje de manhã. Erro 504."
                }
            ]
        }
    )

    text: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Texto ou descrição do ticket de suporte submetido pelo cliente"
    )


class PredictResponse(BaseModel):
    input_text: str = Field(..., description="Texto original submetido para análise")
    predicted_intent: str = Field(..., description="Intenção/categoria predita para o ticket", json_schema_extra={"examples": ["Technical issue"]})
    confidence: float = Field(..., description="Pontuação de confiança estimada (0 a 1)", json_schema_extra={"examples": [0.94]})
    simulated_model: str = Field(default="MockIntentClassifier-v1.0 (Simulation Phase)", description="Identificador do modelo")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Data e hora do processamento UTC")


class TicketOut(BaseModel):
    """Recurso retornado por GET /tickets/{id} (sujeito a checagem de dono - anti-BOLA)."""
    id: int = Field(..., description="Identificador do ticket")
    owner_username: str = Field(..., description="Usuário dono do ticket")
    subject: str = Field(..., description="Assunto do ticket")
    text: str = Field(..., description="Texto original do ticket")
    intent: str = Field(..., description="Intenção associada ao ticket")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Status operacional da API", json_schema_extra={"examples": ["ok"]})
    version: str = Field(default="3.0.0", description="Versão atual da API", json_schema_extra={"examples": ["3.0.0"]})
    service: str = Field(default="Customer Support Ticket API - PB TP3", description="Nome do microsserviço")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp da consulta")