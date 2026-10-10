"""Uniform error responses: {"error": {"code", "message", "details"}}."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

log = logging.getLogger(__name__)


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: object | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details


def not_found(entity: str, key: object) -> ApiError:
    return ApiError(404, "not_found", f"{entity} '{key}' não encontrado(a) ou não publicado(a).")


def _body(code: str, message: str, details: object | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=_body("http_error", str(exc.detail)), headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content=_body("validation_error", "Dados inválidos.", details))

    @app.exception_handler(IntegrityError)
    async def integrity_error(_: Request, exc: IntegrityError):
        msg = str(exc.orig).split("\n")[0] if exc.orig else str(exc)
        friendly = "Violação de integridade dos dados."
        if "ex_unit_subordinations_organic_overlap" in msg:
            friendly = "Sobreposição temporal: a unidade já possui uma subordinação orgânica nesse intervalo."
        elif "ex_person_positions_single_commander" in msg:
            friendly = "Sobreposição temporal: a unidade já possui um comandante titular nesse intervalo."
        elif "valid_interval" in msg or "_interval" in msg:
            friendly = "Intervalo de datas inválido: a data inicial deve ser anterior ou igual à final."
        elif "unique" in msg.lower() or "duplicate" in msg.lower():
            friendly = "Registro duplicado (identificador já existente)."
        elif "foreign key" in msg.lower():
            friendly = "Referência inválida ou registro ainda referenciado por outros dados."
        return JSONResponse(status_code=409, content=_body("integrity_error", friendly, msg))

    @app.exception_handler(OperationalError)
    async def db_unavailable(_: Request, exc: OperationalError):
        log.error("database error: %s", exc)
        return JSONResponse(status_code=503, content=_body("database_unavailable", "Banco de dados indisponível. Tente novamente em instantes."))
