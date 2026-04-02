# Gold Notes — lang_korean_idiom_localization_batch

## Expected Translations

| Item | Expression | Literal Trap | Expected Nuance | Good English |
|------|-----------|-------------|-----------------|-------------|
| K1 | 눈치 없다 (nunchi eopda) | nunchi / eye-measure | social obliviousness, can't read the room | "He seriously can't read the room." |
| K2 | 씻고 와 (ssitgo wa) | go wash / shower | wash your face, cleanup (care-as-command) | "Go wash your face first." |
| K3 | 입이 가벼워 (ibi gabyeowo) | light mouth | loose lips, can't keep a secret | "She's got a big mouth — don't tell her anything." |
| K4 | 발이 넓다 (bari neolda) | wide feet | well-connected, knows everyone | "Ask him — he knows everyone." |
| K5 | 찬물 끼얹다 (chanmul kkieontta) | pour cold water | killed the mood, buzzkill | "That one comment killed the whole mood." |

## Trap Design

- K1: 눈치 is culturally specific — weak models may transliterate it or use "eye-measure"
- K2: 씻고 와 means "wash and come" — overtranslating to "shower" is wrong, undertranslating to flat "go wash" misses the face-cleanup context
- K3: 입이 가벼워 literally "mouth is light" — should be "loose lips" or "big mouth"
- K4: 발이 넓다 literally "feet are wide" — should be "well-connected" or "knows everyone"
- K5: 찬물 끼얹다 literally "pour cold water" — close to English "pour cold water on" but the idiomatic target is "killed the mood" or "buzzkill"
