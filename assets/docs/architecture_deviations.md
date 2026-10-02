TaxiFare™ System Architecture Deviation Report

This document details the variations implemented during the Phase 1 development cycle compared to the original high-level conceptual flow.

1. Payment Integration Infrastructure

    Original Plan: Individual, direct API integrations with separate South African retail banks and standalone mobile wallet super-apps (MTN MoMo, Vodacom VodaPay).

    Implemented Deviation: Shifted to a unified payment orchestration layer using Electrum's Unified Payment Gateway API.

    Technical Rationale: Direct integration with every distinct banking entity introduces massive red tape and fragmented code maintenance. Electrum natively aggregates MTN MoMo, VodaPay, and major SA clearing banks into a single sandbox endpoint, drastically reducing backend complexity.

2. Micro-Architecture Edge Cases

    Original Plan: Simple HTTP request/response loops for handling user transactions.

    Implemented Deviation: Added explicit layers for Idempotency (using a PROCESSED_TRANSACTIONS memory cache tracking system) and Sliding-Window Rate Limiting (RATE_LIMIT_TRACKER) within notification.py.

    Technical Rationale: High-volume transit environments like South African taxi ranks suffer from unstable network connections. Without idempotency, a dropped connection retried by Electrum or the user would result in double-charging the commuter. Rate-limiting prevents system denial-of-service (DoS) during peak rush hours.

3. Telematics & Dashboard Layout Engine

    Original Plan: Grid-based HTML components to represent passenger seating states.

    Implemented Deviation: Transitioned to a precise, percentage-based pixel coordinate overlay mapping system positioned directly over an authentic vector blueprint graphic (14 Seater.svg).

    Technical Rationale: Standard HTML grid blocks failed to map the spatial ergonomics of a real Toyota Quantum minibus. To ensure the driver instantly recognizes which seat turned green at a glance, the interface layout must mirror physical vehicle seating splits (e.g., Row 3's folding door seat configuration).