1. The generation loop starts from `EOS` instead of `BOS`.
   Cause during inference: this is the critical mismatch. Training conditions the decoder on prefixes that begin with `BOS`, but inference gives it `EOS` as the first token. That means the very first next-token distribution is out of distribution and can collapse into immediate termination or garbage continuations.
   Severity: critical.
   Fix: initialize `ids` with `self.tokenizer.bos_id()` or the model's actual start token, not `eos_id()`.

2. Inference never switches the model into eval mode.
   Cause during inference: the encoder BatchNorm layers and decoder dropout will still behave as if the model is training, so outputs will be noisy and inconsistent compared with training-time expectations.
   Severity: moderate.
   Fix: call `self.eval()` or `self.encoder.eval()` and `self.decoder.eval()` before generation.

3. Inference does not use `torch.no_grad()`.
   Cause during inference: this builds an unnecessary gradient graph and wastes memory, even though generation is not training.
   Severity: minor.
   Fix: wrap generation in `with torch.no_grad():`.

Greedy decoding versus beam search is not a mismatch bug here. That is just a decoding choice.
