# Anomaly Taxonomy (v1)

This document defines all valid anomaly types.
No anomaly should be recorded unless it fits one of these categories.

---

## A. Demand anomalies

### unexpected_peak
Demand is significantly higher than forecast or historical baseline.

### suppressed_demand
Demand is significantly lower than expected.

### prolonged_peak
Demand remains elevated longer than the historical norm.

### volatile_demand
Demand fluctuates rapidly within a short time window.

---

## B. Timing anomalies

### shifted_peak
Peak demand occurs earlier or later than usual.

### missing_peak
An expected peak does not occur.

---

## C. Signal mismatch anomalies

### transport_demand_mismatch
Transport signals and observed demand disagree.

### weather_demand_mismatch
Weather impact contradicts demand behaviour.

### event_demand_mismatch
A known event does not affect demand as expected.

---

## D. Crowd behaviour anomalies

### composition_shift
The type of people present changes unexpectedly.

### behavioural_change
How people behave changes without volume change.

---

## Severity levels
- low: noticeable but minor
- medium: operationally relevant
- high: materially impactful

---

## Confidence
Confidence reflects signal agreement, not certainty.
Range: 0.4 – 0.95
