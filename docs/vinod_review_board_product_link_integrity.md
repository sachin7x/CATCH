# Vinod Review Board: CATCH-style verifier-first product link integrity

## Goal

Apply CATCH's verifier-first principle to the Vinod Review Board deployment:

https://vinod-ridhi-amazon-review-20vnvv8gj-sachin7xs-projects.vercel.app/

This is an evidence-backed audit/repair specification, not a claim that changes have already shipped. A rendered card or generic Amazon URL is not proof of product identity.

## Current observed state

- Vercel production deployment is READY and returned HTTP 200 through the authenticated Vercel fetch integration.
- The deployed artifact is a single static `src/index.html`.
- It renders 50 benchmark cards.
- Card artwork is CSS gradients and emoji rather than actual product photographs.
- Clicking a card opens a modal; its “Open Amazon US” action always points to `https://www.amazon.com/stores/Ridhi`, not a product-specific detail page.
- The deployed records are name/category/price tuples; no verified per-product ASIN or URL mapping is implemented.
- The generic store CTA fails the requirement for exact product-specific destinations.
- Recent Vercel runtime-error lookup returned no errors for the selected time range. This does not prove UI/link correctness.

## CATCH truth invariant

Visible output is not correctness. A product card passes only when an independent verifier confirms the full chain:

`internal_product_id → source_product → correct_reference_image → exact_variant → verified_Amazon_US_ASIN → canonical Amazon.com product URL`

Keep Amazon India benchmark evidence separate from Amazon.com destinations. Ridhi images must be labelled research/reference images and must not be represented as FabricsG commercial photography.

## Required implementation

1. Establish a source of truth for the 50 product records and image assets, retaining provenance.
2. Create a typed product/link manifest with product ID, source URL, category, color, size, design/variant, image URLs/hashes, candidate ASIN, canonical Amazon.com URL, matching evidence, verification status, and last-checked timestamp.
3. Replace emoji/gradient-only visuals with the corresponding actual product photos when authorized source assets can be found. Preserve source URLs and label imagery as Ridhi/reference research material.
4. Replace the generic Amazon store CTA with a product-specific “View on Amazon.com” link only when that exact product/variation mapping has been verified.
5. When an exact match cannot be proven, display a non-clickable “Amazon.com US listing not verified” status. Never substitute a generic search page/store page, Amazon.in URL, or inferred ASIN.
6. Add independent integrity checks for malformed URLs, redirects, inaccessible URLs, Amazon.in contamination, ASIN/product mismatch, duplicate mappings, missing/broken images, and source/deployed-data drift.
7. Treat rate-limiting, bot blocking, access denied, and similar checks as `ACCESS_BLOCKED / NOT_VERIFIED`, not as a confirmed broken link.
8. Generate `AMAZON_LINK_AUDIT.csv`, `BROKEN_LINK_REPORT.csv`, `BROKEN_IMAGE_REPORT.csv`, and `VERCEL_SOURCE_DRIFT_REPORT.csv`.
9. Add tests with deliberate mutations: wrong ASIN, swapped colors, wrong image, missing image, generic store URL, Amazon.in URL, broken URL, duplicate ASIN, missing metadata.
10. Deploy only after checks pass. Then fetch production and re-verify; do not claim deployment or tests succeeded without evidence.

## Acceptance criteria

- Each visible product card has a clear identity and corresponding product photo.
- Only exact, independently verified Amazon.com product URLs are clickable.
- Generic store/home/search URLs never pass as a specific product link.
- Amazon.in is never presented as an Amazon USA purchase destination.
- Unverified matches are visible, non-clickable statuses.
- Image/ASIN associations are checked against variant-specific metadata.
- Audit counters reconcile checked/pass/fail/blocked/not-verified totals.
- Any high-severity mismatch keeps the overall status BLOCKED.

## Scope boundary

This issue concerns the deployed Vinod Review Board and its Amazon benchmark links. It does not authorize Amazon listing creation, GTIN purchase, inventory production, or use of Ridhi photographs as FabricsG commercial listing photos.