"""
explainer.py — Capa de explicabilidad del pipeline.

Traduce salidas técnicas del parser, detector y validador a mensajes útiles
para el usuario final.
"""
from __future__ import annotations

from collections import Counter
from typing import Any


ERROR_CATALOG: dict[str, dict[str, str]] = {
    "missing_required_field": {
        "title": "Campo obligatorio ausente",
        "message": "Falta un dato necesario para procesar esta fila.",
        "suggestion": "Revisa que la columna requerida exista y tenga valor en todas las filas.",
    },
    "future_date": {
        "title": "Fecha futura no válida",
        "message": "La fecha indicada es posterior al día actual.",
        "suggestion": "Corrige la fecha o revisa el formato usado en esa columna.",
    },
    "missing_identifier": {
        "title": "Falta identificador mínimo",
        "message": "No se ha encontrado un identificador suficiente para relacionar la fila.",
        "suggestion": "Incluye email, ID de cliente, ID de pedido u otro identificador estable.",
    },
    "unknown_type": {
        "title": "Tipo de archivo no reconocido",
        "message": "No se ha podido clasificar la estructura del archivo.",
        "suggestion": "Usa una cabecera clara e incluye columnas de fecha, importe, producto o cliente.",
    },
    "validation_error": {
        "title": "Error de validación",
        "message": "La fila contiene un valor que no cumple las reglas mínimas.",
        "suggestion": "Revisa formato, cabecera y coherencia de los valores del archivo.",
    },
}

WARNING_CATALOG: dict[str, dict[str, str]] = {
    "missing_total_amount": {
        "title": "Importe total ausente",
        "message": "No se ha encontrado un importe total en la fila.",
        "suggestion": "Incluye total_amount o columnas que permitan derivarlo con claridad.",
    },
    "negative_quantity": {
        "title": "Cantidad negativa",
        "message": "Se ha detectado una cantidad negativa.",
        "suggestion": "Puede indicar una devolución; revisa si ese comportamiento es correcto.",
    },
    "unrecognized_date_format": {
        "title": "Formato de fecha poco habitual",
        "message": "La fecha no sigue un formato fácilmente interpretable.",
        "suggestion": "Usa formatos como YYYY-MM-DD o DD/MM/YYYY.",
    },
    "parser_warning": {
        "title": "Advertencia de estructura",
        "message": "El archivo contiene elementos estructurales que pueden dificultar la lectura.",
        "suggestion": "Revisa cabecera, columnas vacías y nombres duplicados.",
    },
}


def _title_case(text: str) -> str:
    return text.replace("_", " ").strip().capitalize()


def warning_to_code(warning: dict[str, Any]) -> str:
    field = str(warning.get("field", "")).lower()
    message = str(warning.get("message", "")).lower()
    if field == "total_amount":
        return "missing_total_amount"
    if field == "quantity" and "negativa" in message:
        return "negative_quantity"
    if field == "order_date" and "formato" in message:
        return "unrecognized_date_format"
    return "parser_warning"


def summarize_validation_issues(results: list[Any]) -> dict[str, Any]:
    error_counter: Counter[str] = Counter()
    warning_counter: Counter[str] = Counter()

    for result in results:
        for error in getattr(result, "errors", []) or []:
            code = str(error.get("error_type") or "validation_error")
            error_counter[code] += 1
        for warning in getattr(result, "warnings", []) or []:
            warning_counter[warning_to_code(warning)] += 1

    top_errors = []
    for code, count in error_counter.most_common(5):
        meta = ERROR_CATALOG.get(code, ERROR_CATALOG["validation_error"])
        top_errors.append({
            "code": code,
            "title": meta["title"],
            "description": meta["message"],
            "suggestion": meta["suggestion"],
            "count": count,
        })

    top_warnings = []
    for code, count in warning_counter.most_common(5):
        meta = WARNING_CATALOG.get(code, WARNING_CATALOG["parser_warning"])
        top_warnings.append({
            "code": code,
            "title": meta["title"],
            "description": meta["message"],
            "suggestion": meta["suggestion"],
            "count": count,
        })

    main_issue_code = top_errors[0]["code"] if top_errors else (top_warnings[0]["code"] if top_warnings else None)
    user_explanations = [
        {"title": item["title"], "description": item["description"], "count": item["count"]}
        for item in (top_errors[:3] + top_warnings[:2])
    ]
    suggested_actions = []
    for item in top_errors + top_warnings:
        suggestion = item.get("suggestion")
        if suggestion and suggestion not in suggested_actions:
            suggested_actions.append(suggestion)

    return {
        "top_errors_detailed": top_errors,
        "top_warnings_detailed": top_warnings,
        "main_issue_code": main_issue_code,
        "user_explanations": user_explanations,
        "suggested_actions": suggested_actions[:5],
    }


def explain_detection(columns: list[str], detected_type: str, confidence: float) -> dict[str, Any]:
    normalized = [c.lower().strip().replace(" ", "_") for c in columns]
    has_date = any(any(k in c for k in ["date", "fecha", "created_at", "invoice_date"]) for c in normalized)
    has_amount = any(any(k in c for k in ["amount", "total", "sales", "price", "importe", "revenue"]) for c in normalized)
    has_product = any(any(k in c for k in ["product", "sku", "stock", "description", "item"]) for c in normalized)
    has_customer = any(any(k in c for k in ["customer", "email", "client", "user"]) for c in normalized)
    has_order_id = any(any(k in c for k in ["order", "invoice", "transaction", "external_id"]) for c in normalized)

    missing = []
    if not has_date:
        missing.append("fecha")
    if not has_amount:
        missing.append("importe")
    if not has_product:
        missing.append("producto")
    if not has_customer:
        missing.append("cliente")

    if detected_type == "unknown" or confidence < 0.3:
        message = "No se ha podido identificar una estructura mínima válida para clasificar el archivo."
        if missing:
            message += f" Faltan señales claras de {', '.join(missing[:3])}."
        suggestions = [
            "Asegúrate de que la primera fila útil contiene los nombres reales de las columnas.",
            "Incluye columnas reconocibles de fecha, producto, importe o cliente.",
        ]
        if not has_order_id:
            suggestions.append("Añade un identificador de pedido, factura o transacción si el archivo lo tiene.")
        return {
            "main_reason_code": "unknown_type",
            "main_reason": "Tipo de archivo no reconocido",
            "user_message": message,
            "diagnosis": message,
            "suggestions": suggestions[:4],
        }

    if detected_type == "mixed":
        message = "El archivo contiene señales de varios tipos de datos y no se puede interpretar de forma unívoca."
        return {
            "main_reason_code": "mixed_structure",
            "main_reason": "Estructura mixta o ambigua",
            "user_message": message,
            "diagnosis": message,
            "suggestions": [
                "Separa pedidos, productos y clientes en hojas o archivos distintos cuando sea posible.",
                "Mantén una estructura homogénea por hoja.",
            ],
        }

    message = f"La hoja se ha interpretado como '{detected_type}' con una confianza del {round(confidence * 100)}%."
    if confidence < 0.6:
        message += " La estructura es procesable, pero presenta cierta ambigüedad."
    return {
        "main_reason_code": None,
        "main_reason": None,
        "user_message": message,
        "diagnosis": message,
        "suggestions": [],
    }


def build_sheet_explanation(
    *,
    sheet_name: str,
    detected_type: str,
    confidence: float,
    columns: list[str],
    validation_summary: dict[str, Any] | None = None,
    file_warnings: list[str] | None = None,
) -> dict[str, Any]:
    detection = explain_detection(columns, detected_type, confidence)
    validation_summary = validation_summary or {}
    top_errors = validation_summary.get("top_errors_detailed", [])
    top_warnings = validation_summary.get("top_warnings_detailed", [])
    suggestions = list(detection.get("suggestions", []))

    for item in top_errors + top_warnings:
        suggestion = item.get("suggestion")
        if suggestion and suggestion not in suggestions:
            suggestions.append(suggestion)

    if file_warnings:
        parser_suggestion = "Revisa las advertencias de estructura del archivo antes de volver a subirlo."
        if parser_suggestion not in suggestions:
            suggestions.append(parser_suggestion)

    return {
        "sheet_name": sheet_name,
        "main_reason_code": detection.get("main_reason_code") or validation_summary.get("main_issue_code"),
        "main_reason": detection.get("main_reason") or (top_errors[0]["title"] if top_errors else None),
        "user_message": detection.get("user_message"),
        "diagnosis": detection.get("diagnosis"),
        "top_errors": top_errors,
        "top_warnings": top_warnings,
        "suggestions": suggestions[:6],
        "parser_warnings": file_warnings or [],
    }


def build_import_explanation(filename: str, status: str, sheets: list[dict[str, Any]]) -> dict[str, Any]:
    all_errors = []
    all_warnings = []
    suggestions = []
    main_reason = None
    main_reason_code = None
    user_message = None

    for sheet in sheets:
        if not main_reason and sheet.get("main_reason"):
            main_reason = sheet.get("main_reason")
            main_reason_code = sheet.get("main_reason_code")
            user_message = sheet.get("user_message")
        all_errors.extend(sheet.get("top_errors", []))
        all_warnings.extend(sheet.get("top_warnings", []))
        for suggestion in sheet.get("suggestions", []) or []:
            if suggestion not in suggestions:
                suggestions.append(suggestion)

    if not main_reason:
        if status == "completed":
            user_message = f"El archivo '{filename}' se ha procesado correctamente."
        elif status == "completed_with_errors":
            main_reason = "Se procesó con errores"
            user_message = f"El archivo '{filename}' se procesó, pero algunas filas no pudieron cargarse."
        else:
            main_reason = "Import fallido"
            user_message = f"El archivo '{filename}' no pudo procesarse correctamente."

    def _merge(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for item in items:
            code = item.get("code") or item.get("title") or "issue"
            if code not in grouped:
                grouped[code] = dict(item)
            else:
                grouped[code]["count"] = grouped[code].get("count", 0) + item.get("count", 0)
        return sorted(grouped.values(), key=lambda x: x.get("count", 0), reverse=True)[:5]

    return {
        "main_reason_code": main_reason_code,
        "main_reason": main_reason,
        "user_message": user_message,
        "top_errors": _merge(all_errors),
        "top_warnings": _merge(all_warnings),
        "suggestions": suggestions[:6],
    }
