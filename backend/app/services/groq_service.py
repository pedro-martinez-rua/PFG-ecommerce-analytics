from typing import Optional
from groq import Groq
from app.core.config import settings


SYSTEM_PROMPT = """
Eres el mejor consultor de negocio digital de España, con 20 años de experiencia ayudando a pequeñas empresas, autónomos y emprendedores a entender sus datos de ventas y tomar mejores decisiones.

Tu misión es analizar las métricas de un negocio de e-commerce y dar un análisis completo, honesto y muy práctico. Las personas que te leen NO son expertas en datos ni en finanzas. Muchas llevan su negocio solas, sin equipo, sin tiempo y con recursos limitados. Necesitan que alguien les explique exactamente qué está pasando, por qué importa y qué pueden hacer esta semana para mejorar.

REGLAS ABSOLUTAS — NUNCA LAS INCUMPLAS

IDIOMA Y TONO:
- Responde SIEMPRE en español, con un tono cercano, directo y empático
- Habla de "tu negocio", "tus ventas", "tus clientes" — en segunda persona
- Evita jerga técnica. Si usas un término técnico, explícalo en la misma frase
- No uses frases vacías como "es importante considerar" o "se recomienda explorar"
- Sé directo: di exactamente qué hacer, no sugerencias vagas

DATOS Y ESPECIFICIDAD:
- Menciona los números exactos de las métricas en CADA punto que expliques
- Compara siempre con benchmarks del sector cuando los tengas (los encontrarás en el contexto)
- Si un dato es bueno, dilo con entusiasmo. Si es preocupante, dilo con claridad sin alarmar
- No inventes datos que no están en el contexto — trabaja solo con lo que tienes

ESTRUCTURA OBLIGATORIA — SIGUE ESTE FORMATO EXACTO:

**Estado general de tu negocio**
[3-4 frases resumiendo el estado real del negocio con los números más importantes. Incluye si va bien, regular o necesita atención urgente. Menciona revenue total, pedidos y AOV con sus valores exactos.]

**Lo que está funcionando bien**
[2-3 puntos con lo que el negocio hace bien, con datos concretos que lo demuestren. Si el margen es bueno, dilo y explica qué significa. Si hay crecimiento, cuantifícalo.]

**Lo que necesita atención**
[2-3 puntos con los problemas o riesgos detectados, con datos exactos. Explica por qué es un problema y cuál es el impacto real en dinero o clientes perdidos si no se corrige.]

**Plan de acción: 5 cosas concretas que puedes hacer**
[5 recomendaciones MUY específicas y accionables, ordenadas de más a menos urgente. Cada una debe tener:
- Qué hacer exactamente (no "mejorar la retención" sino "envía un email a los clientes que compraron hace más de 60 días con un descuento del 10%")
- Por qué hacerlo (el dato que lo justifica)
- Cuándo hacerlo (esta semana / este mes / este trimestre)
- Qué resultado esperar (estimación realista)]
- PROHIBIDO dar recomendaciones vagas como "crear un plan de marketing" o "analizar la situación". Cada recomendación debe ser tan específica que el dueño pueda empezar a implementarla hoy mismo sin necesitar más información.

**Una reflexión final**
[1-2 frases de cierre con el mensaje más importante que el dueño del negocio debe llevarse. Que sea motivador pero realista.]

BENCHMARKS DEL SECTOR E-COMMERCE
Úsalos para contextualizar las métricas del negocio:
- Margen bruto e-commerce: 40-60% es normal, >60% es excelente, <30% es preocupante
- AOV (valor medio de pedido): varía mucho por sector, pero crecer el AOV un 10-15% es un objetivo realista
- Tasa de devoluciones: <5% excelente, 5-10% normal, >15% preocupante
- Tasa de recompra: <20% baja, 20-35% normal, >35% excelente
- LTV / AOV ratio: debería ser >3x (un cliente debería comprarte al menos 3 veces)
- Tasa de descuento sobre revenue: <5% saludable, 5-15% moderado, >20% puede erosionar márgenes
- Pedidos retrasados: <10% aceptable, >20% problema de operación
- Días de entrega: <3 días excelente, 3-7 normal, >10 días riesgo de abandono

CÓMO INTERPRETAR LOS DATOS QUE RECIBES
- Si "has_cogs: false" → no puedes calcular margen real, indícalo
- Si "availability: missing" en un KPI → ese dato no existe, no lo menciones
- Si "availability: estimated" → menciona que es una estimación
- La tendencia (primeros vs últimos meses) es muy importante — úsala para dar contexto temporal
- Si hay datos de canales, identifica el canal estrella y el canal con más potencial de mejora
- Si hay datos de productos, identifica el héroe (más revenue) y el producto con mejor margen
- El ratio pedidos/clientes únicos te dice cuánto repite de media un cliente — úsalo

EXTENSIÓN: Usa las palabras que necesites. Ni más ni menos. Lo que importa es que cada frase aporte valor real al dueño del negocio. Elimina cualquier relleno.
CONCISIÓN: El análisis completo debe caber en 600-700 palabras máximo. Sé directo y elimina cualquier repetición. Si una idea ya se mencionó, no la repitas.
"""


def _build_context(kpis: dict, coverage: dict, charts: dict, period: str) -> str:
    """
    Construye el contexto completo enviado a Groq.
    Solo métricas agregadas — nunca datos personales.
    """
    lines = [
        f"PERIODO ANALIZADO: {_format_period(period)}",
        "      MÉTRICAS PRINCIPALES    ",

    ]

    # Ventas principales
    order_count = kpis.get("order_count", {}).get("value")
    revenue     = kpis.get("total_revenue", {}).get("value")
    aov         = kpis.get("avg_order_value", {}).get("value")

    if order_count: lines.append(f"Pedidos totales: {int(order_count):,}")
    if revenue:     lines.append(f"Revenue total bruto: {revenue:,.2f}")
    if aov:         lines.append(f"Valor medio por pedido (AOV): {aov:,.2f}")

    rev = kpis.get("total_revenue", {})
    if rev.get("growth_pct") is not None:
        g = rev["growth_pct"]
        lines.append(f"Crecimiento revenue vs periodo anterior: {'↑' if g >= 0 else '↓'}{abs(g):.1f}%")

    net_rev = kpis.get("net_revenue", {})
    if net_rev.get("availability") != "missing" and net_rev.get("value"):
        lines.append(f"Revenue neto (descontados descuentos y devoluciones): {net_rev['value']:,.2f}")

    # Descuentos
    disc      = kpis.get("total_discounts", {})
    disc_rate = kpis.get("discount_rate", {})
    if disc.get("availability") != "missing" and disc.get("value"):
        lines.append(f"Total descuentos aplicados: {disc['value']:,.2f}")
    if disc_rate.get("availability") != "missing" and disc_rate.get("value") is not None:
        lines.append(f"Tasa de descuento sobre revenue: {disc_rate['value']:.2f}% [benchmark saludable: <5%]")

    # Rentabilidad
    lines += ["", "── RENTABILIDAD ──"]
    gm     = kpis.get("gross_margin", {})
    gm_pct = kpis.get("gross_margin_pct", {})
    refunds     = kpis.get("total_refunds", {})
    refund_rate = kpis.get("refund_rate", {})

    if gm_pct.get("availability") != "missing" and gm_pct.get("value") is not None:
        note = "ESTIMADO (COGS parcial)" if gm_pct.get("availability") == "estimated" else ""
        lines.append(f"Margen bruto: {gm_pct['value']:.1f}%{note} [benchmark: 40-60% normal, >60% excelente]")
    if gm.get("availability") != "missing" and gm.get("value"):
        lines.append(f"Beneficio bruto absoluto: {gm['value']:,.2f}")
    if refunds.get("availability") != "missing" and refunds.get("value"):
        lines.append(f"Total reembolsos: {refunds['value']:,.2f}")
    if refund_rate.get("availability") != "missing" and refund_rate.get("value") is not None:
        lines.append(f"Tasa de reembolso sobre revenue: {refund_rate['value']:.1f}% [benchmark: <5%]")

    # Clientes
    lines += ["", "── CLIENTES ──"]
    unique = kpis.get("unique_customers", {})
    repeat = kpis.get("repeat_purchase_rate", {})
    ltv    = kpis.get("avg_customer_ltv", {})
    nvr    = kpis.get("new_vs_returning", {})

    if unique.get("availability") != "missing" and unique.get("value"):
        u_val = unique["value"]
        lines.append(f"Clientes únicos en el periodo: {int(u_val):,}")
        if order_count and u_val:
            avg_orders_per_cust = round(int(order_count) / u_val, 2)
            lines.append(f"Media de pedidos por cliente: {avg_orders_per_cust} pedidos/cliente")

    if repeat.get("availability") != "missing" and repeat.get("value") is not None:
        lines.append(f"Tasa de recompra: {repeat['value']:.1f}% [benchmark: <20% baja, 20-35% normal, >35% excelente]")

    if ltv.get("availability") != "missing" and ltv.get("value"):
        ltv_aov_ratio = round(ltv["value"] / aov, 2) if aov else None
        lines.append(f"LTV medio por cliente: {ltv['value']:,.2f}")
        if ltv_aov_ratio:
            lines.append(f"Ratio LTV/AOV: {ltv_aov_ratio}x [benchmark saludable: >3x]")

    if nvr.get("availability") != "missing" and isinstance(nvr.get("value"), dict):
        new_c = nvr["value"].get("new", 0)
        ret_c = nvr["value"].get("returning", 0)
        total_c = new_c + ret_c
        if total_c > 0:
            lines.append(f"Clientes nuevos en el periodo: {new_c:,} ({new_c/total_c*100:.0f}%)")
            lines.append(f"Clientes recurrentes en el periodo: {ret_c:,} ({ret_c/total_c*100:.0f}%)")

    # Operación
    lines += ["", "── OPERACIÓN Y LOGÍSTICA ──"]
    ret_rate  = kpis.get("return_rate", {})
    ret_count = kpis.get("returned_orders", {})
    delivery  = kpis.get("avg_delivery_days", {})
    delayed   = kpis.get("delayed_orders_pct", {})

    if ret_rate.get("availability") != "missing" and ret_rate.get("value") is not None:
        lines.append(f"Tasa de devoluciones: {ret_rate['value']:.1f}% [benchmark: <5% excelente, <10% normal, >15% preocupante]")
    if ret_count.get("availability") != "missing" and ret_count.get("value"):
        lines.append(f"Número de pedidos devueltos: {int(ret_count['value']):,}")
    if delivery.get("availability") != "missing" and delivery.get("value"):
        lines.append(f"Días de entrega promedio: {delivery['value']:.1f} días [benchmark: <3 excelente, 3-7 normal, >10 preocupante]")
    if delayed.get("availability") != "missing" and delayed.get("value") is not None:
        lines.append(f"Porcentaje de pedidos con entrega retrasada: {delayed['value']:.1f}% [benchmark: <10% aceptable]")

    # Canales
    channel_data = charts.get("revenue_by_channel", [])
    if channel_data:
        lines += ["", "── CANALES DE VENTA ──"]
        total_ch = sum(c["value"] for c in channel_data) or 1
        for ch in sorted(channel_data, key=lambda x: x["value"], reverse=True):
            pct = ch["value"] / total_ch * 100
            lines.append(f"  {ch['label']}: {ch['value']:,.2f} ({pct:.1f}% del revenue total de canales)")

    # Países
    country_data = charts.get("revenue_by_country", [])
    if country_data:
        lines += ["", "── DISTRIBUCIÓN GEOGRÁFICA ──"]
        total_geo = sum(c["value"] for c in country_data) or 1
        for c in sorted(country_data, key=lambda x: x["value"], reverse=True)[:7]:
            pct = c["value"] / total_geo * 100
            lines.append(f"  {c['label']}: {c['value']:,.2f} ({pct:.1f}%)")

    # Productos
    top_prods = charts.get("top_products_revenue", [])
    if top_prods:
        lines += ["", "── TOP PRODUCTOS POR REVENUE ──"]
        total_prod = sum(p["value"] for p in top_prods) or 1
        for p in top_prods[:10]:
            pct = p["value"] / total_prod * 100
            lines.append(f"  {p['label']}: {p['value']:,.2f} ({pct:.1f}% del top-10)")

    top_units = charts.get("top_products_units", [])
    if top_units:
        lines += ["", "── TOP PRODUCTOS POR UNIDADES VENDIDAS ──"]
        for p in top_units[:5]:
            lines.append(f"  {p['label']}: {int(p['value']):,} unidades")

    # Categorías
    cat_data = charts.get("revenue_by_category", [])
    if cat_data:
        lines += ["", "── REVENUE POR CATEGORÍA ──"]
        total_cat = sum(c["value"] for c in cat_data) or 1
        for c in sorted(cat_data, key=lambda x: x["value"], reverse=True):
            pct = c["value"] / total_cat * 100
            lines.append(f"  {c['label']}: {c['value']:,.2f} ({pct:.1f}%)")

    # Margen por producto
    prod_margin = charts.get("product_margin", [])
    if prod_margin:
        lines += ["", "── MARGEN MEDIO POR PRODUCTO ──"]
        for p in sorted(prod_margin, key=lambda x: x["value"], reverse=True)[:5]:
            lines.append(f"  {p['label']}: {p['value']:.1f}% margen")

    # Estado de pedidos
    order_status = charts.get("orders_by_status", [])
    if order_status:
        lines += ["", "── ESTADO DE PEDIDOS ──"]
        total_st = sum(s["value"] for s in order_status) or 1
        for s in sorted(order_status, key=lambda x: x["value"], reverse=True):
            pct = s["value"] / total_st * 100
            lines.append(f"  {s['label']}: {int(s['value']):,} pedidos ({pct:.1f}%)")

    # Tendencia temporal
    rev_time = charts.get("revenue_over_time", [])
    if rev_time and len(rev_time) >= 4:
        lines += ["", "── TENDENCIA TEMPORAL ──"]
        first_3 = sum(p["value"] for p in rev_time[:3]) / 3
        last_3  = sum(p["value"] for p in rev_time[-3:]) / 3
        if first_3 > 0:
            trend = ((last_3 - first_3) / first_3) * 100
            lines.append(f"Revenue medio primeros 3 periodos: {first_3:,.0f}")
            lines.append(f"Revenue medio últimos 3 periodos: {last_3:,.0f}")
            lines.append(f"Variación de tendencia: {'↑' if trend > 0 else '↓'}{abs(trend):.0f}% "
                         f"({'crecimiento' if trend > 0 else 'caída'})")

        # Mejor y peor mes
        best  = max(rev_time, key=lambda x: x["value"])
        worst = min(rev_time, key=lambda x: x["value"])
        lines.append(f"Mejor periodo: {best['label']} con {best['value']:,.2f}")
        lines.append(f"Peor periodo: {worst['label']} con {worst['value']:,.2f}")

    # Órdenes en el tiempo
    ord_time = charts.get("orders_over_time", [])
    if ord_time and len(ord_time) >= 4:
        first_ord = sum(p["value"] for p in ord_time[:3]) / 3
        last_ord  = sum(p["value"] for p in ord_time[-3:]) / 3
        if first_ord > 0:
            ord_trend = ((last_ord - first_ord) / first_ord) * 100
            lines.append(f"Tendencia volumen de pedidos: {'↑' if ord_trend > 0 else '↓'}{abs(ord_trend):.0f}%")

    # Cobertura de datos
    lines += ["", "── CALIDAD DE LOS DATOS ──"]
    coverage_items = {
        "has_cogs":       "Costes de producto (COGS)",
        "has_channels":   "Canales de venta",
        "has_countries":  "Datos geográficos",
        "has_returns":    "Devoluciones",
        "has_discounts":  "Descuentos",
        "has_delivery":   "Tiempos de entrega",
        "has_customers":  "Datos de clientes",
        "has_categories": "Categorías de producto",
    }
    missing = [label for key, label in coverage_items.items() if not coverage.get(key, False)]
    available = [label for key, label in coverage_items.items() if coverage.get(key, False)]
    if available:
        lines.append(f"Datos disponibles: {', '.join(available)}")
    if missing:
        lines.append(f"Datos no disponibles (no analizar): {', '.join(missing)}")

    return "\n".join(lines)


def _format_period(period: str) -> str:
    mapping = {
        "last_30":   "últimos 30 días",
        "last_90":   "últimos 90 días",
        "ytd":       "año en curso",
        "last_year": "año anterior",
        "all":       "todos los datos disponibles",
        "custom":    "rango personalizado",
    }
    return mapping.get(period, period)


def generate_insights(
    kpis: dict,
    coverage: dict,
    period: str,
    charts: dict = None
) -> str:
    """
    Genera un análisis detallado con recomendaciones accionables.
    Nunca envía datos personales a Groq.
    """
    if charts is None:
        charts = {}

    if not settings.GROQ_API_KEY:
        return _fallback_insights(kpis, coverage)

    context = _build_context(kpis, coverage, charts, period)

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    "Aquí tienes todas las métricas de mi negocio de e-commerce. "
                    "Analízalas en detalle, sé muy específico con los números, "
                    "y dame recomendaciones concretas que pueda aplicar esta semana:\n\n"
                    + context
                )}
            ],
            max_tokens=800,
            temperature=0.2,
        )

        response_text  = response.choices[0].message.content.strip()
        finish_reason  = response.choices[0].finish_reason

        # Si Groq se quedó sin tokens, cerrar en el último punto completo
        # para evitar frases cortadas a mitad
        if finish_reason == "length":
            last_period = max(
                response_text.rfind("."),
                response_text.rfind("!"),
                response_text.rfind("?"),
            )
            # Solo cortar si hay suficiente contenido antes del último punto
            if last_period > len(response_text) * 0.6:
                response_text = response_text[:last_period + 1]

        return response_text

    except Exception:
        return _fallback_insights(kpis, coverage)


def _fallback_insights(kpis: dict, coverage: dict) -> str:
    """Insights de reglas básicas si Groq no está disponible."""
    parts = ["**Estado general de tu negocio**\n"]

    revenue     = kpis.get("total_revenue", {})
    orders      = kpis.get("order_count", {})
    aov         = kpis.get("avg_order_value", {})
    repeat      = kpis.get("repeat_purchase_rate", {})
    ret_rate    = kpis.get("return_rate", {})
    gm_pct      = kpis.get("gross_margin_pct", {})

    if revenue.get("value"):
        parts.append(
            f"Tu negocio generó {revenue['value']:,.2f} en "
            f"{int(orders.get('value') or 0):,} pedidos con un AOV de "
            f"{aov.get('value') or 0:,.2f}."
        )

    parts.append("\n\n**Plan de acción**\n")
    n = 1

    rev_growth = revenue.get("growth_pct")
    if rev_growth is not None:
        if rev_growth < -10:
            parts.append(
                f"{n}. **Recuperar ventas urgente**: Tus ventas cayeron un {abs(rev_growth):.1f}%. "
                f"Lanza esta semana una campaña de email a tus clientes con un descuento del 10-15% "
                f"por tiempo limitado. Objetivo: recuperar al menos un 5% de la caída en 30 días."
            )
            n += 1
        elif rev_growth > 15:
            parts.append(
                f"{n}. **Escalar lo que funciona**: Tus ventas crecieron un {rev_growth:.1f}%. "
                f"Identifica qué canal o producto está impulsando este crecimiento e invierte "
                f"un 20-30% más de presupuesto ahí este mes."
            )
            n += 1

    if gm_pct.get("availability") != "missing" and gm_pct.get("value") is not None:
        gm = gm_pct["value"]
        if gm < 30:
            parts.append(
                f"{n}. **Margen preocupante ({gm:.1f}%)**: Estás por debajo del 30%, que es el mínimo "
                f"recomendable. Revisa tus proveedores para negociar mejores precios o sube los precios "
                f"de venta un 5-10% en los productos con menos margen."
            )
            n += 1
        elif gm > 60:
            parts.append(
                f"{n}. **Margen excelente ({gm:.1f}%)**: Tienes un margen muy saludable. "
                f"Aprovéchalo para invertir en marketing de captación — puedes permitirte "
                f"gastar más por cliente nuevo que tu competencia."
            )
            n += 1

    if repeat.get("availability") != "missing" and repeat.get("value") is not None:
        rr = repeat["value"]
        if rr < 20:
            parts.append(
                f"{n}. **Mejorar retención ({rr:.1f}% recompra)**: Solo 1 de cada 5 clientes vuelve. "
                f"Implementa un email automático 15 días después de cada compra con una recomendación "
                f"personalizada. Objetivo: subir al 25% en 3 meses."
            )
            n += 1

    if ret_rate.get("availability") != "missing" and ret_rate.get("value") is not None:
        rr = ret_rate["value"]
        if rr > 10:
            parts.append(
                f"{n}. **Reducir devoluciones ({rr:.1f}%)**: El benchmark del sector es <10%. "
                f"Revisa los productos con más devoluciones, mejora sus fotos y descripciones "
                f"para que el cliente sepa exactamente lo que recibe."
            )
            n += 1

    if n < 3:
        parts.append(
            f"{n}. **Activa los datos que faltan**: Cuantos más datos tengas, mejores serán "
            f"las recomendaciones. Asegúrate de subir ficheros con datos de clientes, "
            f"canales de venta y tiempos de entrega para un análisis completo."
        )

    return "".join(parts)