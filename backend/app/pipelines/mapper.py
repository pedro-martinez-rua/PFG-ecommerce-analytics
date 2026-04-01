"""
mapper.py — Tercera capa del pipeline.

Responsabilidad: traducir los nombres de columna del CSV del cliente
al nombre canónico de nuestro schema.

Mejoras respecto a la versión anterior:
- Usa rapidfuzz para matching aproximado (maneja mayúsculas, espacios, guiones)
- Persiste los mappings en BD por tenant para reutilizarlos
- Devuelve confianza por cada campo mapeado
"""
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from app.models.field_mapping import FieldMapping


# Aliases canónicos — construidos a partir del análisis de todos los datasets reales
CANONICAL_ALIASES: dict[str, list[str]] = {
    # PEDIDOS
    "external_id":       ["order_id","order_number","orderid","ordernumber","invoice_no",
                          "invoiceno","transaction_id","transactionid","nº_pedido",
                          "num_pedido","pedido_id","order_ref"],
    "order_date":        ["order_date","date","fecha","fecha_pedido","created_at",
                          "invoice_date","invoicedate","transaction_date","f_pedido",
                          "purchase_date","sale_date","fecha_venta","fecha_compra"],
    "total_amount":      ["total_amount","total_sales","price_usd","final_total","total",
                          "importe","amount","revenue","pvp","sales","gross_revenue",
                          "total_price_before_discount","order_total"],
    "discount_amount":   ["discount_amount","discount","descuento","discount_value",
                          "discount_total","total_discount"],
    "net_amount":        ["net_amount","price_after_discount","net_total","importe_neto",
                          "net_sales","total_neto"],
    "shipping_cost":     ["shipping_cost","shipping","envio","freight","delivery_cost",
                          "shipping_fee","gastos_envio"],
    "cogs_amount":       ["cogs_usd","cogs","total_cost","coste","unit_cost_total",
                          "cost_of_goods","coste_total"],
    "currency":          ["currency","moneda","coin","divisa"],
    "channel":           ["channel","canal","sales_channel","fuente","origin"],
    "status":            ["status","estado","order_status","estado_pedido",
                          "fulfillment_status","delivery_status"],
    "payment_method":    ["payment_method","payment","metodo_pago","forma_pago",
                          "payment_type","medio_pago"],
    "shipping_country":  ["country","pais","shipping_country","ship_country",
                          "destination","destination_country","country_code"],
    "shipping_region":   ["state_code","state","region","provincia","comunidad",
                          "state_province","billing_state"],
    "delivery_days":     ["delivery_days","dias_entrega","days_to_deliver",
                          "lead_time","shipping_days"],
    "is_returned":       ["return_status","returned","devuelto","is_returned",
                          "refunded","is_refund","return_flag"],
    "session_id":        ["website_session_id","session_id","visit_id","web_session"],
    "utm_source":        ["utm_source","fuente_trafico","traffic_source"],
    "utm_campaign":      ["utm_campaign","campaign","campaña","campaign_name"],
    "device_type":       ["device_type","device","dispositivo","device_category"],
    # CLIENTE
    "customer_external_id": ["customer_id","customerid","user_id","userid","client_id",
                              "clientid","id_cliente","buyer_id"],
    "customer_email":    ["customer_email","email","correo","mail","email_cliente",
                          "buyer_email","contact_email"],
    "customer_name":     ["customer_name","nombre_cliente","client_name","nombre",
                          "full_name","buyer_name","nombre_completo"],
    # PRODUCTO
    "product_external_id": ["product_id","productid","stock_code","stockcode",
                             "item_id","id_producto","prod_id"],
    "product_name":      ["product_name","product","description","descripcion",
                          "nombre_producto","item_name","producto","articulo",
                          "item","product_title"],
    "sku":               ["sku","stock_code","stockcode","reference","referencia",
                          "codigo","item_sku","product_code"],
    "category":          ["category","categoria","product_category","tipo",
                          "product_type","item_category"],
    "brand":             ["brand","marca","manufacturer","fabricante","brand_name"],
    "quantity":          ["quantity","qty","units","unidades","cantidad",
                          "items_purchased","num_units","order_qty"],
    "unit_price":        ["unit_price","unitprice","price","precio","precio_unitario",
                          "price_usd","pvp_unitario","item_price","sale_price"],
    "unit_cost":         ["cogs_usd","unit_cost","coste_unitario","cost_usd",
                          "item_cost","product_cost"],
    "line_total":        ["line_total","total_line","subtotal","line_amount",
                          "item_total","line_revenue"],
    "customer_rating":   ["customer_rating","rating","satisfaction","puntuacion",
                          "review_score","score"],
    "refund_amount":     ["refund_amount","refund","reembolso","refund_total",
                          "refund_usd","refund_value"],
}

FUZZY_THRESHOLD = 75  # score mínimo para considerar un match válido


def _normalize(col: str) -> str:
    return col.lower().strip().replace(" ", "_").replace("-", "_").replace(".", "_")


def infer_mapping_with_confidence(columns: list[str]) -> dict[str, dict]:
    """
    Infiere el mapping con confianza para cada columna.

    Returns:
        {
            "Order_Date": {"canonical": "order_date", "confidence": 0.98, "method": "exact"},
            "Fch_Compra":  {"canonical": "order_date", "confidence": 0.81, "method": "fuzzy"},
            "Unknown_Col": {"canonical": None,         "confidence": 0.0,  "method": "unresolved"},
        }
    """
    result = {}

    for col in columns:
        col_norm = _normalize(col)
        best_canonical = None
        best_score = 0
        best_method = "unresolved"

        for canonical, aliases in CANONICAL_ALIASES.items():
            for alias in aliases:
                # Primero: coincidencia exacta (máxima confianza)
                if col_norm == alias:
                    best_canonical = canonical
                    best_score = 100
                    best_method = "exact"
                    break

                # Segundo: fuzzy matching
                score = fuzz.token_sort_ratio(col_norm, alias)
                if score > best_score and score >= FUZZY_THRESHOLD:
                    best_score = score
                    best_canonical = canonical
                    best_method = "fuzzy"

            if best_score == 100:
                break  # match exacto — no seguir buscando

        result[col] = {
            "canonical":  best_canonical,
            "confidence": round(best_score / 100, 2),
            "method":     best_method
        }

    return result


def infer_mapping(columns: list[str]) -> dict[str, str]:
    """
    Compatibilidad con código existente.
    Devuelve solo {columna_original: campo_canónico}.
    Columnas sin match devuelven None (van a extra_attributes).
    """
    full = infer_mapping_with_confidence(columns)
    return {col: info["canonical"] for col, info in full.items() if info["canonical"]}


def persist_mapping(
    db: Session,
    tenant_id: str,
    upload_type: str,
    mapping_with_confidence: dict[str, dict],
    import_id: str
) -> None:
    """
    Guarda el mapping inferido en BD asociado al tenant.
    Usa 1 query para cargar los mappings existentes en lugar de
    1 query por columna — crítico para CSVs con muchas columnas.
    """
    # 1 query para todos los mappings existentes de este tenant+type
    existing_mappings = {
        fm.source_column: fm
        for fm in db.query(FieldMapping).filter_by(
            tenant_id=tenant_id,
            upload_type=upload_type
        ).all()
    }

    for source_col, info in mapping_with_confidence.items():
        if not info["canonical"]:
            continue

        if source_col in existing_mappings:
            # Actualizar solo si la nueva confianza es mayor
            existing = existing_mappings[source_col]
            if info["confidence"] > (existing.confidence or 0):
                existing.confidence = info["confidence"]
        else:
            fm = FieldMapping(
                tenant_id=tenant_id,
                upload_type=upload_type,
                source_column=source_col,
                canonical_field=info["canonical"],
                confidence=info["confidence"],
                is_confirmed=info["method"] == "exact",
                import_id=import_id
            )
            db.add(fm)

    db.commit()

def get_saved_mapping(
    db: Session,
    tenant_id: str,
    upload_type: str
) -> dict[str, str] | None:
    """
    Recupera el mapping guardado en BD para este tenant y tipo.
    Devuelve None si no hay mapping guardado.
    """
    mappings = db.query(FieldMapping).filter_by(
        tenant_id=tenant_id,
        upload_type=upload_type
    ).all()

    if not mappings:
        return None

    return {fm.source_column: fm.canonical_field for fm in mappings}


def apply_mapping(row: dict, mapping: dict[str, str]) -> tuple[dict, dict]:
    """
    Aplica el mapping a una fila del CSV.
    Devuelve (canonical_dict, extra_dict).
    """
    canonical = {}
    extra = {}

    for col, value in row.items():
        if col in mapping and mapping[col]:
            canonical[mapping[col]] = value
        else:
            extra[col] = value

    return canonical, extra