#!/usr/bin/env python3
"""Rebrand the Solico tank shop-drawing PDF with ATM Tanks company details.

Replacements applied on every page:
  * "Solico Panel Type Water Tank"            -> "ATM Tanks Panel Type Water Tank"
  * Contractor "ATM TANK"                     -> "ATM TANKS"
  * Solico vector logo                        -> ATM Tanks logo image
  * Solico Dubai address / phone / email      -> ATM Tanks Currumbin address block
  * "Copyright Solico Fiber Glass Factory..." -> "Copyright ATM Tanks Group"
  * PDF metadata Solico path                  -> ATM Tanks title

The source pages carry a /Rotate 270, so page content is authored in the
un-rotated media-box coordinate system.  All target rectangles below are given
in the *displayed* (rotated, human-readable) coordinate system and converted to
media-box coordinates with U().  Inserted text/images use rotate=270 so they
render upright in the displayed view.
"""
import sys
import pymupdf

H = 841.9199829101562  # media-box height == displayed width origin offset


def U(dx0, dy0, dx1, dy1):
    """Displayed rect -> un-rotated media-box rect (page /Rotate 270)."""
    return pymupdf.Rect(H - dy1, dx0, H - dy0, dx1)


def put(page, drect, text, cap, bold, color=(0, 0, 0)):
    """Insert one upright, centred line into a displayed-coordinate box.

    On this rotated page the limiting dimensions are:
      * reading direction  -> box display *width*  (dx1 - dx0)
      * line height         -> box display *height* (dy1 - dy0)
    Pick the largest font (<= cap) that satisfies both, then shrink until
    insert_textbox reports the line actually fits (positive return value).
    """
    fontname = "hebo" if bold else "helv"
    dw = (drect[2] - drect[0]) - 2
    dh = (drect[3] - drect[1])
    w1 = pymupdf.get_text_length(text, fontname=fontname, fontsize=1)
    fs = min(cap, dw / w1 if w1 else cap, dh / 1.72)
    r = U(*drect)
    while fs > 2:
        if page.insert_textbox(r, text, fontsize=fs, fontname=fontname,
                               rotate=270, align=1, color=color) >= 0:
            return fs
        fs -= 0.25
    return fs


def process(src, dst, logo):
    doc = pymupdf.open(src)

    # The bottom title-block cell is bounded by a red frame spanning the
    # displayed rectangle x[966, 1173].  Its centre (x = 1069.5) is where all
    # logo/contact content must be centred.  Redactions use fill=None so that
    # frame/border lines crossing a redaction rectangle are never painted over
    # (only fully-covered line-art -- the Solico logo -- is removed).
    cx = 1069.5

    def box(width, dy0, dy1):
        return (cx - width / 2, dy0, cx + width / 2, dy1)

    for page in doc:
        # --- remove old Solico TEXT only ------------------------------------
        # fill=None + LINE_ART_NONE guarantees no frame/border line is painted
        # over or deleted.
        for r in [
            (985, 334, 1158, 352),     # title cell
            (1024, 514, 1116, 538),    # contractor cell
            (975, 762, 1160, 808),     # contact block
            (997, 810, 1142, 820.5),   # copyright line
        ]:
            page.add_redact_annot(U(*r), fill=None)
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
            text=pymupdf.PDF_REDACT_TEXT_REMOVE,
        )

        # --- hide the Solico logo -------------------------------------------
        # The logo is vector art inside a form XObject that redaction cannot
        # reliably delete (some viewers still render the leftover strokes), so
        # paint an opaque white rectangle over it, kept strictly INSIDE the
        # cell frame lines (top y=719, bottom y=809.6, sides x=966/1173) so no
        # border is affected.
        page.draw_rect(U(968, 720, 1172, 762), color=None, fill=(1, 1, 1))

        # --- ATM logo, centred in the cell ----------------------------------
        page.insert_image(U(*box(103, 723, 752)), filename=logo,
                          rotate=270, keep_proportion=True)

        # --- new upright, centred text --------------------------------------
        put(page, box(171, 335, 352),
            "ATM Tanks Panel Type Water Tank", cap=11, bold=True)
        put(page, box(92, 516, 536), "ATM TANKS", cap=11, bold=True)

        contact = [
            "52/1014 Currumbin Creek Road,",
            "Currumbin Waters QLD 4223",
            "1800 422 444",
            "info@atmtanks.com.au",
            "atmtanks.com.au",
        ]
        top, row = 753.0, 10.8
        for i, line in enumerate(contact):
            put(page, box(169, top + i * row, top + (i + 1) * row),
                line, cap=8, bold=False)

        put(page, box(145, 810.5, 820),
            "Copyright ATM Tanks Group", cap=6.8, bold=False)

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


if __name__ == "__main__":
    import os
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
