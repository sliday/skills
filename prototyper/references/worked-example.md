# Worked example: supplier reorder draft

This example is fictional. It illustrates scope decisions; it contains no customer research or measured results.

A small café manager tracks low stock in a spreadsheet, then writes a supplier email. The proposed product creates a reorder draft.

Direction: “For a café manager preparing tomorrow's stock order, help them turn low-stock items into a supplier draft they can check. We need to learn whether reviewing the draft saves effort without hiding mistakes.”

A first prototype can test whether someone understands and completes the review. It cannot establish time savings until a person compares it with their existing workflow.

## One task

Start at a stock list. Select low-stock items, adjust quantities, review an order and copy a text draft. Stop before sending it.

Use synthetic records:

| Item | On hand | Target | Supplier | Unit |
|---|---:|---:|---|---|
| Oat milk | 3 | 12 | Harbour Supplies | cartons |
| Coffee beans | 2 | 6 | Harbour Supplies | kg |
| Cup lids | 20 | 100 | Unassigned | pieces |

Suggested quantities are 9 cartons, 4 kg and 80 lids. Show those calculations. Let the manager change them. Use fictional company details and no real contact address.

## States worth building

- No selected items: explain how to begin; do not create an empty order.
- Invalid quantity: reject zero, negative or non-numeric values beside the field.
- Missing supplier: flag cup lids and let the manager exclude them or select a synthetic supplier.
- Review: display quantities, units and supplier before copying.
- Copy failure: display selectable plain text so the task still finishes.
- Return to edit: preserve the selected items and changed quantities.

## Boundaries

Local calculations and editable state work. Persistence may use browser storage if available. Supplier lookup uses synthetic data. Copy uses the browser clipboard when supported, with a text fallback. Sending, inventory synchronization and payment remain absent. Label the final action “Copy draft”; do not show “Order sent”.

## Cuts

Skip login, stock forecasts, dashboards, supplier ratings and a mobile app. The task needs a stock list, review screen and copyable result. Build those before adding navigation.

## Feedback task

“Prepare a draft to restore oat milk and coffee beans to their target quantities. Do not order lids yet.” Observe whether the person excludes lids, notices the units and can edit a quantity. Ask what they expected before explaining the interface. Record observations as observations, not proof that cafés will buy the product.

## Handoff note

“Prototype covers one supplier draft. All stock data is synthetic; no messages or orders leave the browser. Test the copy fallback in the target browser. Next team decisions: source of inventory data, supplier identity and whether draft export belongs before direct sending.”
