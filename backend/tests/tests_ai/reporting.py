def print_case_report(case: dict, result: dict) -> None:
    structure = result["structure"]
    semantics = result["semantics"]
    facts = result["facts"]

    print("\n" + "=" * 80)
    print(f"CASE: {case['id']} — {case['name']}")
    print("=" * 80)
    print(f"Final score         : {result['final_score']:.4f}")
    print(f"Structure score     : {structure['structure_score']:.4f}")
    print(f"Word count          : {structure['word_count']}")
    print(f"Required ratio      : {structure['required_ratio']:.4f}")
    print(f"Found numbers       : {structure['found_numbers']}")
    print(f"BERTScore Precision : {semantics['bertscore_precision']:.4f}")
    print(f"BERTScore Recall    : {semantics['bertscore_recall']:.4f}")
    print(f"BERTScore F1        : {semantics['bertscore_f1']:.4f}")
    print(f"METEOR              : {semantics['meteor']:.4f}")
    print(f"Factual score       : {facts['factual_score']:.4f}")
    print(f"Hallucinations      : {facts['hallucination_count']}")
    if structure["errors"]:
        print(f"Structure errors    : {structure['errors']}")
    if facts["failed_checks"]:
        print(f"Failed fact checks  : {facts['failed_checks']}")
    print("=" * 80)


def compute_summary(results: list[dict]) -> dict:
    n = len(results) or 1

    avg_final_score = sum(r["final_score"] for r in results) / n
    avg_structure_score = sum(r["structure"]["structure_score"] for r in results) / n
    avg_bertscore_f1 = sum(r["semantics"]["bertscore_f1"] for r in results) / n
    avg_meteor = sum(r["semantics"]["meteor"] for r in results) / n
    avg_factual_score = sum(r["facts"]["factual_score"] for r in results) / n

    min_final_score = min(r["final_score"] for r in results)
    min_bertscore_f1 = min(r["semantics"]["bertscore_f1"] for r in results)
    min_factual_score = min(r["facts"]["factual_score"] for r in results)

    total_hallucinations = sum(r["facts"]["hallucination_count"] for r in results)

    return {
        "cases": len(results),
        "avg_final_score": round(avg_final_score, 4),
        "avg_structure_score": round(avg_structure_score, 4),
        "avg_bertscore_f1": round(avg_bertscore_f1, 4),
        "avg_meteor": round(avg_meteor, 4),
        "avg_factual_score": round(avg_factual_score, 4),
        "min_final_score": round(min_final_score, 4),
        "min_bertscore_f1": round(min_bertscore_f1, 4),
        "min_factual_score": round(min_factual_score, 4),
        "total_hallucinations": total_hallucinations,
    }


def print_global_summary(summary: dict) -> None:
    print("\n" + "#" * 80)
    print("GLOBAL BENCHMARK SUMMARY")
    print("#" * 80)
    print(f"Cases                : {summary['cases']}")
    print(f"Avg final score      : {summary['avg_final_score']:.4f}")
    print(f"Avg structure score  : {summary['avg_structure_score']:.4f}")
    print(f"Avg BERTScore F1     : {summary['avg_bertscore_f1']:.4f}")
    print(f"Avg METEOR           : {summary['avg_meteor']:.4f}")
    print(f"Avg factual score    : {summary['avg_factual_score']:.4f}")
    print(f"Min final score      : {summary['min_final_score']:.4f}")
    print(f"Min BERTScore F1     : {summary['min_bertscore_f1']:.4f}")
    print(f"Min factual score    : {summary['min_factual_score']:.4f}")
    print(f"Total hallucinations : {summary['total_hallucinations']}")
    print("#" * 80)

def print_judge_report(judge_result: dict) -> None:
    if not judge_result.get("available"):
        print("LLM Judge          : no disponible")
        return
    if "error" in judge_result:
        print(f"LLM Judge error    : {judge_result['error']}")
        return

    scores = judge_result.get("scores", {})
    reasoning = judge_result.get("reasoning", {})
    print(f"Judge avg score     : {judge_result['avg_score']:.2f}/5.00  (normalizado: {judge_result['normalized_score']:.4f})")
    print(f"  Clarity           : {scores.get('clarity', '-')}/5  — {reasoning.get('clarity', '')}")
    print(f"  Actionability     : {scores.get('actionability', '-')}/5  — {reasoning.get('actionability', '')}")
    print(f"  Data fidelity     : {scores.get('data_fidelity', '-')}/5  — {reasoning.get('data_fidelity', '')}")
    print(f"  Tone              : {scores.get('tone', '-')}/5  — {reasoning.get('tone', '')}")
    print(f"Judge passed        : {judge_result.get('passed')}")


def print_prompt_ranking(ranking: list[dict]) -> None:
    print("\n" + "#" * 80)
    print("PROMPT ENGINEERING — RANKING COMPARATIVO")
    print("#" * 80)
    print(f"{'Rank':<5} {'Prompt':<38} {'BERTScore':>10} {'METEOR':>8} {'Factual':>8} {'Halluc':>7} {'Words':>7} {'Score':>8} {'Status'}")
    print("-" * 80)
    valid_rank = 1
    for r in ranking:
        if r["eliminated"]:
            rank_label = "  —  "
            status = f"ELIMINADO ({r['discard_reason']})"
        else:
            rank_label = f"{valid_rank:<5}"
            status = "OK"
            valid_rank += 1
        print(
            f"{rank_label} {r['prompt_name']:<38} "
            f"{r['avg_bertscore_f1']:>10.4f} "
            f"{r['avg_meteor']:>8.4f} "
            f"{r['avg_factual']:>8.4f} "
            f"{r['total_halluc']:>7} "
            f"{r['avg_words']:>7.0f} "
            f"{r['aggregate_score']:>8.4f}  {status}"
        )
    print("#" * 80)
    valid = [r for r in ranking if not r["eliminated"]]
    if valid:
        best = valid[0]
        print(f"PROMPT SELECCIONADO: {best['prompt_id']} — {best['prompt_name']}")
        print(f"  BERTScore F1: {best['avg_bertscore_f1']:.4f} | METEOR: {best['avg_meteor']:.4f}")
    else:
        print("NINGÚN PROMPT SUPERA LOS FILTROS DE CALIDAD")
    print(f"Criterio: eliminacion si hallucinations > 0 o factual_score < 0.70")
    print(f"Seleccion: 70% BERTScore F1 + 30% METEOR entre prompts validos")
    print("#" * 80)