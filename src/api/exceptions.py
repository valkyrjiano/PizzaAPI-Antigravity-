"""RFC 9457 / Problem Details standard exceptions and FastAPI exception handlers.

Ensures all error responses strictly adhere to the ApiError schema:
- type: URI identifier
- title: Short error title
- status: HTTP status code
- detail: Explanation of the error
- instance: Request URL path
- invalidParams: List of field errors for validation failures
"""

from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

ERROR_TYPE_MAP = {
    400: ("https://api.pizzariabarriga.dev/errors/bad-request", "Bad Request"),
    401: ("https://api.pizzariabarriga.dev/errors/unauthorized", "Unauthorized"),
    403: ("https://api.pizzariabarriga.dev/errors/forbidden", "Forbidden"),
    404: ("https://api.pizzariabarriga.dev/errors/not-found", "Not Found"),
    422: ("https://api.pizzariabarriga.dev/errors/validation-error", "Validation Error"),
}


def create_problem_details_response(
    status_code: int,
    title: str,
    detail: str,
    type_uri: str,
    instance: str,
    invalid_params: Optional[List[Dict[str, str]]] = None,
) -> JSONResponse:
    """Build a standard RFC 9457 Problem Details JSONResponse."""
    payload: Dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
    }
    if invalid_params is not None:
        payload["invalidParams"] = invalid_params

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
    )


class AppException(Exception):
    """Base application exception for RFC 9457 compliant error reporting."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        title: Optional[str] = None,
        type_uri: Optional[str] = None,
        instance: Optional[str] = None,
        invalid_params: Optional[List[Dict[str, str]]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        default_type, default_title = ERROR_TYPE_MAP.get(
            status_code,
            ("https://api.pizzariabarriga.dev/errors/internal-error", "Internal Server Error"),
        )
        self.title = title or default_title
        self.type_uri = type_uri or default_type
        self.instance = instance or ""
        self.invalid_params = invalid_params
        super().__init__(self.detail)


class BadRequestException(AppException):
    """HTTP 400 Bad Request exception."""

    def __init__(
        self,
        detail: str = "A requisição enviada é inválida ou está malformada.",
        instance: Optional[str] = None,
        invalid_params: Optional[List[Dict[str, str]]] = None,
    ):
        super().__init__(
            status_code=400,
            detail=detail,
            title="Bad Request",
            type_uri="https://api.pizzariabarriga.dev/errors/bad-request",
            instance=instance,
            invalid_params=invalid_params,
        )


class UnauthorizedException(AppException):
    """HTTP 401 Unauthorized exception."""

    def __init__(
        self,
        detail: str = "Credenciais ausentes, inválidas ou expiradas.",
        instance: Optional[str] = None,
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            title="Unauthorized",
            type_uri="https://api.pizzariabarriga.dev/errors/unauthorized",
            instance=instance,
        )


class ForbiddenException(AppException):
    """HTTP 403 Forbidden exception."""

    def __init__(
        self,
        detail: str = "Acesso negado: você não possui permissão para acessar este recurso.",
        instance: Optional[str] = None,
    ):
        super().__init__(
            status_code=403,
            detail=detail,
            title="Forbidden",
            type_uri="https://api.pizzariabarriga.dev/errors/forbidden",
            instance=instance,
        )


class NotFoundException(AppException):
    """HTTP 404 Not Found exception."""

    def __init__(
        self,
        detail: str = "O recurso solicitado não foi encontrado.",
        instance: Optional[str] = None,
    ):
        super().__init__(
            status_code=404,
            detail=detail,
            title="Not Found",
            type_uri="https://api.pizzariabarriga.dev/errors/not-found",
            instance=instance,
        )


class ValidationException(AppException):
    """HTTP 422 Validation Error exception."""

    def __init__(
        self,
        detail: str = "Falha na validação dos campos enviados.",
        instance: Optional[str] = None,
        invalid_params: Optional[List[Dict[str, str]]] = None,
    ):
        super().__init__(
            status_code=422,
            detail=detail,
            title="Validation Error",
            type_uri="https://api.pizzariabarriga.dev/errors/validation-error",
            instance=instance,
            invalid_params=invalid_params or [],
        )


# Aliases
BadRequestError = BadRequestException
UnauthorizedError = UnauthorizedException
ForbiddenError = ForbiddenException
NotFoundError = NotFoundException
ValidationError = ValidationException


# ==========================================
# FastAPI Global Exception Handlers
# ==========================================


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application domain exceptions."""
    instance = exc.instance or request.url.path
    return create_problem_details_response(
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        type_uri=exc.type_uri,
        instance=instance,
        invalid_params=exc.invalid_params,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI validation exceptions (RFC 9457 status 422 or 400 for malformed json)."""
    errors = exc.errors()
    invalid_params: List[Dict[str, str]] = []
    is_malformed_json = False

    for err in errors:
        err_type = err.get("type", "")
        # Detect malformed JSON body
        if "json_invalid" in err_type or "json_decode" in err_type:
            is_malformed_json = True

        loc = err.get("loc", ())
        if loc:
            # Drop 'body', 'query', or 'path' if it's the first element
            field_parts = [str(part) for part in loc if part not in ("body",)]
            field_name = ".".join(field_parts) if field_parts else str(loc[-1])
        else:
            field_name = "payload"

        msg = err.get("msg", "Valor inválido")
        # Clean up Pydantic prefix if present
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]

        invalid_params.append({"name": field_name, "reason": msg})

    if is_malformed_json:
        return create_problem_details_response(
            status_code=400,
            title="Bad Request",
            detail="O corpo da requisição contém JSON inválido ou malformado.",
            type_uri="https://api.pizzariabarriga.dev/errors/bad-request",
            instance=request.url.path,
            invalid_params=invalid_params,
        )

    return create_problem_details_response(
        status_code=422,
        title="Validation Error",
        detail="Erro de validação nos parâmetros da requisição.",
        type_uri="https://api.pizzariabarriga.dev/errors/validation-error",
        instance=request.url.path,
        invalid_params=invalid_params,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette and FastAPI HTTPExceptions."""
    status_code = exc.status_code
    type_uri, default_title = ERROR_TYPE_MAP.get(
        status_code,
        ("https://api.pizzariabarriga.dev/errors/internal-error", "Internal Server Error"),
    )
    detail = str(exc.detail) if exc.detail else default_title

    return create_problem_details_response(
        status_code=status_code,
        title=default_title,
        detail=detail,
        type_uri=type_uri,
        instance=request.url.path,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all RFC 9457 exception handlers on the FastAPI application."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
