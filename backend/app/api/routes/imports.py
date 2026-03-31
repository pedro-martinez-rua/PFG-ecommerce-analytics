from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.import_record import Import
from app.schemas.import_schema import ImportResponse
from app.pipelines.import_orchestrator import run_import

router  = APIRouter(prefix="/api/imports", tags=["imports"])
limiter = Limiter(key_func=get_remote_address)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE      = 100 * 1024 * 1024  # 100 MB


@router.post("/", response_model=ImportResponse, status_code=201)
@limiter.limit("20/hour")
async def create_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un fichero CSV o XLSX y lo procesa completamente.
    Soporta múltiples hojas en XLSX.
    Rate limit: 20 uploads por hora por IP.
    El tenant_id se extrae del JWT — nunca del body del request.
    """
    # Validar extensión
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Se aceptan: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Leer en memoria — nunca a disco
    content = await file.read()

    # Validar que no está vacío
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="El fichero está vacío"
        )

    # Validar tamaño
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"El fichero supera el límite de {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    result = run_import(
        db=db,
        tenant_id=str(current_user.tenant_id),
        filename=file.filename,
        file_content=content
    )

    return ImportResponse(**result)


@router.get("/")
def list_imports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos los imports del tenant autenticado — ordenados por fecha descendente."""
    imports = db.query(Import).filter_by(
        tenant_id=current_user.tenant_id
    ).order_by(Import.created_at.desc()).all()

    return [
        {
            "import_id":    str(i.id),
            "filename":     i.filename,
            "file_format":  i.file_format,
            "status":       i.status,
            "total_rows":   i.total_rows,
            "valid_rows":   i.valid_rows,
            "invalid_rows": i.invalid_rows,
            "detected_type": i.detected_type,
            "created_at":   i.created_at.isoformat() if i.created_at else None,
        }
        for i in imports
    ]


@router.get("/{import_id}")
def get_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detalle completo de un import.
    Solo accesible por el tenant propietario — aislamiento garantizado.
    """
    import_record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()

    if not import_record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    return import_record