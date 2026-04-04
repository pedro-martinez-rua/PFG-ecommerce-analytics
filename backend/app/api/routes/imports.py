from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.import_record import Import
from app.schemas.import_schema import ImportResponse
from app.pipelines.import_orchestrator import run_import
from app.services.kpi_service import invalidate_kpi_cache

router  = APIRouter(prefix="/api/imports", tags=["imports"])
limiter = Limiter(key_func=get_remote_address)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE      = 100 * 1024 * 1024


@router.post("/", response_model=ImportResponse, status_code=201)
@limiter.limit("20/hour")
async def create_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sube y procesa un fichero CSV o XLSX."""
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400,
            detail=f"Formato no soportado. Se aceptan: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El fichero está vacío")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400,
            detail=f"El fichero supera el límite de {MAX_FILE_SIZE // (1024*1024)} MB")

    result = run_import(
        db=db,
        tenant_id=str(current_user.tenant_id),
        filename=file.filename,
        file_content=content
    )
    return ImportResponse(**result)


@router.get("/available-range")
def get_available_range(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rango de fechas disponible en todos los datos del tenant."""
    result = db.execute(text("""
        SELECT
            MIN(order_date) AS date_from,
            MAX(order_date) AS date_to,
            COUNT(*)        AS total_orders,
            COUNT(DISTINCT DATE_TRUNC('month', order_date)) AS months_with_data
        FROM orders
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": str(current_user.tenant_id)})

    row = result.fetchone()
    if not row or not row[0]:
        return {"has_data": False, "date_from": None,
                "date_to": None, "total_orders": 0, "months_with_data": 0}
    return {
        "has_data":         True,
        "date_from":        row[0].isoformat(),
        "date_to":          row[1].isoformat(),
        "total_orders":     row[2],
        "months_with_data": row[3]
    }


@router.get("/")
def list_imports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista imports del tenant con estadísticas y rango de fechas de sus datos."""
    result = db.execute(text("""
        SELECT
            i.id::text,
            i.filename,
            i.file_format,
            i.status,
            i.detected_type,
            i.total_rows,
            i.valid_rows,
            i.invalid_rows,
            i.file_size_bytes,
            i.created_at,
            i.completed_at,
            MIN(o.order_date) AS data_date_from,
            MAX(o.order_date) AS data_date_to,
            COUNT(o.id)       AS orders_loaded,
            COUNT(ol.id)      AS lines_loaded
        FROM imports i
        LEFT JOIN orders o
               ON o.import_id = i.id
              AND o.tenant_id = i.tenant_id
        LEFT JOIN order_lines ol
               ON ol.import_id = i.id
              AND ol.tenant_id = i.tenant_id
        WHERE i.tenant_id = :tenant_id
        GROUP BY i.id, i.filename, i.file_format, i.status, i.detected_type,
                 i.total_rows, i.valid_rows, i.invalid_rows,
                 i.file_size_bytes, i.created_at, i.completed_at
        ORDER BY i.created_at DESC
    """), {"tenant_id": str(current_user.tenant_id)})

    rows = result.fetchall()
    keys = list(result.keys())

    def serialize(v):
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        if hasattr(v, 'hex'):
            return str(v)
        return v

    return [{k: serialize(v) for k, v in zip(keys, row)} for row in rows]


@router.get("/{import_id}")
def get_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detalle de un import."""
    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")
    return record


@router.delete("/{import_id}", status_code=200)
def delete_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un import y TODOS sus datos del schema canónico.

    Elimina en cascada (respetando FKs):
    order_lines → orders → customers → products → raw_uploads → import_sheets → import
    """
    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=str(current_user.tenant_id)
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    tid = str(current_user.tenant_id)

    db.execute(text("""
        DELETE FROM order_lines
        WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})

    db.execute(text("""
        DELETE FROM orders
        WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})

    db.execute(text("""
        DELETE FROM customers
        WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})

    db.execute(text("""
        DELETE FROM products
        WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})
    
    db.execute(text("""
    DELETE FROM field_mappings
    WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})

    db.execute(text("""
        DELETE FROM raw_uploads
        WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})

    db.execute(text("""
        DELETE FROM import_sheets
        WHERE tenant_id = :tid AND import_id = :iid
    """), {"tid": tid, "iid": import_id})
    

    invalidate_kpi_cache(db, tid)

    db.delete(record)
    db.commit()

    return {
        "message":   f"Import '{record.filename}' eliminado correctamente",
        "import_id": import_id,
        "deleted":   True
    }