# Kings Cross Seasonal Demand Intelligence

**Urban demand volatility detection & seasonal pattern learning**
*Kings Cross / Coal Drops Yard · London*

---

## Status: Seasonal Data Collection (Paused Development)

This project is currently in **data-collection mode**.

From **22 December 2025 to mid-January 2026**, no new features, UI changes, or anomaly logic are being added.

### Purpose of the pause

Capture **clean seasonal demand volatility signals** under a **frozen model**, allowing post-period analysis without confounding changes.

### Dataset lock

* **Model & anomaly logic frozen:** 22 Dec 2025 → 7 Jan 2026
* **All insights derive from an unchanged seasonal model**
* Any findings are attributable to **real-world conditions**, not code iteration

This pause is intentional and foundational for downstream insight quality.

---

## Overview

Kings Cross Seasonal Demand Intelligence is an **experimental urban analytics system** designed to:

* Detect **demand volatility** in high-footfall districts
* Explain *why* deviations occur using observable public signals
* Learn **seasonal demand behaviour** without requiring private data

The system focuses on **district-level dynamics**, not individual venue performance.

It is built to support:

* Property & asset managers
* Urban operators
* Place-making teams
* PropTech & analytics partners
* Consultants analysing seasonal or event-driven demand risk

---

## What This Is (and Is Not)

### This *is*:

* A **signal-based demand intelligence engine**
* Explainable, taxonomy-driven anomaly detection
* Infrastructure-aware (transport, weather, events)
* Designed for **replicability across districts and cities**

### This is *not*:

* A POS system
* A sales forecast tool
* A marketing optimisation platform
* A restaurant operations dashboard

The system deliberately avoids private or sensitive data sources.

---

## Core Signals

The pipeline ingests **public, explainable signals only**:

* **Weather** (temperature, conditions)
* **Transport status** (TfL disruptions & pressure)
* **Local events** (Eventbrite)
* **Venue density & proximity** (Google Places)
* **Time-of-day & seasonal context**

These are fused into a single **district busyness signal** and compared against seasonal baselines.

---

## Anomaly Taxonomy (v1)

All deviations are classified using a fixed taxonomy:

### Demand anomalies

* `unexpected_peak`
* `suppressed_demand`
* `prolonged_peak`
* `volatile_demand`

### Timing anomalies

* `shifted_peak`
* `missing_peak`

### Signal mismatch anomalies

* `transport_demand_mismatch`
* `weather_demand_mismatch`
* `event_demand_mismatch`

Each anomaly includes:

* Severity (`low`, `medium`, `high`)
* Confidence (signal agreement, not certainty)
* Persistence (`transient`, `emerging`, `established`)
* Human-readable explanation
* Contributing drivers

---

## Seasonal Learning Phase (Dec 2025 – Jan 2026)

This period was chosen intentionally due to:

* Christmas trading volatility
* Pre-NYE build-up
* NYE spike
* Post-holiday normalization

During this phase the system collected:

* Continuous hourly observations
* Anomaly persistence patterns
* Driver co-occurrence statistics
* Confidence stability metrics

No tuning or optimisation occurred during collection.

---

## Outputs

The system produces:

* `kingscross_dashboard.json`
  → Current state, context, venues, cluster pressure

* `forecast.json`
  → Short-term baseline demand projection

* `history/kingscross_history.json`
  → Long-running demand signal history

* `anomalies.json`
  → Fully classified seasonal deviations

* `observations.json`
  → Raw signal truth-log for learning & audit

* `seasonal_insights_2025.json`
  → Aggregated post-season analysis (counts, patterns, interpretations)

---

## Explainability First

Every insight is:

* Traceable to observable signals
* Logged with drivers
* Interpretable by non-technical stakeholders

Confidence reflects **signal agreement**, not ground truth certainty.

This makes the system suitable for:

* Risk discussions
* Strategic planning
* Post-event analysis
* Investor or board-level reporting

---

## Why Kings Cross?

Kings Cross was selected as a **validation district** because it combines:

* Transport complexity
* Mixed-use footfall
* Event-driven volatility
* Strong seasonal effects

The architecture is **not Kings Cross–specific** and is designed for reuse.

---

## Roadmap (Locked During Pause)

### Completed

* Seasonal anomaly engine (v1)
* Persistence tracking
* Explainable drivers
* Frozen seasonal dataset

### Next (post-pause)

* Seasonal insight synthesis (Jan report)
* District-to-district replication
* Decision signal abstraction
* Product narrative & buyer positioning

No roadmap items will be executed until the seasonal dataset is fully analysed.

---

## Data Ethics & Scope

* No personal data
* No payment data
* No device tracking
* No private venue data

All signals are public, aggregated, and explainable.

---

## Project Intent

This project explores whether **urban demand volatility itself** is a valuable signal — independent of sales, marketing, or venue-level optimisation.

The goal is to determine whether **explainable seasonal demand intelligence** can support better decision-making at the district and asset level.

---
