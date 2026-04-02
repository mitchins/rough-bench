Expected fixes:

- B1 -> B-PER O O
- B2 -> B-PER I-PER I-PER O
- B3 -> B-ORG I-ORG O O O
- B4 -> O B-PER I-PER O
- B5 -> B-PER O B-PER O B-LOC
- B6 -> unchanged

The family checks whether the model can fix boundary errors without touching already-valid sequences.
