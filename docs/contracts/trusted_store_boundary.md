# Contract: Trusted Store Boundary

Doc: `docs/contracts/trusted_store_boundary.md`  
Date: 2026-02-18  
Status: Active (v0 prototype)

## Purpose

Define mutation rules for trusted stores (`POL`, `ID`, `CAPS`).

## Store Interface

Trusted stores are exposed through:

- `src/ree_openclaw/stores/trusted.py`

Available stores:

- policy store (`POL`)
- identity store (`ID`)
- capability store (`CAPS`)

## Write Rules

- Any write to `POL`/`ID`/`CAPS` must pass typed-boundary source checks.
- Untrusted sources (for example `USER`, `MODEL_INTERNAL`) are blocked.
- Trusted internal sources may write through explicit store APIs.

## Read Rules

- Reads are key-based and do not bypass typed-boundary write protections.
- Absence returns `None`; no implicit store creation from reads.
