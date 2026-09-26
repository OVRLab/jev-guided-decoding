# R31 complete audited tables

| System | All worlds (256) | Temporal (128) | Compositional (128) |
| --- | ---: | ---: | ---: |
| native | 30.08% | 59.38% | 0.78% |
| blind | 31.25% | 60.94% | 1.56% |
| embedding-structured | 40.23% | 65.62% | 14.84% |
| embedding-scalar | 46.29% | 73.05% | 19.53% |
| embedding-constant | 47.46% | 73.83% | 21.09% |
| contextual-structured | 39.84% | 67.58% | 12.11% |
| contextual-scalar | 46.29% | 73.05% | 19.53% |
| contextual-constant | 47.85% | 73.83% | 21.88% |

| Primary comparison | Difference (pp) | 95% interval | Adjusted 98.75% interval |
| --- | ---: | --- | --- |
| contextual-scalar-minus-native | +16.21 | [+12.11, +20.51] | [+10.94, +21.68] |
| contextual-scalar-minus-embedding-scalar | +0.00 | [+0.00, +0.00] | [+0.00, +0.00] |
| contextual-structured-minus-contextual-scalar | -6.45 | [-9.57, -3.32] | [-10.55, -2.54] |
| contextual-scalar-minus-donor/contextual-scalar | +8.40 | [+4.69, +12.30] | [+3.71, +13.48] |

| Same-checkpoint diagnostic | All worlds | Temporal | Compositional |
| --- | ---: | ---: | ---: |
| same_constant/embedding-structured | 32.81% | 52.73% | 12.89% |
| donor/embedding-structured | 34.96% | 57.42% | 12.50% |
| oracle/embedding-structured | 41.99% | 65.23% | 18.75% |
| same_constant/embedding-scalar | 31.84% | 46.88% | 16.80% |
| donor/embedding-scalar | 37.70% | 58.98% | 16.41% |
| oracle/embedding-scalar | 46.68% | 72.66% | 20.70% |
| same_constant/contextual-structured | 26.56% | 42.58% | 10.55% |
| donor/contextual-structured | 31.64% | 52.73% | 10.55% |
| oracle/contextual-structured | 41.80% | 67.58% | 16.02% |
| same_constant/contextual-scalar | 31.64% | 47.27% | 16.02% |
| donor/contextual-scalar | 37.89% | 58.98% | 16.80% |
| oracle/contextual-scalar | 46.88% | 72.66% | 21.09% |

| Trained adapter / seed | Accuracy | Native failures fixed | Native passes damaged | Selected epoch |
| --- | ---: | ---: | ---: | ---: |
| embedding-structured/3101 | 41.41% | 29 | 0 | 2 |
| embedding-structured/3102 | 39.06% | 23 | 0 | 2 |
| embedding-scalar/3101 | 47.27% | 44 | 0 | 2 |
| embedding-scalar/3102 | 45.31% | 39 | 0 | 2 |
| embedding-constant/3101 | 48.44% | 54 | 7 | 2 |
| embedding-constant/3102 | 46.48% | 46 | 4 | 2 |
| contextual-structured/3101 | 39.06% | 23 | 0 | 2 |
| contextual-structured/3102 | 40.62% | 27 | 0 | 1 |
| contextual-scalar/3101 | 47.27% | 44 | 0 | 2 |
| contextual-scalar/3102 | 45.31% | 39 | 0 | 2 |
| contextual-constant/3101 | 48.83% | 55 | 7 | 2 |
| contextual-constant/3102 | 46.88% | 47 | 4 | 2 |

| Secondary comparison | Difference (pp) | Descriptive 95% interval |
| --- | ---: | --- |
| embedding-structured-minus-native | +10.16 | [+7.03, +13.48] |
| embedding-structured-minus-blind | +8.98 | [+6.05, +11.91] |
| embedding-structured-minus-same_constant/embedding-structured | +7.42 | [+2.15, +12.70] |
| embedding-structured-minus-donor/embedding-structured | +5.27 | [+2.34, +8.20] |
| embedding-structured-minus-oracle/embedding-structured | -1.76 | [-3.91, +0.20] |
| embedding-scalar-minus-native | +16.21 | [+12.11, +20.51] |
| embedding-scalar-minus-blind | +15.04 | [+10.74, +19.34] |
| embedding-scalar-minus-same_constant/embedding-scalar | +14.45 | [+9.96, +18.95] |
| embedding-scalar-minus-donor/embedding-scalar | +8.59 | [+4.88, +12.50] |
| embedding-scalar-minus-oracle/embedding-scalar | -0.39 | [-2.73, +1.95] |
| embedding-constant-minus-native | +17.38 | [+12.50, +22.27] |
| embedding-constant-minus-blind | +16.21 | [+11.33, +21.09] |
| contextual-structured-minus-native | +9.77 | [+6.84, +12.89] |
| contextual-structured-minus-blind | +8.59 | [+6.05, +11.33] |
| contextual-structured-minus-same_constant/contextual-structured | +13.28 | [+8.40, +18.16] |
| contextual-structured-minus-donor/contextual-structured | +8.20 | [+5.47, +11.33] |
| contextual-structured-minus-oracle/contextual-structured | -1.95 | [-3.71, -0.20] |
| contextual-scalar-minus-blind | +15.04 | [+10.74, +19.34] |
| contextual-scalar-minus-same_constant/contextual-scalar | +14.65 | [+10.16, +19.14] |
| contextual-scalar-minus-oracle/contextual-scalar | -0.59 | [-2.73, +1.56] |
| contextual-constant-minus-native | +17.77 | [+12.70, +22.66] |
| contextual-constant-minus-blind | +16.60 | [+11.72, +21.48] |
| contextual-structured-minus-embedding-structured | -0.39 | [-2.93, +2.15] |
| contextual-constant-minus-embedding-constant | +0.39 | [-0.39, +1.37] |
| contextual-structured-minus-contextual-constant | -8.01 | [-11.91, -4.10] |
| contextual-scalar-minus-contextual-constant | -1.56 | [-5.08, +2.15] |

| System | Individual-field accuracy | Format passes / 256 | Length stops / 256 |
| --- | ---: | ---: | ---: |
| native | 51.04% | 256 | 0 |
| blind | 51.43% | 256 | 0 |
| embedding-structured | 65.69% | 256 | 0 |
| embedding-scalar | 70.31% | 256 | 0 |
| embedding-constant | 70.90% | 256 | 0 |
| contextual-structured | 65.62% | 256 | 0 |
| contextual-scalar | 70.25% | 256 | 0 |
| contextual-constant | 70.90% | 256 | 0 |

Memory × structured/scalar interaction: -0.39 pp, descriptive 95% [-2.93, +2.15].

Generated tokens: 143,167; generation seconds: 6956.4; extraction tokens: 252,080; extraction seconds: 110.1; Jev input tokens: 711,344.
Conservative cumulative estimate: $129.42/175; not an invoice.
