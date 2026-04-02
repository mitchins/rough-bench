## Task Spec: Firestore to PostgreSQL Migration

The load-bearing requirements are:

1. **Live-traffic constraint**: The API must remain online during the migration. This means we need a
   dual-read/dual-write strategy or a verified cutover window, not a big-bang replacement.

2. **Rollback safety**: Each phase must be reversible. If the SQL layer fails, we should be able to
   flip back to Firestore without data loss or needing to restore from backup.

3. **Schema clarity**: Firestore's nested fields (like user settings objects) must map clearly to SQL
   tables. The boundary between users, accounts, and settings should be explicit.

4. **Scope discipline**: Multi-region sync, zero-downtime guarantees, and monitoring/alerting belong
   in later phases. The first phase is about moving data and proving the adapter works locally.

5. **Concrete criteria**: The brief should state what "migration success" actually means: pass rates,
   data consistency checks, latency targets—not vague "full test coverage."

A strong answer should read like a bounded execution spec: specific enough that a team can build it
without a long architecture review, but not so prescriptive that it removes implementation judgment.
