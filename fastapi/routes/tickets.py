from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import TicketOut, User
from security.auth import get_token_user
from sqlite_database import get_ticket_by_id

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "/{ticket_id}",
    response_model=TicketOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar um ticket pelo ID (protegido + checagem de propriedade)",
    description=(
        "Rota protegida por JWT (`Authorization: Bearer <token>`). Retorna o ticket "
        "apenas se o usuário autenticado for o dono do recurso (`owner_username`). "
        "Caso contrário retorna 403 Forbidden, mesmo que o ticket exista "
        "(controle anti-BOLA / Broken Object Level Authorization - TP3, item 3)."
    )
)
async def get_ticket(ticket_id: int, current_user: User = Depends(get_token_user)):
    row = get_ticket_by_id(ticket_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")

    if row["owner_username"] != current_user.username:
        # Controle de autorização a nível de objeto (anti-BOLA): o ticket
        # existe, mas pertence a outro usuário -> 403, nunca os dados do ticket.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: este ticket pertence a outro usuário."
        )

    return TicketOut(
        id=row["id"],
        owner_username=row["owner_username"],
        subject=row["subject"],
        text=row["text"],
        intent=row["intent"],
    )
