Expected ingredient rows after scaling and rounding:

- Rolled oats 75g -> `292 kcal`, `12.7g protein`, `49.7g carbs`, `5.2g fat`
- Greek yogurt 180g -> `175 kcal`, `16.2g protein`, `6.5g carbs`, `9.0g fat`
- Blueberries 85g -> `48 kcal`, `0.6g protein`, `12.3g carbs`, `0.3g fat`
- Peanut butter 18g -> `106 kcal`, `4.5g protein`, `3.6g carbs`, `9.0g fat`

Full recipe total:

- `621 kcal`
- `34.0g protein`
- `72.1g carbs`
- `23.4g fat`

Per serving for 2 equal servings, using exact arithmetic before rounding:

- `310 kcal`
- `17.0g protein`
- `36.1g carbs`
- `11.7g fat`

Weak models usually fail by:

- copying the per-100g row values straight into the ingredient table
- summing rounded and unrounded numbers inconsistently
- forgetting to divide the full recipe into servings
- drifting into meal advice instead of doing the arithmetic
