"""
mapper.py — Tercera capa del pipeline.

Estrategia en 2 niveles:
  Nivel 1: Fuzzy matching de nombres de columna (rápido, cero coste)
  Nivel 2: Inferencia por contenido cuando fuzzy no resuelve

Nunca envía datos a servicios externos.
"""
import re
import pandas as pd
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from app.models.field_mapping import FieldMapping


# ─── Aliases canónicos ──────────────────────────────────────────────────────

CANONICAL_ALIASES: dict[str, list[str]] = {

    # ── PEDIDOS ─────────────────────────────────────────────────────────────
    "external_id": [
        "order_id","order_number","orderid","ordernumber",
        "invoice_no","invoiceno","invoice_number","invoicenumber",
        "transaction_id","transactionid","txn_id","txnid",
        "nº_pedido","num_pedido","pedido_id","order_ref",
        "sale_id","receipt_id","confirmation_number","reference_id",
        "checkout_id","booking_id","purchase_id",
    ],
    "order_date": [
        "order_date","date","fecha","fecha_pedido","created_at",
        "invoice_date","invoicedate","transaction_date","f_pedido",
        "purchase_date","sale_date","fecha_venta","fecha_compra",
        "event_time","order_timestamp","purchase_timestamp",
        "order_created","placed_at","submitted_at","sold_date",
        "transaction_time","order_placed","fecha_transaccion",
    ],
    "total_amount": [
        "total_amount","total_sales","price_usd","final_total",
        "total","importe","amount","revenue","pvp","sales",
        "gross_revenue","total_price_before_discount","order_total",
        "gross_sales","charged_amount","invoice_total","grand_total",
        "total_price","billing_total","sale_amount","selling_price",
        "total_value","order_value",
    ],
    "net_amount": [
        "net_amount","price_after_discount","net_total","importe_neto",
        "net_sales","total_neto","amount_after_discount","subtotal",
        "net_revenue","discounted_total","net_price","after_discount",
        "total_after_discount",
    ],
    "discount_amount": [
        "discount_amount","discount","descuento","discount_value",
        "discount_total","total_discount","promo_amount","coupon_amount",
        "savings","amount_saved","reduction","rebate_amount",
    ],
    "discount_rate": [
        "discount_percentage","discount_pct","descuento_pct",
        "discount_percent","pct_discount","promo_pct","rebate_pct",
        "discount_rate","discount_%","promo_percent","offer_pct",
        "sale_pct","markdown_pct",
    ],
    "shipping_cost": [
        "shipping_cost","shipping","envio","freight","delivery_cost",
        "shipping_fee","gastos_envio","postage","delivery_fee",
        "shipping_charge","freight_cost","transport_cost","logistic_cost",
    ],
    "cogs_amount": [
        "cogs_usd","cogs","total_cost","coste","unit_cost_total",
        "cost_of_goods","coste_total","cost_amount","total_cogs",
        "product_cost_total","landed_cost",
    ],
    "currency": [
        "currency","moneda","coin","divisa","currency_code",
        "iso_currency","transaction_currency",
    ],
    "channel": [
        "channel","canal","sales_channel","fuente","origin","source",
        "traffic_source","acquisition_channel","marketing_channel",
        "utm_medium","referral_source","sale_channel","order_source",
    ],
    "status": [
        "status","estado","order_status","estado_pedido",
        "fulfillment_status","delivery_status","shipment_status",
        "order_state","transaction_status","payment_status",
        "processing_status","order_flag",
    ],
    "payment_method": [
        "payment_method","payment","metodo_pago","forma_pago",
        "payment_type","medio_pago","payment_mode","pay_method",
        "payment_option","checkout_method","tender_type",
    ],
    "shipping_country": [
        "country","pais","shipping_country","ship_country",
        "destination","destination_country","country_code",
        "billing_country","customer_country","ship_to_country",
        "delivery_country","recipient_country",
    ],
    "shipping_region": [
        "state_code","state","region","provincia","comunidad",
        "state_province","billing_state","shipping_state",
        "county","territory","province","prefecture",
    ],
    "delivery_days": [
        "delivery_days","dias_entrega","days_to_deliver",
        "lead_time","shipping_days","days_for_shipping",
        "transit_days","estimated_delivery","fulfillment_days",
    ],
    "is_returned": [
        "return_status","returned","devuelto","is_returned",
        "refunded","is_refund","return_flag","has_return",
        "is_refunded","returned_item","order_returned",
    ],
    "session_id": [
        "website_session_id","session_id","visit_id","web_session",
        "browsing_session","user_session","tracking_id",
    ],
    "utm_source":   ["utm_source","fuente_trafico","traffic_source","ref_source"],
    "utm_campaign": ["utm_campaign","campaign","campaña","campaign_name","promo_code"],
    "device_type":  ["device_type","device","dispositivo","device_category","platform"],

    # ── CLIENTE ──────────────────────────────────────────────────────────────
    "customer_external_id": [
        "customer_id","customerid","user_id","userid","client_id",
        "clientid","id_cliente","buyer_id","shopper_id","member_id",
        "account_id","patron_id","contact_id","guest_id",
    ],
    "customer_email": [
        "customer_email","email","correo","mail","email_cliente",
        "buyer_email","contact_email","user_email","client_email",
        "billing_email","account_email","notification_email",
    ],
    "customer_name": [
        "customer_name","nombre_cliente","client_name","nombre",
        "full_name","buyer_name","nombre_completo","user_name",
        "shopper_name","account_name","recipient_name","contact_name",
        "billed_to","ship_to_name",
    ],

    # ── PRODUCTO ─────────────────────────────────────────────────────────────
    "product_external_id": [
        "product_id","productid","stock_code","stockcode","item_id",
        "id_producto","prod_id","primary_product_id","item_number",
        "product_ref","article_id","catalog_id","material_id",
    ],
    "product_name": [
        "product_name","product","description","descripcion",
        "nombre_producto","item_name","producto","articulo",
        "item","product_title","item_description","product_desc",
        "product_label","goods_name","merchandise",
    ],
    "sku": [
        "sku","stock_code","stockcode","reference","referencia",
        "codigo","item_sku","product_code","barcode","upc","asin",
        "ean","isbn","part_number","model_number","mpn",
    ],
    "category": [
        "category","categoria","product_category","tipo",
        "product_type","item_category","department","product_group",
        "item_type","merchandise_type","product_family","segment",
        "class","subcategory","line",
    ],
    "brand": [
        "brand","marca","manufacturer","fabricante","brand_name",
        "vendor","supplier","make","label","producer",
    ],
    "quantity": [
        "quantity","qty","units","unidades","cantidad",
        "items_purchased","num_units","order_qty","units_sold",
        "pieces","count","quantity_ordered","qty_sold","amount_ordered",
    ],
    "unit_price": [
        "unit_price","unitprice","price","precio","precio_unitario",
        "price_usd","pvp_unitario","item_price","sale_price",
        "selling_price","retail_price","list_price","msrp",
        "regular_price","base_price","original_price",
    ],
    "unit_cost": [
        "cogs_usd","unit_cost","coste_unitario","cost_usd",
        "item_cost","product_cost","cost_price","purchase_price",
        "landed_cost_per_unit","wholesale_price","buy_price",
    ],
    "line_total": [
        "line_total","total_line","subtotal","line_amount",
        "item_total","line_revenue","extended_price","ext_price",
        "row_total","position_total","item_value",
    ],
    "customer_rating": [
        "customer_rating","rating","satisfaction","puntuacion",
        "review_score","score","stars","feedback_score",
        "nps","review_rating","product_rating",
    ],
    "refund_amount": [
        "refund_amount","refund","reembolso","refund_total",
        "refund_usd","refund_value","refund_amount_usd",
        "return_amount","returned_amount","credit_amount",
    ],
    "is_primary_item": [
        "is_primary_item","primary_item","main_item","primary_product",
    ],
}

FUZZY_THRESHOLD = 75


# ─── Nivel 1: Fuzzy matching ─────────────────────────────────────────────────

def _normalize(col: str) -> str:
    return col.lower().strip().replace(" ", "_").replace("-", "_").replace(".", "_")


def infer_mapping_with_confidence(
    columns: list[str],
    df: pd.DataFrame | None = None,
) -> dict[str, dict]:
    """
    Infiere el mapping con confianza para cada columna.
    Aplica fuzzy en Nivel 1 y análisis de contenido en Nivel 2.

    Returns:
        {
            "Order_Date": {"canonical": "order_date", "confidence": 0.98, "method": "exact"},
            "Fch_Compra":  {"canonical": "order_date", "confidence": 0.81, "method": "fuzzy"},
            "Col_X":       {"canonical": "order_date", "confidence": 0.72, "method": "content"},
            "Unknown":     {"canonical": None,         "confidence": 0.0,  "method": "unresolved"},
        }
    """
    result: dict[str, dict] = {}
    already_assigned: dict[str, str] = {}  # canonical → col (para evitar duplicados)

    # ── Nivel 1: fuzzy ────────────────────────────────────────────────
    for col in columns:
        col_norm = _normalize(col)
        best_canonical = None
        best_score = 0.0
        best_method = "unresolved"

        for canonical, aliases in CANONICAL_ALIASES.items():
            for alias in aliases:
                score = fuzz.token_sort_ratio(col_norm, alias)
                if score > best_score:
                    best_score = score
                    best_canonical = canonical
                if best_score == 100:
                    break
            if best_score == 100:
                break

        if best_score >= FUZZY_THRESHOLD:
            best_method = "exact" if best_score == 100 else "fuzzy"
            result[col] = {
                "canonical":  best_canonical,
                "confidence": round(best_score / 100, 2),
                "method":     best_method,
            }
        else:
            result[col] = {
                "canonical":  None,
                "confidence": round(best_score / 100, 2),
                "method":     "unresolved",
            }

    # ── Nivel 2: análisis de contenido para los no resueltos ──────────
    if df is not None:
        for col in columns:
            if result[col]["canonical"] is not None:
                continue
            inferred = _infer_from_content(df, col)
            if inferred:
                result[col] = {
                    "canonical":  inferred,
                    "confidence": 0.70,
                    "method":     "content",
                }

    # ── Resolver duplicados: si dos columnas mapean al mismo canonical ─
    # Prioridad: exact > fuzzy > content. La de mayor confianza gana.
    canonical_to_best: dict[str, tuple[str, float]] = {}
    for col, info in result.items():
        if not info["canonical"]:
            continue
        c = info["canonical"]
        score = info["confidence"]
        if c not in canonical_to_best or score > canonical_to_best[c][1]:
            canonical_to_best[c] = (col, score)

    for col, info in result.items():
        if not info["canonical"]:
            continue
        c = info["canonical"]
        winner_col, _ = canonical_to_best[c]
        if col != winner_col:
            # Este duplicado va a extra_attributes con nombre original
            result[col] = {
                "canonical":  None,
                "confidence": info["confidence"],
                "method":     "duplicate_discarded",
            }

    return result


def _infer_from_content(df: pd.DataFrame, col: str) -> str | None:
    """
    Analiza los valores de una columna para inferir el campo canónico.
    Solo se usa cuando fuzzy no resuelve.
    """
    try:
        sample = df[col].dropna().astype(str).head(30).tolist()
        if not sample:
            return None
        n = len(sample)
        col_lower = col.lower()

        # Email
        email_re = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]{2,}$')
        if sum(1 for v in sample if email_re.match(v.strip())) / n > 0.6:
            return "customer_email"

        # Fecha (múltiples formatos)
        date_patterns = [
            r'^\d{4}[-/]\d{2}[-/]\d{2}',
            r'^\d{2}[-/]\d{2}[-/]\d{4}',
            r'^\d{1,2} \w{3} \d{4}',
            r'^\w+ \d{1,2},? \d{4}',
            r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}',
            r'^\d{2}\.\d{2}\.\d{4}',                    # DD.MM.YYYY (alemán)
        ]
        date_re = re.compile('|'.join(date_patterns))
        if sum(1 for v in sample if date_re.match(v.strip())) / n > 0.6:
            return "order_date"

        # ID de transacción prefijado
        order_id_re = re.compile(r'^(TXN|INV|ORD|SALE|ORDER|PO|SO|REC)[_\-]?\w+', re.I)
        if sum(1 for v in sample if order_id_re.match(v.strip())) / n > 0.5:
            return "external_id"

        # ID de cliente prefijado
        cust_id_re = re.compile(r'^(CUST|USR|USER|CLIENT|CLI|MEM|ACC)[_\-]?\w+', re.I)
        if sum(1 for v in sample if cust_id_re.match(v.strip())) / n > 0.5:
            return "customer_external_id"

        # Porcentaje → discount_rate
        nums = []
        for v in sample:
            try:
                nums.append(float(v.replace(',', '.').replace('%', '').strip()))
            except (ValueError, AttributeError):
                pass
        if len(nums) / n > 0.8 and nums:
            avg = sum(nums) / len(nums)
            if 0 <= avg <= 100 and max(nums) <= 100:
                if any(kw in col_lower for kw in ["disc","pct","percent","promo","rebate","off"]):
                    return "discount_rate"

        # País
        countries = {
            "spain","france","germany","usa","uk","united kingdom","mexico",
            "italy","india","china","brazil","canada","australia","japan",
            "netherlands","sweden","norway","denmark","poland","portugal",
            "españa","alemania","reino unido","japón","brasil","países bajos",
        }
        if sum(1 for v in sample if v.strip().lower() in countries) / n > 0.3:
            return "shipping_country"

        # Estado de pago / canal
        statuses = {"delivered","shipped","processing","cancelled","returned",
                    "pending","completed","failed","refunded","dispatched"}
        if sum(1 for v in sample if v.strip().lower() in statuses) / n > 0.4:
            if any(kw in col_lower for kw in ["status","state","estado"]):
                return "status"

        channels = {"direct","organic","paid","email","social","referral",
                    "search","affiliate","display","seo","sem","cpc"}
        if sum(1 for v in sample if v.strip().lower() in channels) / n > 0.3:
            return "channel"

        # Booleano de devolución
        yn_vals = {"yes","no","true","false","1","0","returned","devuelto","si","sí"}
        if sum(1 for v in sample if v.strip().lower() in yn_vals) / n > 0.8:
            if any(kw in col_lower for kw in ["return","devol","refund","reembolso"]):
                return "is_returned"

        return None
    except Exception:
        return None


# ─── Funciones públicas ───────────────────────────────────────────────────────

def infer_mapping(
    columns: list[str],
    df: pd.DataFrame | None = None,
) -> dict[str, str]:
    """
    Compatibilidad con código existente.
    Devuelve {columna_original: campo_canónico | None}.
    """
    full = infer_mapping_with_confidence(columns, df)
    return {col: info["canonical"] for col, info in full.items()}


def persist_mapping(
    db: Session,
    tenant_id: str,
    upload_type: str,
    mapping_with_confidence: dict[str, dict],
    import_id: str,
) -> None:
    """
    Guarda el mapping inferido en BD asociado al tenant.
    1 query para cargar existentes — crítico para CSVs con muchas columnas.
    """
    existing_mappings = {
        fm.source_column: fm
        for fm in db.query(FieldMapping).filter_by(
            tenant_id=tenant_id,
            upload_type=upload_type
        ).all()
    }

    for source_col, info in mapping_with_confidence.items():
        if not info.get("canonical"):
            continue
        if source_col in existing_mappings:
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
                import_id=import_id,
            )
            db.add(fm)
    db.commit()


def get_saved_mapping(
    db: Session,
    tenant_id: str,
    upload_type: str,
) -> dict[str, str] | None:
    mappings = db.query(FieldMapping).filter_by(
        tenant_id=tenant_id,
        upload_type=upload_type,
    ).all()
    if not mappings:
        return None
    return {fm.source_column: fm.canonical_field for fm in mappings}


def apply_mapping(
    row: dict,
    mapping: dict[str, str],
) -> tuple[dict, dict]:
    """
    Aplica el mapping a una fila del CSV.
    Devuelve (canonical_dict, extra_dict).
    """
    canonical: dict = {}
    extra: dict     = {}
    for col, value in row.items():
        target = mapping.get(col)
        if target:
            canonical[target] = value
        else:
            extra[col] = value
    return canonical, extra