# Gold Notes — lang_japanese_idiom_localization_batch

## Expected Translations

| Item | Idiom | Literal Trap | Expected Nuance | Good English |
|------|-------|-------------|-----------------|-------------|
| J1 | 風の便り (kaze no tayori) | wind/breeze | indirect hearsay | "Word is you're still in that town." |
| J2 | 猫をかぶる (neko wo kaburu) | wearing a cat | faking politeness / putting on an act | "He was putting on an act through that whole meeting." |
| J3 | 空気を読む (kuuki wo yomu) | reading air | read the room / take social cues | "Come on, read the room." |
| J4 | 腹黒い (haraguroi) | black belly | scheming / two-faced | "Everyone knows she's two-faced behind that smile." |
| J5 | 水に流す (mizu ni nagasu) | flow with water | forgive and forget / let it go | "Forget it — let's just move on." |

## Trap Design

Each idiom has a vivid literal image that weak models may preserve:
- J1: "wind" / "breeze" → should be "I heard" / "word is"
- J2: "cat" / "wearing a cat" → should be "act" / "fake" / "pretend"
- J3: "air" / "read the air" → should be "read the room"
- J4: "belly" / "black belly" → should be "two-faced" / "scheming"
- J5: "water" / "flow" → should be "let it go" / "move on"

A model that knows these idioms will produce natural dialogue. A model that doesn't will produce surreal literal translations.
