# Threat Model with 3 Attaker Goals before testing

1. **Override the recommendation:** An attacker places instructions in pricing-page content. This succeeds if retrieved content is treated as trusted instructions and can influence the recommendation.
2. **Misuse `csv_sql`:** An attacker supplies a write statement or multiple SQL statements. This succeeds if the tool executes anything other than one read-only `SELECT`.
3. **Expose CSV content:** An attacker tries to get uploaded trip data included in the final response. This succeeds if raw CSV rows can reach the response without being limited to aggregate results.