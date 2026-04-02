## Blight Spread Mechanic

The season lasts 6 rounds. At the end of each round, reveal 2 cards from a shared **Blight Deck** and resolve them in order.

The Blight Deck has four card families:

- **Directional cards**: North Wind, South Wind, East Wind, West Wind. Blight spreads only orthogonally in the named direction from every infected tile.
- **Surge cards**: Rot Surge, Slow Creep. These change intensity. Rot Surge makes each infected tile spread two steps instead of one. Slow Creep limits all spread to one adjacent tile of the active player's choice.
- **Weather cards**: Wet Week, Dry Crack. Wet Week raises every infected tile's Blight Level by 1 before spread. Dry Crack prevents spread through Root tiles this round.
- **Containment cards**: Burn Line, Quarantine Break. Burn Line stops spread through any cleared tile. Quarantine Break ignores one barrier or firewall effect this round.

Each infected tile has a **Blight Level** from 1 to 3. Level 1 weakens yield. Level 2 ruins vulnerable crops. Level 3 kills the crop and leaves a **Ruined** tile. Ruined tiles do not score and do not spread further until a player spends an action to clear them into Fallow.

Spread procedure:

1. Raise or lower intensity if a Weather or Surge card says so.
2. For each infected tile, spread one orthogonal step in the drawn direction unless a card overrides it.
3. The receiving tile gains Blight Level equal to the source tile minus 1, minimum 1.
4. Vine can block spread if mature. Cleared Fallow blocks spread unless Quarantine Break is in effect.

This is runnable because direction, rate, acceleration, and stopping conditions are explicit.

## Crop Vulnerability And Yield Profiles

- **Grain**: low yield, high resistance. Grain scores 2 per healthy tile, 1 at Blight Level 1, and still harvests at Level 2. Grain is the best border buffer.
- **Root**: high yield, high vulnerability. Root scores 5 per healthy tile but is ruined at Blight Level 2. Root is the greed crop.
- **Vine**: medium yield, slow timing, spatial utility. Vine scores 3 per tile, only matures after 2 rounds, and only scores if in a contiguous set of 2 or more. Mature Vine acts as a firewall: blight can hit the Vine tile, but it does not spread through it that round.

Grain is the survival crop, Root is the explosive crop, and Vine is the positional crop. None is dominant in all states because one maximizes stability, one maximizes payout, and one manipulates the board.

## Hand And Action Economy

Players draft 40-card decks from a shared pool. Card families are:

- planting cards
- treatment / clearance cards
- market / trade cards
- manipulation cards that interact with the Blight Deck
- harvest timing cards

Each player gets **2 actions per turn** plus one free harvest if a crop is mature.

Core actions are:

- plant
- harvest
- clear a ruined tile
- play a card
- initiate a trade

The main decision each turn is whether to invest in yield now, spend tempo on containment, or manipulate the board state so a later spread hurts someone else more than you.

## Trade And Negotiation Mechanic

After actions, the active player may open one **Market Window** with exactly one opponent.

Players may trade:

- one card for one card
- a crop token for a card
- a binding payment now for a non-binding future promise

The interesting part is not equal exchange. It is **leverage** and **asymmetric information**. I can see that you have two Root tiles about to mature and that a Wet Week would destroy them. You know that I know. That makes my spare Clearance card expensive. Players can also offer unenforceable promises such as "I will not push spread through our shared edge next round" or "I will not contest the border-majority bonus this season." Those promises matter because trade is happening around visible board desperation, not hidden perfect information.

If a player reneges on a future promise, nothing in the rules stops them, but that creates retaliation and embargo behavior in later Market Windows.

## Scoring

End-game scoring has two components:

1. **Absolute harvest points**: score all harvested crops normally.
   - Grain: 2
   - Root: 5
   - Vine: 3 per tile in a mature contiguous set
2. **Relative scoring bonuses**:
   - **Healthiest Frontier**: 6 points to the player with the most healthy border tiles at season end.
   - **Best Diversified Harvest**: 4 points to the player with the highest total across at least two crop types.

This creates tension. Absolute harvest pushes players toward Root greed. Relative scoring pushes them toward denying neighbors, protecting border tiles, and sometimes taking a smaller but safer harvest. A player does not just need points; they need to finish ahead of the table on at least one comparative axis.

## Stress Test Your Own Design

The most likely **degenerate strategy** is **weaponize blight through the border**.

Round by round, the player drafts Grain buffers, one or two Blight Deck manipulation cards, and just enough Root to stay relevant on absolute harvest points. They plant Grain on border tiles adjacent to opponents and Root deeper in their own grid. Then they spend actions to steer the Blight Deck toward directional cards that push infection through shared edges. Because Grain tolerates Level 1 and even Level 2 better than Root, the player survives modestly while the neighbors lose their greed crops. The relative scoring component makes this stronger: they do not need the highest raw yield, only to ruin enough opposing border tiles to win Healthiest Frontier or stay ahead of a crippled table.

The design does **not fully close** this door by default.

I close most of it with two costs:

- any card that deliberately changes spread direction also gives the source tile **self-blight** of +1
- player-caused spread can never count toward Healthiest Frontier on that border this round

That makes offensive blight real but expensive. The exploit line is still viable, which I want, but it is no longer the automatic best line every season. Fully closing it would require removing Blight Deck manipulation or removing the relative border bonus, and that would flatten the game into defensive farming with much less interaction.
