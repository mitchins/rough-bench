The load-bearing bug is the BOS versus EOS mismatch.

Strong answers should say some version of:

- training uses teacher-forced prefixes that start from `BOS`
- inference initializes generation with `EOS`
- the decoder has not been trained to condition on `EOS` as the first prefix token
- this corrupts generation from step 1 and should be ranked `critical`
- inference also never switches the model into eval mode, so dropout and BatchNorm behave incorrectly
- fixes are:
  - initialize with `BOS`
  - call `model.eval()` or `self.eval()`
  - ideally use `torch.no_grad()` during generation

Weak answers usually fail by:

- missing the BOS/EOS issue entirely
- noticing only eval mode
- calling beam search versus greedy decoding a mismatch
- listing generic inference hygiene without explaining what the decoder was actually trained on
