# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users confirmed by the user: fishers and fish traders checking prices and demand while planning where and when to sell. Other known users are harbour operations teams, harbour committees, and auction operators.

## Product Purpose

KALASTUS presents fishing-harbour market and operational information in one workspace so fishers and traders can review prices, buyer demand, landings, available resources, announcements, and alerts when planning sales.

## Positioning

The frontend combines a harbour-level operations view with the existing Harbour OS API. Its usefulness depends on the data that API and its configured database actually provide.

## Operating Context

Users review a selected harbour or all returned harbours, then scan current market observations, buyer demand, and related operational records. The dashboard should be readable at desktop, laptop, tablet, and mobile widths.

## Capabilities and Constraints

- The existing backend is Flask with Flask-SQLAlchemy and its existing SQLite-compatible database configuration.
- The added frontend is React, TypeScript, and Vite; the repository's existing Vue frontend remains separate.
- The current API supports harbours, dashboard summaries, market prices, landings, buyers and demand, ice, cold storage, announcements, and alerts.
- The current API does not provide vessel/AIS tracking, berth slots, weather, sea state, or historical price series. The interface must show these as unavailable rather than fabricate values.
- Loading, error, and empty states are required. Backend-marked demonstration data must remain identified as demonstration data.
- The locally fetched `origin/harbour-os` branch is at commit `43da0f1`; it contains no tracked database file. Do not seed demo records as if they were live operational data.

## Brand Commitments

- The user requests the displayed project name `KALASTUS`.
- The user requests a classic, restrained maritime identity: deep navy, muted ocean blue, restrained sea-green, and warm light neutrals.
- Preserve the existing ocean-wave header and animated fishing boat exactly, changing only its project-name text.
- Preserve existing navigation and backend/API behavior while refining the dashboard's visual presentation.

## Evidence on Hand

The source repository documents the backend API contract. No persistent harbour database file was present in the fetched branch or local backend folder during this task. Its seed fixtures are fictional demonstration data and must not be presented as live facts.

## Product Principles

- Show the source of operational information honestly.
- Keep unavailable or missing data explicit.
- Make routine harbour operations quick to scan.
- Preserve the existing working backend and frontend behavior.

## Accessibility & Inclusion

Keep the dashboard responsive, readable, and usable with its existing loading, error, and empty states.
