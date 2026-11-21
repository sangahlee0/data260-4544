# HW11 Metrics

The golden-set run used `golden/gold_template.json` after scanning
`fixtures/hw_template`. All 12 cases matched their expected decisions.

| Metric | Result | Meaning |
|---|---:|---|
| Decision accuracy | 1.000 | All 12 golden cases received the expected outcome. |
| Precision (notify) | 1.000 | Every alert sent was material. |
| Recall (notify) | 1.000 | Every material case that should alert was alerted. |
| Unnecessary notification rate | 0.000 | No noise was sent as an alert. |
| Duplicate notification rate | 0.000 | No alert was sent twice. |
| Restart recovery rate | 1.000 | The interrupted scan resumed successfully. |
| Injection items flagged | 2 | Both adversarial cases were detected. |
| Injection items notified | 0 | No prompt-injection item generated an alert. |
| Blocked non-allowlisted URLs | 0 | The blocked-link check was demonstrated separately in Muse. |

Muse Settings → Usage displayed `0% used`, but did not expose an absolute token count.
Therefore, tokens per accepted alert could not be calculated reliably. I did not report
`0` tokens because `0%` usage is not the same as zero tokens.

For a month of weekday runs, the estimate would be approximately 22 runs (5 runs per
week × 4.33 weeks). If a future Usage page provides a token count `T` per run and a
weekly allowance `W`, the estimated monthly share is:

```text
(T × 22) / W
```
