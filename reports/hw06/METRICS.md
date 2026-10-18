# HW06 Metrics

## Short-term window comparison

Each mean is the five probe turns for that window, added together and divided by 5.

Each probe answer is scored from 1 to 5 using the rubric created in memory_probes.yaml. The probe quality is the average.

| Setting | Mean prompt tokens | Mean latency (ms) | Probe quality (1-5) |
|---|---:|---:|---:|
| 4 | 265.0 | 3311.86 | 4.2 |
| 12 | 281.4 | 2672.72 | 4.4 |
| 30 | 310.8 | 2645.72 | 4.2 |
| 12 with eviction | 329.0 | 4031.50 | 4.2 |

Scores for the five questions, in yaml order:

- SHORT_TERM_N = 4: 4, 4, 3, 5, 5
- SHORT_TERM_N = 12: 4, 4, 4, 5, 5
- SHORT_TERM_N = 30: 3, 3, 5, 5, 5
- 12 with eviction: 4, 4, 5, 5, 3

Refer to the memory_probes.yaml file to find the rubric.

## Memory cost

Price is $1 per million input tokens and $5 per million output tokens. The estimate is 10,000 conversations of 30 turns

The mean of completion tokens: 
- SHORT_TERM_N=4: 41.0
- SHORT_TERM_N=12: 32.8
- SHORT_TERM_N=30 29.6
- SHORT_TERM_N=12 with eviction: 33.6.

Cost was calculated by:
(mean prompt tokens × 30 × 10,000 / 1,000,000 × $1) + (mean completion tokens × 30 × 10,000 / 1,000,000 × $5).

This gives us:
| Setting | Cost for 10,000 conversations |
|---|---:|
| SHORT_TERM_N = 4 | $141.00 |
| SHORT_TERM_N = 12 | $133.62 |
| SHORT_TERM_N = 30 | $137.64 |
| 12 with eviction | $149.10 |

The best setting is SHORT_TERM_N = 12, because it costs the lowest, whereas the worst value is SHORT_TERM_12 with eviction, as the cost is highest.