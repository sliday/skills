---
name: consumer-billing-refunds
version: 1.0.0
description: Use when identifying charges or requesting refunds.
author: Sliday
license: MIT
triggers:
  - "what is this charge"
  - "find whom to contact for a refund"
  - "cancel this subscription"
  - "write a chargeback warning"
  - "I was charged for a plan I do not use"
tools:
  - terminal
  - browser
  - email search/read/draft tools
mutating: true
---

# Consumer Billing Refunds

## Contract
Identify the merchant from primary evidence, verify the current refund route and deadline, cancel renewal separately, and produce or create a firm factual refund request with a bounded card-dispute escalation. Never overstate merchant identity, policy eligibility, fraud, or authorization status.

## 1. Triage urgency

1. Establish the current date/time with a live tool.
2. Determine the approximate charge date, amount/currency, plan term, and whether the user recognizes the merchant.
3. Treat short refund windows as urgent. If the user appears to be inside one, prepare the request immediately rather than spending time on exhaustive background research.

## 2. Identify the merchant

Search the original source first: receipt, bank descriptor, app-store history, or connected email. For email, use multiple independent angles:

- exact and nearby amounts (`$200.00`, `199.99`),
- billing language (`annual`, `renewal`, `receipt`, `invoice`, `Pro`),
- a tight date window around the charge,
- merchant or card descriptor once surfaced.

Widen the date range only when needed to locate older renewal reminders or account mail.

### Evidence levels

- **Confirmed:** receipt/invoice, bank transaction, app-store purchase, or explicit user confirmation.
- **Strong candidate:** matching renewal reminder tied to the right account and timing.
- **Hypothesis only:** matching plan price, marketing email, or product page.

Do not say “confirmed” from price matching alone. State the evidence level and ask for the missing bank descriptor only if it materially changes the action.

## 3. Extract transaction facts

From the strongest source, capture:

- merchant and billing entity,
- charged account email,
- amount and currency,
- charge date/time,
- annual/monthly term,
- invoice/order/transaction ID,
- payment rail or card last four digits,
- cancellation link,
- support/refund route.

Avoid exposing complete card numbers, home addresses, or irrelevant private receipt details.

## 4. Verify policy and contact route

Use the merchant’s official help, billing, or legal source and record:

- refund deadline,
- eligibility conditions,
- required contact channel,
- whether web, Apple, and Google purchases use different routes,
- cancellation instructions.

If direct access is blocked, use indexed snippets or secondary sources only as provisional evidence and label them. Prefer a user-provided official URL over historical chat context. Refresh time-sensitive policy details before relying on them.

## 5. Cancel and request refund separately

Cancellation usually stops future renewal; it does not necessarily refund the current charge. Tell the user to do both:

1. disable automatic renewal through the merchant or storefront;
2. submit the refund request through the correct route;
3. retain the receipt, sent request, cancellation confirmation, and policy evidence.

## 6. Draft the refund request

Return or create:

- **To / support route**
- **From / associated account**
- **Subject**
- **Copy-ready body**
- **Separate cancellation path**
- **Evidence-retention note**

The body should contain only established facts or facts supplied by the user. Ask for cancellation, full refund to the original method, and written confirmation.

### Chargeback language

Use a card dispute as bounded escalation, not as the opening accusation:

> Please process the cancellation and full refund and confirm both actions. If this timely request is refused or receives no response within three business days, I will dispute the charge with my card issuer and provide this correspondence as evidence.

Never call the charge fraudulent or unauthorized unless the user explicitly says it was unauthorized. A calm policy-based demand is usually stronger than hostility.

## 7. Mailbox action and verification

Before promising to create a draft, inspect mailbox access:

- with write/triage access, create the draft and read back recipients, subject, and body; report its ID;
- with read-only access, provide copy-ready text and plainly state why direct draft creation was unavailable.

Do not claim an email was sent unless a send action was explicitly requested and verified.

## Anti-patterns

- Guessing the merchant from a round amount and presenting it as fact.
- Treating a product-description page as transaction evidence.
- Quoting a refund window from memory without checking freshness.
- Threatening chargeback before making a normal refund request.
- Claiming unauthorized use to strengthen a case.
- Assuming cancellation automatically creates a refund.
- Promising to place a draft before checking mailbox permissions.
