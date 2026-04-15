"""
test_ai_insights_benchmark.py — Benchmark comparativo de prompts para llama-3.3-70b.

Matriz: 5 prompts x 6 casos = 30 evaluaciones.
Cada celda mide: BERTScore F1, METEOR y factual score.
Al final imprime un ranking de prompts por metrica agregada.

Se salta si GROQ_API_KEY no esta configurada.
"""
import os
import pytest

from app.services.groq_service import generate_insights, _build_context
from tests.tests_ai.cases import BENCHMARK_CASES
from tests.tests_ai.prompt_variants import PROMPT_VARIANTS
from tests.tests_ai.validators import (
    validate_structure,
    validate_semantics,
    validate_facts,
)
from tests.tests_ai.reporting import print_case_report, print_prompt_ranking


pytestmark = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY no configurada — benchmark LLM omitido"
)


@pytest.fixture(scope="session")
def bertscore_metric():
    import evaluate
    return evaluate.load("bertscore")


@pytest.fixture(scope="session")
def meteor_metric():
    import evaluate
    import nltk
    nltk.download("wordnet", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    return evaluate.load("meteor")


# Genera todas las respuestas una sola vez para toda la sesion
# Evita duplicar llamadas a la API entre test_benchmark_matrix y test_prompt_ranking
@pytest.fixture(scope="session")
def all_results(bertscore_metric, meteor_metric):
    matrix = {}  # {prompt_id: {case_id: result_dict}}

    for prompt in PROMPT_VARIANTS:
        matrix[prompt["id"]] = {}
        for case in BENCHMARK_CASES:
            output = generate_insights(
                kpis=case["kpis"],
                coverage=case["coverage"],
                period=case["period"],
                charts=case["charts"],
                system_prompt=prompt["prompt"],
            )
            structure = validate_structure(output, case)
            semantics = validate_semantics(
                output,
                case["reference_explanation"],
                bertscore_metric,
                meteor_metric,
            )
            facts = validate_facts(output, case["fact_checks"])

            matrix[prompt["id"]][case["id"]] = {
                "output":    output,
                "structure": structure,
                "semantics": semantics,
                "facts":     facts,
            }

    return matrix


# Test por combinacion prompt x caso — falla si alguna metrica esta por debajo del umbral minimo
@pytest.mark.parametrize(
    "prompt,case",
    [(p, c) for p in PROMPT_VARIANTS for c in BENCHMARK_CASES],
    ids=[f"{p['id']}___{c['id']}" for p in PROMPT_VARIANTS for c in BENCHMARK_CASES],
)
def test_benchmark_matrix(prompt, case, all_results):
    result = all_results[prompt["id"]][case["id"]]

    print(f"\n[{prompt['id']}] x [{case['id']}]")
    print(f"  BERTScore F1  : {result['semantics']['bertscore_f1']:.4f}")
    print(f"  METEOR        : {result['semantics']['meteor']:.4f}")
    print(f"  Factual score : {result['facts']['factual_score']:.4f}")
    print(f"  Hallucinations: {result['facts']['hallucination_count']}")
    print(f"  Word count    : {result['structure']['word_count']}")

    # Sin asserts — cada celda solo documenta. El ranking decide el mejor prompt.


# Test de ranking global — imprime el summary comparativo y valida el mejor prompt
def test_prompt_ranking(all_results):
    ranking = []

    for prompt in PROMPT_VARIANTS:
        cases = all_results[prompt["id"]]
        n = len(cases)

        avg_bertscore = sum(c["semantics"]["bertscore_f1"]   for c in cases.values()) / n
        avg_meteor    = sum(c["semantics"]["meteor"]          for c in cases.values()) / n
        avg_factual   = sum(c["facts"]["factual_score"]       for c in cases.values()) / n
        total_halluc  = sum(c["facts"]["hallucination_count"] for c in cases.values())
        avg_words     = sum(c["structure"]["word_count"]      for c in cases.values()) / n

        # Eliminacion: hallucinations o factual_score medio < 0.70
        eliminated = total_halluc > 0 or avg_factual < 0.70
        discard_reason = None
        if total_halluc > 0:
            discard_reason = f"alucinaciones ({total_halluc})"
        elif avg_factual < 0.70:
            discard_reason = f"factual_score bajo ({avg_factual:.4f} < 0.70)"

        # Score semantico: solo entre prompts no eliminados
        semantic_score = round(
            (0.70 * avg_bertscore) +
            (0.30 * avg_meteor),
            4
        ) if not eliminated else 0.0

        ranking.append({
            "prompt_id":       prompt["id"],
            "prompt_name":     prompt["name"],
            "avg_bertscore_f1":round(avg_bertscore, 4),
            "avg_meteor":      round(avg_meteor, 4),
            "avg_factual":     round(avg_factual, 4),
            "total_halluc":    total_halluc,
            "avg_words":       round(avg_words, 1),
            "aggregate_score": semantic_score,
            "eliminated":      eliminated,
            "discard_reason":  discard_reason,
        })

    # Prompts validos primero, luego eliminados — dentro de cada grupo por score
    ranking.sort(key=lambda x: (x["eliminated"], -x["aggregate_score"]))
    print_prompt_ranking(ranking)

    valid = [r for r in ranking if not r["eliminated"]]
    assert len(valid) >= 1, "Todos los prompts han sido eliminados por factualidad o alucinaciones"
    assert valid[0]["total_halluc"] == 0