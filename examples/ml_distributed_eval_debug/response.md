The first thing I would fix is the collator. `DataCollatorWithPadding` is the wrong choice for a `Seq2SeqTrainer` evaluation path, especially once you move to distributed generation-heavy eval. Replace it with `DataCollatorForSeq2Seq(tokenizer, model=model)`.

Second, make sure `predict_with_generate=True` is set in `Seq2SeqTrainingArguments`, otherwise the trainer can stay on the loss-oriented path instead of the generation-oriented evaluation path that `compute_metrics` usually expects for summarization metrics.

Third, if you still think metrics are disappearing after those fixes, verify that you are only looking for logs on the main process under DeepSpeed or DDP, because metric reporting can be rank-gated.

Why training still looks healthy: training loss is computed under teacher forcing, so the training path can continue to optimize normally even while the eval path is misconfigured.
