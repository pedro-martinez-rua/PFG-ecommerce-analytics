"""
groq_service.py — Generación de insights con IA.

SEGURIDAD CRÍTICA:
- Groq NUNCA recibe datos personales (emails, nombres, IDs de clientes)
- Solo recibe métricas agregadas ya calculadas
- El contexto se construye desde kpi_snapshots, no desde las tablas originales
"""
import os
from typing import Optional
from groq import Groq
from app.core.config import settings


def _build_context(kpis: dict, coverage: dict, period: str) -> str:
    """
    Construye el contexto que se envía a Groq.
    Solo métricas agregadas — nunca datos personales.
    """
    lines = [f"Periodo de análisis: {period}"]
    lines.append(f"Pedidos totales: {int(kpis.get('order_count', {}).get('value') or 0)}")

    revenue = kpis.get("total_revenue", {})
    if revenue.get("value"):
        lines.append(f"Revenue total: {revenue['value']:,.2f}")
        if revenue.get("growth_pct") is not None:
            lines.append(f"Crecimiento vs periodo anterior: {revenue['growth_pct']:+.1f}%")

    aov = kpis.get("avg_order_value", {})
    if aov.get("value"):
        lines.append(f"Valor medio de pedido: {aov['value']:,.2f}")

    gm = kpis.get("gross_margin_pct", {})
    if gm.get("value") and gm.get("availability") != "missing":
        avail_note = " (estimado)" if gm.get("availability") == "estimated" else ""
        lines.append(f"Margen bruto: {gm['value']:.1f}%{avail_note}")

    ret_rate = kpis.get("return_rate", {})
    if ret_rate.get("value") is not None and ret_rate.get("availability") != "missing":
        lines.append(f"Tasa de devolución: {ret_rate['value']:.1f}%")
        if ret_rate.get("growth_pct") is not None:
            lines.append(f"Cambio tasa de devolución: {ret_rate['growth_pct']:+.1f}%")

    repeat = kpis.get("repeat_purchase_rate", {})
    if repeat.get("value") is not None and repeat.get("availability") != "missing":
        lines.append(f"Tasa de recompra: {repeat['value']:.1f}%")

    ltv = kpis.get("avg_customer_ltv", {})
    if ltv.get("value") and ltv.get("availability") != "missing":
        lines.append(f"LTV medio por cliente: {ltv['value']:,.2f}")

    delayed = kpis.get("delayed_orders_pct", {})
    if delayed.get("value") is not None and delayed.get("availability") != "missing":
        lines.append(f"Pedidos con entrega retrasada: {delayed['value']:.1f}%")

    refund = kpis.get("refund_rate", {})
    if refund.get("value") is not None and refund.get("availability") != "missing":
        lines.append(f"Tasa de reembolsos sobre revenue: {refund['value']:.1f}%")

    return "\n".join(lines)


SYSTEM_PROMPT = """Eres un analista de negocio especializado en e-commerce. 
Tu función es interpretar métricas de ventas y dar recomendaciones claras y accionables 
a dueños de negocio sin conocimientos técnicos.

Reglas:
- Responde siempre en español
- Sé directo y concreto — el usuario quiere saber qué hacer, no solo qué pasó
- Usa lenguaje simple, sin jerga técnica
- Destaca 2-3 puntos clave máximo — no abrumes con información
- Si hay datos negativos, explica el impacto y sugiere una acción concreta
- Si los datos son positivos, refuerza qué está funcionando bien
- Máximo 150 palabras en total
- No menciones que eres una IA ni que estás analizando métricas
- Habla en segunda persona: "Tus ventas...", "Tu negocio..."
"""


def generate_insights(kpis: dict, coverage: dict, period: str) -> str:
    """
    Genera un párrafo de insights interpretando los KPIs.
    Nunca envía datos personales a Groq.
    """
    if not settings.GROQ_API_KEY:
        return _fallback_insights(kpis, coverage)

    context = _build_context(kpis, coverage, period)

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Analiza estas métricas de mi negocio:\n\n{context}"}
            ],
            max_tokens=300,
            temperature=0.3,   # Baja temperatura — respuestas consistentes y factuales
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return _fallback_insights(kpis, coverage)


def _fallback_insights(kpis: dict, coverage: dict) -> str:
    """
    Insights básicos sin IA — si Groq no está disponible.
    Lógica de reglas simples.
    """
    insights = []

    revenue = kpis.get("total_revenue", {})
    if revenue.get("growth_pct") is not None:
        growth = revenue["growth_pct"]
        if growth > 10:
            insights.append(f"Tus ventas crecieron un {growth:.1f}% respecto al periodo anterior.")
        elif growth < -10:
            insights.append(f"Tus ventas cayeron un {abs(growth):.1f}% respecto al periodo anterior. Revisa si hubo cambios en tu oferta o en el mercado.")
        else:
            insights.append(f"Tus ventas se mantienen estables con un cambio del {growth:+.1f}%.")

    ret = kpis.get("return_rate", {})
    if ret.get("value") is not None and ret.get("availability") != "missing":
        if ret["value"] > 10:
            insights.append(f"Tu tasa de devolución es del {ret['value']:.1f}%, por encima del umbral recomendado del 10%. Revisa la calidad del producto o las descripciones.")

    repeat = kpis.get("repeat_purchase_rate", {})
    if repeat.get("value") is not None and repeat.get("availability") != "missing":
        if repeat["value"] < 20:
            insights.append("Menos del 20% de tus clientes repiten compra. Considera implementar programas de fidelización.")
        else:
            insights.append(f"El {repeat['value']:.1f}% de tus clientes repite compra — una señal positiva de fidelización.")

    if not insights:
        insights.append("Sube más datos de ventas para obtener análisis más detallados.")

    return " ".join(insights)