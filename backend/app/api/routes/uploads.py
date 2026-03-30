from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.upload import UploadResponse
from app.pipelines.loader import load_csv

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/", response_model=UploadResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un fichero CSV y lo procesa completo.
    Requiere autenticación — el tenant_id se extrae del JWT.

    El sistema detecta automáticamente si el CSV contiene
    orders, customers, products o una mezcla.
    """
    # Validar extensión
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan ficheros .csv"
        )

    # Leer contenido
    content = await file.read()

    # Validar tamaño
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="El fichero supera el límite de 10 MB"
        )

    # Procesar pipeline completo
    result = load_csv(
        db=db,
        tenant_id=str(current_user.tenant_id),
        filename=file.filename,
        file_content=content
    )

    return UploadResponse(**result)