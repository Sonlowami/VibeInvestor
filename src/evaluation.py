def compute_metrics(plan, findings, critique=None):
    print("[EVALUATION] Computing metrics...")

    metrics = {}

    # 1️⃣ Task completion
    metrics["task_completion"] = 1 if findings else 0

    # 2️⃣ Plan adherence (based on expected max companies)
    expected = plan.get("max_companies", 1)
    actual = len(findings) if findings else 0

    if expected > 0:
        adherence_ratio = min(actual, expected) / expected
        metrics["plan_adherence_score"] = round(adherence_ratio * 10)
    else:
        metrics["plan_adherence_score"] = 0

    # 3️⃣ Groundedness (structural completeness)
    if not findings:
        metrics["groundedness_score"] = 0
    else:
        required_fields = ["financials", "valuation_metrics"]

        valid = sum(
            1 for c in findings
            if all(field in c for field in required_fields)
        )

        metrics["groundedness_score"] = round(
            (valid / len(findings)) * 10
        )

    print("[EVALUATION OUTPUT]", metrics)

    return metrics


def apply_valuation_filters(findings):
    qualified = []

    for company in findings:
        try:
            pe = float(company["valuation_metrics"].get("pe_ratio", 999))
            ratio = float(company["financials"].get("assets_liabilities_ratio", 0))

            if pe < 20 and ratio > 1.5:
                qualified.append(company)

        except:
            continue

    return qualified
