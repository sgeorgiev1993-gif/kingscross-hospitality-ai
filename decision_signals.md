# Decision Signals (v1)

These signals convert raw anomalies into actionable intelligence.

---

## Volatility Regime Alert
Indicates unstable demand conditions where short-term forecasting
accuracy is reduced.

Trigger:
- Repeated volatile_demand anomalies
- Persistence ≥ emerging

Action:
- Reduce forecast reliance
- Increase operational flexibility

---

## Sustained Demand Pressure
Indicates prolonged elevated demand beyond normal baselines.

Trigger:
- prolonged_peak anomalies
- Persistence ≥ emerging

Action:
- Treat as temporary baseline shift
- Adjust staffing and supply assumptions

---

## Forecast Reliability Drop
Indicates disagreement between demand drivers
(weather, transport, events).

Trigger:
- Volatility + driver mismatch
- Confidence dispersion increase

Action:
- Switch to conservative decision mode
