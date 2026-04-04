
from sqlalchemy.orm import Session
from sqlalchemy import text


def resolve_order_line_to_orders(db: Session, tenant_id: str) -> int:
    """
    Vincula order_lines huérfanas (order_id IS NULL) con sus orders
    usando external_id como clave de unión.

    Caso: usuario sube orders.csv y luego order_items.csv.
    La order_line tiene external_id='1' → busca el order con external_id='1'.
    """
    result = db.execute(text("""
        UPDATE order_lines ol
        SET order_id = o.id
        FROM orders o
        WHERE ol.tenant_id   = :tenant_id
          AND o.tenant_id    = :tenant_id
          AND ol.order_id    IS NULL
          AND ol.external_id IS NOT NULL
          AND o.external_id  = ol.external_id
    """), {"tenant_id": tenant_id})

    resolved = result.rowcount
    if resolved > 0:
        db.commit()
    return resolved


def resolve_order_line_to_products(db: Session, tenant_id: str) -> int:
    """
    Vincula order_lines con sus productos usando SKU o nombre.
    """
    # Por SKU
    result_sku = db.execute(text("""
        UPDATE order_lines ol
        SET product_id = p.id
        FROM products p
        WHERE ol.tenant_id  = :tenant_id
          AND p.tenant_id   = :tenant_id
          AND ol.product_id IS NULL
          AND ol.sku        IS NOT NULL
          AND p.sku         = ol.sku
    """), {"tenant_id": tenant_id})

    # Por nombre de producto si no hay SKU
    result_name = db.execute(text("""
        UPDATE order_lines ol
        SET product_id = p.id
        FROM products p
        WHERE ol.tenant_id    = :tenant_id
          AND p.tenant_id     = :tenant_id
          AND ol.product_id   IS NULL
          AND ol.product_name IS NOT NULL
          AND p.name          = ol.product_name
    """), {"tenant_id": tenant_id})

    resolved = result_sku.rowcount + result_name.rowcount
    if resolved > 0:
        db.commit()
    return resolved


def resolve_orders_to_customers(db: Session, tenant_id: str) -> int:
    """
    Vincula orders con sus clientes usando customer external_id.
    """
    result = db.execute(text("""
        UPDATE orders o
        SET customer_id = c.id
        FROM customers c
        WHERE o.tenant_id     = :tenant_id
          AND c.tenant_id     = :tenant_id
          AND o.customer_id   IS NULL
          AND c.external_id   IS NOT NULL
          AND c.external_id   = o.external_id
    """), {"tenant_id": tenant_id})

    resolved = result.rowcount
    if resolved > 0:
        db.commit()
    return resolved


def run_all_resolvers(db: Session, tenant_id: str) -> dict:
    """
    Ejecuta todos los resolvers en el orden correcto.
    Llamar al final de cada import exitoso.
    """
    lines_to_orders   = resolve_order_line_to_orders(db, tenant_id)
    lines_to_products = resolve_order_line_to_products(db, tenant_id)
    orders_to_customers = resolve_orders_to_customers(db, tenant_id)

    return {
        "order_lines_linked_to_orders":   lines_to_orders,
        "order_lines_linked_to_products": lines_to_products,
        "orders_linked_to_customers":     orders_to_customers,
    }