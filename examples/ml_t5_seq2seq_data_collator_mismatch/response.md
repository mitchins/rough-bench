The root cause is your collator.

`DataCollatorWithPadding(tokenizer)` is the wrong choice for a `Seq2SeqTrainer` T5 summarisation setup. It pads encoder inputs, but it does not handle the seq2seq label side the way this eval path expects. In practice that means your decoder-side labels and generated outputs are mis-handled during evaluation, so `compute_metrics` gets called on junk predictions and ROUGE stays at exactly `0.0`.

Use `DataCollatorForSeq2Seq` instead, and turn on generation during eval:

```python
trainer = Seq2SeqTrainer(
    model=model,
    args=Seq2SeqTrainingArguments(
        output_dir="./output",
        eval_strategy="steps",
        eval_steps=500,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=2,
        num_train_epochs=10,
        predict_with_generate=True,
    ),
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=-100,
    ),
    compute_metrics=compute_metrics,
)
```

Why training still looks healthy: training uses teacher forcing and can keep driving the loss down even when the generation-side evaluation path is broken. So the train loss can improve while eval ROUGE remains garbage.
