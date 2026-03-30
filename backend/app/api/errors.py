from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Manejador global de errores HTTP.
    Equivale a @ControllerAdvice de Spring.
    Devuelve siempre el mismo formato:
    {"detail": "mensaje", "status_code": 404}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )