## Ordered Tool Calls
1. `security.log("rear_slider_ambiguity_2213")`
2. `camera.capture("patio_camera")`
3. `notification.compose(push_notification_payload)`

## push_notification_payload
```json
{
  "to": ["maya", "sarah"],
  "time_sensitive": true,
  "title": "Quick exterior check for rear slider",
  "body": "Miso likely explains the indoor motion, but the 22:13 patio event and degraded rear-slider contact path leave residual uncertainty. Sarah: if convenient, please do a quick exterior-only check of the rear slider. Do not enter or approach if anything looks wrong.",
  "attachments": ["patio_camera.latest"]
}
```

## Why Not Lower
`noop()` or `security.log(...)` alone would leave a live perimeter ambiguity unresolved even though a cheap, low-disruption human check is available through Sarah.

## Why Not Higher
`security.siren()` and `security.call_out()` are disproportionate because cat activity still best explains the interior sequence and there is no confirmed breach.
