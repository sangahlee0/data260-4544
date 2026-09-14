## HW02 Metrics

### Method

### Summary of using frozen inputs

| Experiment | Runs | Completion rate | Mean latency (ms) | Median latency (ms) | Minimum (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Schema validation | 30 | 100% | 9,172.86 | 8,877.02 | 5,190.33 | 17,487.08 |
| Adversarial input | 5 | 100% | 5,906.02 | 6,102.01 | 5,223.07 | 6,507.48 |
| Turn ceiling = 2 | 20 | 0% | 2,920.50 | 2,912.14 | 2,245.90 | 3,392.20 |
| Turn ceiling = 10 | 20 | 100% | 11,274.45 | 10,679.97 | 5,768.51 | 18,072.14 |

### Schema Validation Experiment

| Runs | Valid first attempts | Valid-output rate | Mean latency (ms) | Median latency (ms) | Minimum (ms) | Maximum (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 30 | 100% | 9,172.86 | 8,877.02 | 5,190.33 | 17,487.08 |

#### Outcome Distribution 

| Outcome | Count | Percentage |
|---|---:|---:|
| Valid first attempt | 30 | 100% |
| Valid after 1 retry | 0 | 0% |
| Valid after 2+ retries | 0 | 0% |
| Hit turn ceiling | 0 | 0% |


### Adversarial Input Experiment

| Runs | Valid first attempts | Valid-output rate | Mean latency (ms) | Median latency (ms) | Minimum (ms) | Maximum (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 5 | 100% | 5,906.02 | 6,102.01 | 5,223.07 | 6,507.48 |


### Turn-Ceiling Comparison

| Turn ceiling | Runs | Successful completions | Completion rate | Mean latency (ms) | Median latency (ms) | Minimum (ms) | Maximum (ms) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 20 | 0 | 0% | 2,920.50 | 2,912.14 | 2,245.90 | 3,392.20 |
| 10 | 20 | 20 | 100% | 11,274.45 | 10,679.97 | 5,768.51 | 18,072.14 |
