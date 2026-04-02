## Assumptions and Constraints

- This is a single-shard, stateless API layer. No in-memory caches that would complicate migration.
- Firestore documents are simple: user (id, name, email, created_at, settings), account (id, user_id, plan_type, next_billing, settings).
- Settings objects are nested JSON in Firestore; in SQL they become `user_settings` and `account_settings` tables.
- The API runs on multiple stateless instances. A dual-read/dual-write adapter allows both backends to serve traffic during the transition.
- In-flight transactions are infrequent; we can afford a brief consistency window where reads may lag writes slightly.
- Live traffic is ~100 QPS average, so the cutover window can be small (minutes, not seconds).

## Phase 1: Data Layer Abstraction and Verification

Build a data access layer that decouples the API from Firestore. This allows a gradual cutover.

### Non-Goals (Phase 1)

- Cross-region availability or geo-failover
- Advanced metrics or cloud services integration
- Zero-downtime guarantee (we will accept a brief maintenance window for cutover)
- Snapshot restoration automation or recovery tooling

## Repo Layout

```
api/
  src/
    data/
      firestore_backend.py   # Current Firestore reader/writer
      postgres_backend.py    # New PostgreSQL reader/writer
      data_adapter.py        # Unified interface; routes reads/writes
      models.py              # User, Account, Settings data classes
    migrations/
      001_create_tables.sql  # Schema for PostgreSQL
      002_populate_from_firestore.py  # One-time data dump
    tests/
      test_data_adapter.py   # Dual-read/dual-write logic
      test_migration_consistency.py
  sql/
    schema.sql               # Final schema definition
```

## Phase 1 Milestones

### Milestone 1: Define Database Schema and Adapter Interface

**Database schema mapping:** Firestore nested objects map to normalized SQL tables.
- Write SQL schema for user, account, user_settings, account_settings
- Define the data_adapter interface with read_user, write_user, read_account, etc.
- Create firestore_backend and postgres_backend implementations
- Unit tests for each backend independently

### Milestone 2: Implement Dual-Read/Dual-Write Adapter
- Implement data_adapter to read from PostgreSQL first, fall back to Firestore if not found
- Implement dual-write: writes go to both backends
- Add conflict detection if reads diverge between backends
- Integration tests against both backends simultaneously

### Milestone 3: Migrate Data and Verify
- Run the one-time data dump from Firestore to PostgreSQL
- Verify row counts, key checksums, and nested-field mappings
- Run consistency audit: read_via_postgres == read_via_firestore for 100% of rows

### Milestone 4: Cutover and Rollback Harness
- Switch data_adapter to read-primary from PostgreSQL, with Firestore fallback
- Deploy to production with dual-write still active (safety net)
- Define clear go/no-go gates before cutting writes to Firestore
- Implement quick rollback: revert data_adapter to read-primary from Firestore, re-enable Firestore writes

## Deliverables

1. **data/data_adapter.py** – Unified interface that routes to both backends
2. **data/postgres_backend.py** – PostgreSQL read/write implementation
3. **sql/schema.sql** – Final normalized schema for users, accounts, and settings
4. **migrations/001_create_tables.sql** – Table creation DDL
5. **migrations/002_populate_from_firestore.py** – One-time data migration script
6. **tests/test_data_adapter.py** – Dual-read, dual-write, and fallback logic tests
7. **tests/test_migration_consistency.py** – Verify Firestore → PostgreSQL data integrity
8. **MIGRATION_RUNBOOK.md** – Step-by-step cutover procedure and rollback instructions

## Acceptance Criteria and Go/No-Go Gates

### Before Cutover (Go/No-Go 1)

- [ ] PostgreSQL schema created and all indexes in place
- [ ] Data dump completes without errors; row counts match Firestore
- [ ] Checksum audit passes: all user and account records are byte-identical after dump
- [ ] Nested settings objects correctly denormalized into separate tables
- [ ] All data_adapter tests pass; dual-read returns same result from both backends for 100% of rows
- [ ] All data_adapter tests pass with both backends in both orders (read Firestore first, read PostgreSQL first)

### After Cutover (Go/No-Go 2)

- [ ] API logs show reads are sourcing from PostgreSQL; fallback to Firestore is not happening
- [ ] Latency comparison: PostgreSQL reads ≤ 50ms avg (same as or better than Firestore)
- [ ] Error rate ≤ baseline (no increase in 5XX or data-layer exceptions)
- [ ] Writes to PostgreSQL succeed for 100% of requests over 1-hour production burn-in
- [ ] Firestore writes still succeed in parallel (dual-write safety net is working)
- [ ] Random spot checks: pull 10 user records from PostgreSQL, verify they are identical to manual Firestore queries

### Rollback Gate (if Go/No-Go 2 fails)

- [ ] Revert data_adapter to read-primary from Firestore
- [ ] Disable PostgreSQL writes
- [ ] Verify that API traffic normalizes and no errors occur
- [ ] Leave PostgreSQL populated and dual-write enabled for next attempt (data is preserved)

## Rollback Strategy

**Reversible at any stage:**

1. During Milestone 1–3: PostgreSQL contains only test data. Rollback is a DROP database and revert the code change.
2. After data dump (Go/No-Go 1): PostgreSQL is populated but not read from. Rollback is setting data_adapter to read-Firestore-only.
3. After cutover (post Go/No-Go 2): If latency, errors, or consistency issues emerge within 1 hour, flip data_adapter back to read-Firestore-primary. Firestore writes are still active, so no data loss. PostgreSQL stays populated as a warm standby.

**No step of the migration requires a restore from backup.**

## Summary

This is a bounded first phase: move data, prove the adapter works, cut reads over, and keep writes flowing to both systems until we are confident. Replication and deployment scope are later phases. The focus is on moving safely and reversibly.
