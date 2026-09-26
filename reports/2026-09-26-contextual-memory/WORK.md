# R31 component accounting, not interactive latency

Components measured in the staged study are summed for each algorithmic path; these are not measured interactive end-to-end latencies and include no queue/model-load/training/filesystem/unrecorded bookkeeping time. Native generation is counted once per path. The two seeds are separate alternatives, not an ensemble. Constant-trained and blind path sums omit verifier work unnecessary to those recipes, although the controlled study collected shared verifier records for every case. Branch paths include the joint embedding/contextual extraction actually measured; an embedding-only extractor could be cheaper and was not timed separately.

| Path | Mean recorded component sum (s) | P50 (s) | P95 (s) | Generated tokens / case | Backbone tokens processed / case | Required Jev calls / case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 0.561 | 0.547 | 0.631 | 12.5 | 303.0 | 0 |
| blind | 1.151 | 1.126 | 1.299 | 25.0 | 675.6 | 0 |
| embedding-structured/3101 | 1.787 | 1.771 | 1.915 | 24.6 | 978.1 | 1 |
| embedding-structured/3102 | 1.787 | 1.771 | 1.921 | 24.6 | 978.2 | 1 |
| embedding-scalar/3101 | 1.784 | 1.769 | 1.904 | 24.5 | 978.1 | 1 |
| embedding-scalar/3102 | 1.784 | 1.771 | 1.902 | 24.6 | 978.1 | 1 |
| embedding-constant/3101 | 1.288 | 1.285 | 1.395 | 24.6 | 978.1 | 0 |
| embedding-constant/3102 | 1.289 | 1.285 | 1.401 | 24.6 | 978.1 | 0 |
| contextual-structured/3101 | 1.784 | 1.774 | 1.903 | 24.5 | 978.1 | 1 |
| contextual-structured/3102 | 1.785 | 1.769 | 1.907 | 24.6 | 978.1 | 1 |
| contextual-scalar/3101 | 1.785 | 1.771 | 1.902 | 24.5 | 978.1 | 1 |
| contextual-scalar/3102 | 1.784 | 1.770 | 1.901 | 24.6 | 978.1 | 1 |
| contextual-constant/3101 | 1.288 | 1.288 | 1.392 | 24.6 | 978.1 | 0 |
| contextual-constant/3102 | 1.290 | 1.286 | 1.404 | 24.6 | 978.1 | 0 |
