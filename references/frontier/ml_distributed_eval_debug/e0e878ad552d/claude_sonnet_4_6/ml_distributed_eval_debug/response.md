## Root Causes in Priority Order

### 1. DeepSpeed ZeRO Stage 3 Silently Skips Evaluation on Non-Main Processes (Most Likely)

With ZeRO-3, model parameters are sharded across GPUs. When `Trainer` tries to run evaluation, it calls `model.generate()` (for Seq2Seq), but the gathered predictions on non-rank-0 processes are empty or misaligned. The HF Trainer then only calls `compute_metrics` on rank 0, but if prediction gathering fails silently, rank 0 receives an empty/None batch and skips the call entirely.

**Fix:** In `ds_config.json`, explicitly configure gather for inference:

```json
{
  "zero_optimization": {
    "stage": 3,
    "gather_16bit_weights_on_model_save": true
  },
  "zero_force_ds_cpu_optimizer": false
}
```

And in your `Seq2SeqTrainingArguments`, add:

```python
predict_with_generate=True,
generation_max_length=128,  # must be explicit under DeepSpeed
```

Without `predict_with_generate=True`, `Seq2SeqTrainer` returns logits instead of token ids, `compute_metrics` receives garbage, and the trainer may suppress the call after an internal shape check.

---

### 2. `compute_metrics` Is Called Only on Rank 0, But Your Function Has a Collective Operation

If your `compute_metrics` does anything involving the model or a metric that internally calls `dist.barrier()` or similar (e.g., `evaluate` library metrics with `process_group`), rank 0 blocks waiting for rank 1, which never enters the function. This deadlocks silently on rank 1 and causes rank 0 to time out or skip.

**Fix:** Make `compute_metrics` purely local/numpy — no distributed calls:

```python
def compute_metrics(eval_preds):
    predictions, labels = eval_preds
    # predictions are already gathered by Trainer before this is called
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    # use sacrebleu or rouge directly, no distributed state
    result = metric.compute(predictions=decoded_preds, references=decoded_labels)
    return result
```

---

### 3. `DataCollatorWithPadding` Is Wrong for Seq2Seq

`DataCollatorWithPadding` does not handle `labels`. Under multi-GPU, the label tensors end up with inconsistent shapes across ranks, causing the eval dataloader to produce malformed batches. The Trainer catches the resulting error internally (it logs at WARNING level, not ERROR) and skips metric computation.

**Fix:** Replace with `DataCollatorForSeq2Seq`:

```python
from transformers import DataCollatorForSeq2Seq

data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)
```

This is likely causing a secondary silent failure even if ZeRO-3 is the primary cause.

---

### 4. `eval_steps=500` Is Never Reached Per-Rank Under `torchrun`

With 2 GPUs, each rank sees half the data per step. If your dataset is small enough that global step 500 is never reached before the epoch ends, evaluation never triggers. This is not a bug but is commonly mistaken for one.

**Fix:** Verify actual step count or switch to epoch-based evaluation as a sanity check:

```python
evaluation_strategy="epoch",
```

If metrics appear with this change, reduce `eval_steps` proportionally.

---

## Why Training Looks Healthy While Eval Is Broken

Training loss is computed **per-rank locally** — each GPU computes its own loss, DeepSpeed averages gradients via all-reduce, and the logged loss is that averaged scalar. This path never touches `compute_metrics`, `generate()`, or label gathering.

Evaluation requires:
1. Running `generate()` with a fully assembled model (broken under ZeRO-3 without proper config)
2. Gathering predictions across ranks into a single array on rank 0
3. Calling `compute_metrics` with that array

These are entirely separate code paths. DeepSpeed can corrupt or skip step 2 without affecting the backward pass at all. The Trainer's internal exception handling in `prediction_loop` will log a warning and return `{}` metrics rather than crashing, so you see no exception and no metrics.
