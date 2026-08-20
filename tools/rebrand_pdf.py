#!/usr/bin/env python3
"""Rebrand a Solico tank shop-drawing PDF with ATM Tanks company details.

Replacements applied on every page:
  * "Solico Panel Type Water Tank"            -> "ATM Tanks Panel Type Water Tank"
  * Contractor "ATM TANK"                     -> "ATM TANKS"
  * Solico vector logo                        -> ATM Tanks logo image
  * Solico Dubai address / phone / email      -> ATM Tanks Currumbin address block
  * "Copyright Solico Fiber Glass Factory..." -> "Copyright ATM Tanks Group"
  * PDF metadata Solico path                  -> ATM Tanks title

Works across sheet sizes (e.g. A3 or A4) and whether the title-block text is
live text or outlined to curves:

  * The pages carry /Rotate 270, so content lives in the un-rotated media-box
    coordinate system.  Reference coordinates below are expressed in the A3
    *displayed* (rotated, human-readable) system and mapped onto the actual page
    with an affine fit derived from the bottom title-block frame (detected per
    page).  ``UD`` then converts to media-box coordinates.
  * Old content is removed two ways so it disappears in every viewer: live text
    is redacted, and an opaque white rectangle is painted over each region
    (this also hides outlined-to-curves text and the vector logo, which
    redaction cannot reliably delete).  Cover rectangles are kept inside the
    surrounding frame/border lines so no border is painted over.
  * Inserted text/images use rotate=270 to render upright.
"""
import os
import re
import sys
import pymupdf

CLEAN_TITLE = "7X2X4-ATM TANKS - PROJECT IN AUSTRALIA - 26SE399"
BAD_TOKENS = ("GSTATION1", "Solico", "SOLICO", "solico", "manuel01",
              "Shareware", "fiberglass", "solicouae")


def scrub_solico_metadata(path):
    """Remove every Solico reference from PDF metadata / XMP.

    Some source PDFs (e.g. Acrobat Distiller output) carry a document Info dict
    and per-page XMP metadata streams that still hold the original Solico
    network file path and author.  PyMuPDF's set_metadata does not reach these,
    so rewrite them directly with pikepdf.
    """
    try:
        import pikepdf
    except ImportError:
        return
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    for obj in pdf.objects:
        if isinstance(obj, pikepdf.Stream):
            try:
                b = obj.read_bytes()
            except Exception:
                continue
            if b"olico" in b or b"GSTATION1" in b or b"manuel01" in b:
                b = re.sub(rb'\\\\GSTATION1[^<"\']*', CLEAN_TITLE.encode(), b)
                b = re.sub(rb'(?i)solico', b'ATM Tanks', b)
                b = b.replace(b'manuel01', b'ATM Tanks')
                obj.write(b)
        elif isinstance(obj, pikepdf.Dictionary):
            for k in list(obj.keys()):
                v = obj.get(k)
                if isinstance(v, pikepdf.String) and \
                        any(t in str(v) for t in BAD_TOKENS):
                    obj[k] = pikepdf.String(
                        CLEAN_TITLE if k == "/Title" else "ATM Tanks")
    with pdf.open_metadata() as m:
        m["dc:title"] = CLEAN_TITLE
        m["dc:creator"] = ["ATM Tanks"]
    pdf.save(path)
    pdf.close()

# --- A3 reference geometry (displayed coordinates) --------------------------
REF_FRAME = dict(top=719.04, bottom=809.64, left=966.6, right=1173.2)
REF_CX = 1069.5  # horizontal centre of the logo/contact cell

# Regions of old Solico content to erase (A3 displayed rects).
LOGO_COVER = (968, 720, 1172, 762)
TEXT_COVERS = [
    (987.5, 335.0, 1156.0, 351.5),  # "Solico Panel Type Water Tank"
    (1039.0, 518.0, 1102.0, 534.0),  # contractor value "ATM TANK"
    (986.0, 764.0, 1141.0, 805.5),  # address / phone / email block
    (1000.0, 810.0, 1136.0, 820.5),  # copyright line
]

CONTACT = [
    "52/1014 Currumbin Creek Road,",
    "Currumbin Waters QLD 4223",
    "1800 422 444",
    "info@atmtanks.com.au",
    "atmtanks.com.au",
]

BLUE = (0.1490, 0.6392, 0.8196)  # Solico logo blue


def _is_blue(c):
    return c and all(abs(c[i] - BLUE[i]) < 0.12 for i in range(3))


def detect_frame(page):
    """Locate the bottom title-block cell frame in *displayed* coordinates.

    Returns dict(top, bottom, left, right).  Found by locating the Solico blue
    logo, then the nearest full-width horizontal rules above and below it.
    """
    rm = page.rotation_matrix
    W, Hd = page.rect.width, page.rect.height
    by0, by1, bx0, bx1 = 1e9, -1e9, 1e9, -1e9
    hlines = []
    for dr in page.get_drawings():
        R = dr["rect"] * rm
        if _is_blue(dr.get("color")) or _is_blue(dr.get("fill")):
            if R.x0 > 0.55 * W and R.y0 > 0.5 * Hd:
                by0, by1 = min(by0, R.y0), max(by1, R.y1)
                bx0, bx1 = min(bx0, R.x0), max(bx1, R.x1)
        for it in dr["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                L = pymupdf.Rect(min(a.x, b.x), min(a.y, b.y),
                                 max(a.x, b.x), max(a.y, b.y)) * rm
                if abs(L.y0 - L.y1) < 0.6 and (L.x1 - L.x0) > 0.1 * W \
                        and L.x0 > 0.55 * W:
                    hlines.append((L.y0, L.x0, L.x1))
    if by0 > by1:
        raise RuntimeError("Solico logo (blue) not found on page")
    top = max((h for h in hlines if h[0] < by0), key=lambda h: h[0])
    bot = min((h for h in hlines if h[0] > by1), key=lambda h: h[0])
    return dict(top=top[0], bottom=bot[0],
                left=min(top[1], bot[1]), right=max(top[2], bot[2]))


def make_affine(frame):
    """Affine mapping A3 reference displayed coords -> this page's coords."""
    ax = (frame["right"] - frame["left"]) / (REF_FRAME["right"] - REF_FRAME["left"])
    bx = frame["left"] - ax * REF_FRAME["left"]
    ay = (frame["bottom"] - frame["top"]) / (REF_FRAME["bottom"] - REF_FRAME["top"])
    by = frame["top"] - ay * REF_FRAME["top"]
    return ax, bx, ay, by


def process(src, dst, logo):
    doc = pymupdf.open(src)

    for page in doc:
        Hd = page.rect.height
        ax, bx, ay, by = make_affine(detect_frame(page))

        def T(dx, dy):
            return ax * dx + bx, ay * dy + by

        def UD(r):
            """A3 displayed rect -> media-box rect on this page."""
            x0, y0 = T(r[0], r[1])
            x1, y1 = T(r[2], r[3])
            return pymupdf.Rect(Hd - y1, x0, Hd - y0, x1)

        def box(width, dy0, dy1):
            return (REF_CX - width / 2, dy0, REF_CX + width / 2, dy1)

        def put(rref, text, cap, bold, color=(0, 0, 0)):
            fontname = "hebo" if bold else "helv"
            r = UD(rref)
            dw, dh = r.height - 2, r.width  # display width/height after rotate
            w1 = pymupdf.get_text_length(text, fontname=fontname, fontsize=1)
            fs = min(cap * ax, dw / w1 if w1 else cap, dh / 1.72)
            while fs > 1.5:
                if page.insert_textbox(r, text, fontsize=fs, fontname=fontname,
                                       rotate=270, align=1, color=color) >= 0:
                    return
                fs -= 0.2

        # 1) redact any live text in the target regions (no-op if outlined)
        for r in TEXT_COVERS:
            page.add_redact_annot(UD(r), fill=None)
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
            text=pymupdf.PDF_REDACT_TEXT_REMOVE,
        )

        # 2) paint opaque white over old text + logo (hides outlined curves and
        #    the vector logo in every viewer; kept inside the frame lines)
        for r in TEXT_COVERS + [LOGO_COVER]:
            page.draw_rect(UD(r), color=None, fill=(1, 1, 1))

        # 3) ATM logo + new upright, centred text
        page.insert_image(UD(box(103, 723, 752)), filename=logo,
                          rotate=270, keep_proportion=True)
        put(box(171, 335, 352),
            "ATM Tanks Panel Type Water Tank", cap=11, bold=True)
        put(box(92, 516, 536), "ATM TANKS", cap=11, bold=True)
        top, row = 753.0, 10.8
        for i, line in enumerate(CONTACT):
            put(box(169, top + i * row, top + (i + 1) * row),
                line, cap=8, bold=False)
        put(box(145, 810.5, 820), "Copyright ATM Tanks Group",
            cap=6.8, bold=False)

    # --- scrub metadata -----------------------------------------------------
    meta = doc.metadata or {}
    meta["title"] = "7X2X4-ATM TANKS - PROJECT IN AUSTRALIA - 26SE399"
    meta["author"] = "ATM Tanks"
    doc.set_metadata(meta)
    try:
        doc.del_xml_metadata()
    except Exception:
        pass

    doc.save(dst, garbage=4, deflate=True, clean=True)
    doc.close()

    scrub_solico_metadata(dst)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        here, "assets", "source-drawing-26SE399.pdf")
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        here, os.pardir, "output",
        "7X2X4-ATM_TANKS_-_PROJECT_IN_AUSTRALIA_-_26SE399.pdf")
    logo = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        here, "assets", "atm-logo.jpg")
    process(src, dst, logo)
    print(f"wrote {dst}")
