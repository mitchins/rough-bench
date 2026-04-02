The task is intentionally narrow. The load-bearing diagnosis is that `DataCollatorWithPadding` is the wrong collator for a seq2seq evaluation path, and the answer should replace it with `DataCollatorForSeq2Seq`.

A strong answer should also mention `predict_with_generate=True`, explain the label-padding or `-100` masking detail, and explain why training loss can still look healthy while evaluation is broken. A secondary distributed note about rank-0 or main-process metric logging is useful, but it is not the primary root cause.

Ordering matters. A response that does not put the collator diagnosis at or near the top should be penalized even if it eventually mentions the right fix later.

This task should punish generic distributed-debugging checklists that never name the seq2seq collator problem.
