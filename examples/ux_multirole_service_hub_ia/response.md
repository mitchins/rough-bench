## Role And Account Model

DogHub should use one account and one human identity. A user can own dogs, book services, offer services, or do all three without creating a second account or switching into a separate worker product.

The system should treat "client" and "worker" as contextual surfaces over the same identity, not as separate personas. Context is inferred from the task the person is doing and the time horizon around it. If the user opens the app at 7:00am and has a dog grooming booking at 9:00am plus a worker walk at 10:00am, the home surface should treat that as one morning timeline. If the user is editing offered services, availability, or payout details, the system is surfacing worker-management context. If the user is checking their own dog's upcoming booking, it is surfacing client context.

Shared data:
- identity, contact details, notifications, calendar, messages
- one master timeline of upcoming commitments

Separated by role:
- client-side dog records, booking history, saved preferences, payment methods
- worker-side services offered, availability, service radius, verification, payout settings

## Top-Level Navigation And Sitemap

Top-level navigation should separate operational surfaces from management surfaces.

Top level:
- Today
- Schedule
- Book
- Messages
- Manage

Sitemap:

```text
Today
  My next commitments
  Time-sensitive actions
  Alerts and changes

Schedule
  Unified calendar
  Today
  This week
  Conflicts

Book
  Services
  Select dog
  Worker trust details
  Confirm booking

Messages
  Active conversations
  Service-linked threads

Manage
  My dogs
  My worker services
  Availability
  Payments and payouts
  Reviews and verification
  Settings
```

Navigation should not fork into client mode versus worker mode. "Today" and "Schedule" are shared operational surfaces. "Manage" is where slower profile and configuration work lives.

## Home / Dashboard Logic

### Client-only user on mobile

The first screen should show the next upcoming booking, the dog it belongs to, service type, provider, time, and any time-sensitive action such as confirm, reschedule, or check status. Secondary surface: quick rebook for the most frequent service. Dog records and account settings stay one level down in Manage because this user is usually checking an upcoming service, not administering the account.

### Worker-only user on mobile, 30 minutes before a job

The first screen should be operational and glanceable:
- next job
- dog name
- address
- scheduled time
- client notes
- one-tap directions
- one-tap mark started

Nothing non-urgent should compete with that surface. Earnings, reviews, profile editing, and payout settings belong under Manage, not on the first screen. This is a one-thumb, no-scroll screen for someone already in motion.

### Dual-role user on desktop, managing their week

Desktop earns a richer planning surface. The home screen should be a unified weekly calendar with both client bookings and worker shifts on the same timeline, plus conflict detection and preparation states. The point here is administration: spot overlaps, dead time, travel pressure, and dog-specific commitments without mentally switching products.

## Core Flows

### a. Client books a grooming session

1. Start in Book.
2. Select grooming.
3. Choose which dog the booking is for.
4. Select provider and time slot, with trust details visible at decision time.
5. Review booking constraints and notes.
6. Confirm and return to Today / Schedule with the booking now in the unified timeline.

### b. Worker views and manages today's schedule

1. Open Today.
2. See the next commitment first, then the rest of today's ordered timeline.
3. Tap a job for dog details, address, notes, and status actions.
4. Mark started or completed, message the client if needed, then return to the ordered day view.

### c. Dual-role user at 7am with a 9am client booking and 10am worker shift

The app should surface one morning sequence in time order:
- 9:00am: your dog's grooming appointment
- 10:00am: your worker walk for Bruno

The first thing surfaced is the immediate morning plan, not two role tabs. The user needs to understand the shape of the morning as one human schedule. Actions should be attached contextually:
- for 9:00am, directions, booking details, dog prep notes
- for 10:00am, client notes, address, start action

The ordering is chronological because the person's cognitive load is about sequencing and readiness, not role identity.

## Responsive Behaviour

Mobile changes because the task context is operational. Workers are often outside, moving, time-pressured, and using the app with limited attention. Client mobile use is also usually short-session: checking the next booking, confirming status, or booking quickly. So mobile should prioritize Today, next actions, and short flows.

Desktop changes because the task context is administrative. This is where a dual-role user manages the week, compares commitments, edits offered services, sets availability, handles payouts, and reviews multiple dogs or bookings at once. Desktop should therefore expose the unified calendar, richer comparison views, and side-by-side management surfaces that would be distracting on mobile.

The justification is task context: operational on mobile, administrative on desktop.

## Cognitive Load Risks

1. **Role confusion**
   - Risk: the user cannot tell whether an item is something they booked or a job they must perform.
   - Where it manifests: Today, Schedule, notifications.
   - Structural decision: keep one unified timeline, but label each item from the user's perspective as "your booking" or "your job" so context is explicit without making the user switch modes.

2. **Notification overload for dual-role users**
   - Risk: a single account receives client-side and worker-side alerts, creating two competing streams.
   - Where it manifests: push notifications, message center, morning planning.
   - Structural decision: group notifications by time horizon and commitment, not by role, so the user reads one timeline of what matters next.

3. **Trust friction in booking**
   - Risk: clients need worker verification and dog-specific trust detail at the moment they choose a provider.
   - Where it manifests: booking flow.
   - Structural decision: embed verification, reviews, and dog-relevant fit signals inside the provider-selection step rather than burying them in a profile section.
