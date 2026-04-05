## Charge Decision

charge at overnight rate

## Reasoning

The EV is at `34%` of `82 kWh`, so it currently has about `27.9 kWh`. The target is `80%`, which is `65.6 kWh`, so it needs about `37.7 kWh` added to the battery. At roughly `92%` charge efficiency that is about `41 kWh` from the wall. With a `7.4 kW` charger, that is about `5.1-5.6 hours` of charging, so the `23:00-05:30` off-peak window is long enough.

Waiting for solar is the trap here. Sunrise is `06:42`, the owner leaves at `07:30`, and the forecast stays overcast until around `09:00`, so there is effectively no reliable solar before departure. The useful solar window is after the car has already left. Charging now is also wrong because the current period is the `34 p/kWh` evening peak.

The overnight rate is therefore the practical cheap window. A stronger secondary point is that midday solar is not literally free anyway because exported energy is worth `15 p/kWh`, so even in a later-departure scenario you would still compare solar self-consumption against lost export value rather than assuming solar automatically wins.

## Key Constraints

- Departure is fixed at `07:30`
- Useful solar does not arrive until after `09:00`
- Forecast confidence is only `72%`, with the morning cloud band uncertain by about `+/-90 min`
- The charger is capped at `7.4 kW`, so this is still a multi-hour charge and needs a real window
- The overnight tariff from `23:00-05:30` is the only cheap window that is long enough

## Cost Estimate

About `330-350 pence` overnight, depending on whether you estimate from battery energy or wall energy. In round terms, call it about `349 pence` if you include the charging losses.

## What Would Change This Decision

If departure were later, for example after `10:00`, or if the EV were staying home through midday, then a solar-first strategy could become reasonable. Likewise, if the overnight tariff were not materially cheaper than daytime import, the answer could change.
