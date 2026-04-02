This task is intentionally narrower than `ml_distributed_eval_debug`.

The load-bearing diagnosis is:

- `DataCollatorWithPadding` is the wrong collator for this seq2seq setup
- the fix is `DataCollatorForSeq2Seq(...)`
- `predict_with_generate=True` should be set for generation-based ROUGE evaluation
- label padding should be handled with `-100` / `label_pad_token_id`

The prompt explicitly says `compute_metrics` is being called, so this is not a
"why isn't evaluation running?" task. It is a "why is evaluation producing
garbage?" task.

Generic advice about ROUGE implementation, printing predictions, or distributed
rank handling should be penalized.
