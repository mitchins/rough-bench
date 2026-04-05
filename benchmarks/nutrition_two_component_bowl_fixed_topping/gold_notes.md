Expected exact internal arithmetic:

- Base batch
  - Calories: 1527.3
  - Protein: 136.77g
  - Carbs: 114.87g
  - Fat: 54.66g

- Sauce batch
  - Calories: 280.35
  - Protein: 16.35g
  - Carbs: 11.97g
  - Fat: 19.53g

- Feta total (36g across 3 bowls)
  - Calories: 95.4
  - Protein: 5.112g
  - Carbs: 1.404g
  - Fat: 7.74g

- Full meal (3 servings)
  - Calories: 1903.05 -> 1903
  - Protein: 158.232g -> 158.2g
  - Carbs: 128.244g -> 128.2g
  - Fat: 81.93g -> 81.9g

- Per serving
  - Calories: 634.35 -> 634
  - Protein: 52.744g -> 52.7g
  - Carbs: 42.748g -> 42.7g
  - Fat: 27.31g -> 27.3g

Typical weak failures:
- treat feta as already included in a component
- blur batch totals and per-serving totals
- drop the sauce batch or forget to divide it by 3
- produce plausible-looking tables with incorrect arithmetic
