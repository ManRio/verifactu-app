"""Permisos protegidos por API: ocultar un enlace no constituye autorización."""
from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.domain.user.model import User


def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    # Checkout necesita permitir un SUPERUSER con un plan aún pendiente.
    # Los endpoints comerciales siguen controlando la suscripción por separado.
    if current_user.role != "SUPERUSER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso reservado al superusuario")
    return current_user
