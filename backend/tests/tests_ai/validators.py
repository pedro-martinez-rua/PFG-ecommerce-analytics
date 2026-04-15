import re
from typing import Any


REQUIRED_SECTIONS = [
    "estado general de tu negocio",
    "lo que esta funcionando bien",
    "lo que necesita atencion",
    "plan de accion",
    "una reflexion final",
]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def contains_any(text: str, terms: list[str]) -> bool:
    norm_text = normalize_text(text)
    return any(normalize_text(term) in norm_text for term in terms)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def format_number_variants(value: Any) -> list[str]:
    variants = set()

    if value is None or isinstance(value, bool):
        return []

    if isinstance(value, (int, float)):
        if float(value).is_integer():
            iv = int(value)
            variants.add(str(iv))
            variants.add(f"{iv:,}")
            variants.add(f"{iv:,}".replace(",", "."))
        else:
            fv = float(value)
            variants.add(f"{fv:.1f}")
            variants.add(f"{fv:.2f}")
            variants.add(f"{fv:.1f}".replace(".", ","))
            variants.add(f"{fv:.2f}".replace(".", ","))
            variants.add(str(round(fv)))

    return list(variants)


def extract_expected_numbers(case: dict) -> list[str]:
    keys = [
        "total_revenue",
        "order_count",
        "avg_order_value",
        "net_revenue",
        "gross_margin_pct",
        "repeat_purchase_rate",
        "discount_rate",
        "refund_rate",
        "return_rate",
    ]

    values = []
    for key in keys:
        value = case["kpis"].get(key, {}).get("value")
        values.extend(format_number_variants(value))

    return list(dict.fromkeys(values))


def validate_structure(text: str, case: dict) -> dict:
    errors = []
    lower = normalize_text(text)

    required_present = sum(1 for section in REQUIRED_SECTIONS if section in lower)
    required_ratio = required_present / len(REQUIRED_SECTIONS)

    wc = word_count(text)
    if wc < 250:
        errors.append(f"too_short:{wc}")

    expected_numbers = extract_expected_numbers(case)
    found_numbers = sum(1 for num in expected_numbers if num and num in text)
    number_ratio = min(found_numbers / 5.0, 1.0)

    structure_score = round((0.65 * required_ratio) + (0.35 * number_ratio), 4)

    available_kpi_count = sum(
        1 for key in ["total_revenue","order_count","avg_order_value","net_revenue",
                    "gross_margin_pct","repeat_purchase_rate","discount_rate","refund_rate","return_rate"]
        if case["kpis"].get(key, {}).get("value") is not None
    )
    min_numbers = max(2, min(4, available_kpi_count - 1))
    passed = required_ratio >= 0.8 and wc >= 250 and found_numbers >= min_numbers


    if required_ratio < 0.8:
        errors.append("missing_required_sections")
    if found_numbers < 4:
        errors.append(f"missing_key_numbers:{found_numbers}")

    return {
        "passed": passed,
        "errors": errors,
        "word_count": wc,
        "required_ratio": round(required_ratio, 4),
        "found_numbers": found_numbers,
        "structure_score": structure_score,
    }


def validate_semantics(text: str, reference: str, bertscore_metric, meteor_metric) -> dict:
    bert = bertscore_metric.compute(
        predictions=[text],
        references=[reference],
        lang="es",
    )

    meteor = meteor_metric.compute(
        predictions=[text],
        references=[reference],
    )

    return {
        "bertscore_precision": bert["precision"][0],
        "bertscore_recall": bert["recall"][0],
        "bertscore_f1": bert["f1"][0],
        "meteor": meteor["meteor"],
    }


def validate_facts(text: str, fact_checks: list[dict]) -> dict:
    passed_checks = 0
    failed_checks = []
    hallucinations = []

    for check in fact_checks:
        ctype = check["type"]

        if ctype in {"classification", "trend"}:
            if contains_any(text, check["accepted_terms"]):
                passed_checks += 1
            else:
                failed_checks.append(check["id"])

        elif ctype == "forbidden_topic":
            if contains_any(text, check["topic_terms"]):
                failed_checks.append(check["id"])
                hallucinations.append(check["id"])
            else:
                passed_checks += 1

        else:
            failed_checks.append(check["id"])

    total = len(fact_checks)
    factual_score = passed_checks / total if total else 1.0

    return {
        "passed_checks": passed_checks,
        "total_checks": total,
        "factual_score": round(factual_score, 4),
        "failed_checks": failed_checks,
        "hallucinations": hallucinations,
        "hallucination_count": len(hallucinations),
    }


def aggregate_case_result(structure_result: dict, semantic_result: dict, factual_result: dict) -> dict:
    final_score = round(
        (0.25 * structure_result["structure_score"]) +
        (0.35 * semantic_result["bertscore_f1"]) +
        (0.10 * semantic_result["meteor"]) +
        (0.30 * factual_result["factual_score"]),
        4
    )

    return {
        "final_score": final_score,
        "structure": structure_result,
        "semantics": semantic_result,
        "facts": factual_result,
    }