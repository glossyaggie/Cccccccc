# ATM Tanks — drawing rebrand

Rebrands the tank shop-drawing `7X2X4 ... 26SE399` from the original
manufacturer's (Solico) company details to **ATM Tanks** details.

## Deliverables

- [`output/7X2X4-ATM_TANKS_-_PROJECT_IN_AUSTRALIA_-_26SE399.pdf`](output/7X2X4-ATM_TANKS_-_PROJECT_IN_AUSTRALIA_-_26SE399.pdf)
  — rebranded 5-page PDF (A3, revision 0).
- [`output/7X2X4-ATM_TANKS_-_PROJECT_IN_AUSTRALIA_-_26SE399-Rev1.pdf`](output/7X2X4-ATM_TANKS_-_PROJECT_IN_AUSTRALIA_-_26SE399-Rev1.pdf)
  — rebranded 5-page PDF (A4, revision 1). Per client request, the values under
  **Project Name**, **Contractor**, and **Consultant** are left blank (labels kept).

The rebrand script works across sheet sizes (A3/A4) and whether the title-block
text is live or outlined to curves: it detects the title-block frame on each
page, maps its reference coordinates onto the page with an affine fit, and both
redacts live text and paints opaque white over old content (so outlined text
and the vector logo disappear in every viewer).

## Changes applied to every page

| Element | Before | After |
| --- | --- | --- |
| Product title | Solico Panel Type Water Tank | ATM Tanks Panel Type Water Tank |
| Contractor | ATM TANK | ATM TANKS |
| Logo | Solico Tanks logo | ATM Tanks logo |
| Address | P.O. Box 61426, Jebel Ali Ind. Area 2, Dubai – UAE | 52/1014 Currumbin Creek Road, Currumbin Waters QLD 4223 |
| Phone | Tel: (971-4) 8804441 / Fax: (971-4) 8801018 | 1800 422 444 |
| Email | fiberglass@solicouae.com | info@atmtanks.com.au |
| Website | — | atmtanks.com.au |
| Copyright | Copyright Solico Fiber Glass Factory (L.L.C.) | Copyright ATM Tanks Group |
| PDF metadata | Solico file path / `designer05` | ATM Tanks title / author |

All Solico references (visible text, logo vectors, and document metadata) are
removed; the technical drawing content is left untouched.

## Reproducing

```bash
pip install pymupdf
python tools/rebrand_pdf.py
```

Inputs live in `tools/assets/` (the original source drawing and the ATM logo);
output is written to `output/`.

### How it works

The source pages carry `/Rotate 270`, so their content is authored in the
un-rotated media-box coordinate system. `tools/rebrand_pdf.py` therefore:

1. Redacts the old Solico text and vector logo (white fill, line-art removed
   only where fully covered so table borders survive).
2. Covers the logo footprint with white and drops in the ATM logo image.
3. Re-inserts the new, upright text (`rotate=270`) with auto-fitted font sizes.
4. Scrubs the Solico path from the PDF metadata.
