# Frontier reference cache

- Task: `ml_distributed_eval_debug`
- Task hash: `f57cd1817935`
- GPT-5.4 mini xhigh note: official OpenAI Responses API run returned `status=incomplete` with `reason=max_output_tokens`; all 3000 output tokens were consumed as reasoning and no visible answer was emitted. The cached response is intentionally blank because that is what the model/API returned for this prompt under this configuration.
- Claude Sonnet 4.6 note: response was reused locally after the rubric/order tweak because the prompt did not change; only the scoring did.
