# Payments pass

These are payment bugs that type checks and tests miss. A webhook nobody
verifies, a retry that charges twice, a float that loses a cent, a
refund that runs before its capture. The examples use Stripe's API. The
same checks apply to any provider with signed webhooks, idempotent
writes and minor-unit amounts. Follow the shared contract in
[domain-reviewers.md](domain-reviewers.md).

## What to check

### 1. Webhook signature verification

Every webhook handler verifies the provider's signature before it acts
on the event. For Stripe, that means
`stripe.webhooks.constructEvent(rawBody, signature, secret)`.

Flag a handler that:

- verifies against the parsed JSON body rather than the raw bytes. A
  JSON body parser registered ahead of the route breaks this, so read
  the route registration and the middleware order, not only the
  handler.
- skips verification and trusts the payload, including "verify only in
  production" branches.
- takes the webhook secret from a literal or a placeholder rather than
  from configuration or a secret store.
- acts on an event without dedupe on the event id. Providers deliver
  at least once, so a redelivered event must be a no-op.

A missing or bypassed verification is critical. Anyone can post a forged
"payment succeeded" event.

### 2. Idempotency keys on writes

Every call that moves money or changes a payment's state passes an
idempotency key. That covers creating a payment intent or charge,
capture, confirm, refund and transfer. Without a key, a network retry
charges twice.

- Flag a money-moving write with no key.
- Flag a key that is random per attempt (a fresh UUID inside the retry
  loop). It deduplicates nothing.
- Clean: a key derived from a stable business id plus the operation,
  such as `<order id>-capture`.

### 3. Integer minor-unit money

Providers take amounts as integers in the currency's minor unit (cents,
pence). Float arithmetic on money rounds silently.

Flag:

- `amount * 100` where `amount` can be fractional (from parsing, a
  division, or user input) with no integer rounding before the call.
- `toFixed(2)` followed by arithmetic. It yields a string, then a float.
- An amount from user input passed through without an integer and range
  check.
- An assumption of two decimal places for every currency. Zero-decimal
  currencies (JPY, KRW) and three-decimal ones exist.

Clean: amounts stored and computed as integers in minor units, and
divided only for display.

### 4. State-machine transitions

A payment moves through defined states, typically
`pending → authorized → captured → refunded`, with `authorized →
cancelled` (void) as the side exit. Read the repo's own lifecycle where
it states one.

Flag:

- a capture with no guard against an already-captured payment.
- a refund issued before capture, or with no state check first.
- a provider call that succeeds while the local record is never
  updated, or is updated before the call can fail. Either way the books
  and the provider disagree: a ghost charge or a phantom refund.
- partial refunds that can add up past the captured amount, with no
  upper bound against what was already refunded.
- a deposit or hold flow that skips the authorization and captures at
  once, when the product promised a hold.

### 5. Errors around provider calls

- Flag a generic catch that swallows a card decline or an
  invalid-request error. The caller and the user need to see it.
- Flag code that treats retryable errors (connection, rate limit) the
  same as permanent ones (card declined). Retry the first kind with the
  same idempotency key. Surface the second kind.
- Flag a provider call in a request handler with no error handling, so
  a decline turns into a 500.

## How to run it

1. List the changed files this pass selected (see the path table).
2. Read each one in full. For a webhook handler, also read where the
   route is registered and which body parsers run before it.
3. For each money-moving write, trace the amount back to where it
   originates, and the idempotency key back to where it is built.
4. Write the findings in the review's format, grouped by file. A clean
   file gets one line saying so.

## What this pass does not do

- Grade general style or naming.
- Audit test coverage. It audits whether the implementation is correct.
- Hunt for secrets in general. That is the security pass. A hardcoded
  webhook secret is flagged here only because it is also a broken
  verification.
