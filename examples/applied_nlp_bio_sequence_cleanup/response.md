## Corrections

| item_id | corrected_tags | error_type | note |
| --- | --- | --- | --- |
| B1 | B-PER O O | illegal_start | The entity cannot start with I-PER. |
| B2 | B-PER I-PER I-PER O | missing_continuation | The name span needs to keep going. |
| B3 | B-ORG I-ORG O O O | truncated_span | Northwind Labs is one organization. |
| B4 | O B-PER I-PER O | boundary_extension | The title span was cut short. |
| B5 | B-PER O B-PER O B-LOC | missing_B_after_O | Arlen needs a new B-PER start. |
| B6 | O B-ORG O B-LOC O | clean | This sequence is already valid. |

## Error Audit

The batch is mostly boundary repair, with one already-valid row that should be preserved unchanged.
