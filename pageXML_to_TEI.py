from pathlib import Path
from lxml import etree
import re
import unicodedata

SOURCE_DIR = Path("data/musico-pratico_Pontio_RAGIONAMENTO-DI-MVSICA_1588")

OUTPUT = Path("output/musico-pratico_Pontio_RAGIONAMENTO-DI-MVSICA_1588.xml")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# Liste aller gängigen erlaubten Zeichen
ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789äöüÄÖÜſß.,;:-?!§$%&/()=\"_–'#*+")
UNUSUAL = {}  # dict[char] -> count

def collect_unusual(s: str):
    """Sammelt alle ungewöhnlichen Zeichen"""
    if not s:
        return
    for ch in s:
        if ch.isspace():
            continue
        if ch not in ALLOWED:
            UNUSUAL[ch] = UNUSUAL.get(ch, 0) + 1

def next_lb(parent, n: int):
    """Fügt vor dem neuen <lb> eine Newline ein und nummeriert Zeilen."""
    # Newline in vorherigem Element oder Text
    if len(parent):
        last = parent[-1]
        last.tail = (last.tail or "") + "\n"
    else:
        parent.text = (parent.text or "") + "\n"
    lb = etree.SubElement(parent, tei("lb"))
    lb.set("n", str(n))
    return lb

def tei(tag): 
    return f"{{{TEI_NS}}}{tag}"

def get_text_equiv(line):
    # Bevorzugt index='0' (GT), sonst '1' (Pred)
    for idx in ("0", "1"):
        te = line.find(f"./{{*}}TextEquiv[@index='{idx}']")
        if te is not None:
            uni = te.find("./{*}Unicode")
            if uni is not None:
                return "".join(uni.itertext())
    # Fallback: erstes Unicode
    uni = line.find(".//{*}Unicode")
    return "".join(uni.itertext()) if uni is not None else ""

def parse_points(coords_str):
    pts = []
    if not coords_str:
        return pts, None
    for pair in coords_str.split():
        x, y = pair.split(",")
        pts.append((int(float(x)), int(float(y))))
    if not pts:
        return pts, None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    return pts, bbox

def add_zone(parent_surface, page_id, region_el, default_type="text"):
    reg_id = region_el.get("id") or f"r-{len(parent_surface)}"
    coords = region_el.find(".//{*}Coords")
    pts, bbox = parse_points(coords.get("points") if coords is not None else "")
    z = etree.SubElement(parent_surface, tei("zone"))
    z.set(XML_ID, f"z-{page_id}-{reg_id}")
    rtype = region_el.get("type") or default_type
    z.set("type", rtype)
    if pts:
        points_attr = " ".join([f"{x},{y}" for x, y in pts])
        z.set("points", points_attr)
    if bbox:
        ulx, uly, lrx, lry = bbox
        z.set("ulx", str(ulx)); z.set("uly", str(uly))
        z.set("lrx", str(lrx)); z.set("lry", str(lry))
    return z

def ensure_section(body, current_section):
    if current_section is None:
        sec = etree.SubElement(body, tei("div"))
        sec.set("type", "section")
        return sec
    return current_section


def add_paragraph(parent, zone_id, region_el, page_state, merge_into_prev=False):
    # ggf. an letzten Absatz anhängen
    if merge_into_prev and len(parent) and parent[-1].tag == tei("p"):
        p = parent[-1]
    else:
        p = etree.SubElement(parent, tei("p"))
        p.set("facs", f"#{zone_id}")

    for line in region_el.findall(".//{*}TextLine"):
        txt = get_text_equiv(line)
        if not txt:
            continue
        page_state["line_no"] += 1
        lb = next_lb(p, page_state["line_no"])
        lb.tail = txt
        collect_unusual(txt)

    return p

def add_multiline_head(parent, zone_id, region_el, page_state):
    head = etree.SubElement(parent, tei("head"))
    head.set("facs", f"#{zone_id}")
    lines = [get_text_equiv(l) for l in region_el.findall(".//{*}TextLine")]
    if not lines:
        return head
    # erste Zeile ebenfalls mit <lb n=.../>
    page_state["line_no"] += 1
    lb0 = next_lb(head, page_state["line_no"])
    lb0.tail = lines[0]
    for t in lines[1:]:
        page_state["line_no"] += 1
        lb = next_lb(head, page_state["line_no"])
        lb.tail = t
        collect_unusual(lb.tail)

    return head

LETTER = r"[0-9A-Za-zÀ-ÖØ-öø-ſß]"
SEP = r"[.\u00B7·,:;·\-–—]"  # Punkt, Mittelpunkt, Komma, Doppelpunkt, Strichvarianten
SPACED_BETWEEN = re.compile(rf"{LETTER}\s*(?:{SEP}\s*)+\s*{LETTER}|{LETTER}\s+{LETTER}", re.IGNORECASE)
TRAIL_PUNCT = re.compile(rf"\s*(?:{SEP})+\s*$")

def normalize_header_text(text: str) -> tuple[str, bool]:
    if not text:
        return text, False
    t = unicodedata.normalize("NFKC", text)
    t = " ".join(t.split())  # Whitespace vereinheitlichen
    spaced = bool(SPACED_BETWEEN.search(t))
    t = TRAIL_PUNCT.sub("", t)          # Endzeichen wie '.', ',' entfernen
    # alles außer Buchstaben entfernen (Zwischenzeichen, Punkte etc.)
    core = re.sub(rf"(?:\s|{SEP})+", "", t)
    # falls noch „fremde“ Zeichen vorkommen, nur Groß/Kleinschreibung normieren
    if not core or not re.fullmatch(rf"{LETTER}+", core, re.IGNORECASE):
        return t.upper(), spaced
    return core.upper(), spaced

def add_fw(parent, zone_id, region_el, rtype_lc, page_state=None):
    fw = etree.SubElement(parent, tei("fw"))
    if rtype_lc == "header":
        fw.set("type", "header")
        fw.set("rend", "spaced")
    elif rtype_lc == "page-number":
        fw.set("type", "folNum")
    elif rtype_lc == "signature-mark":
        fw.set("type", "sig")
    elif rtype_lc == "catch-word":
        fw.set("type", "catch")
    else:
        fw.set("type", "other")

    fw.set("facs", f"#{zone_id}")

    lines = [get_text_equiv(l).strip()
             for l in region_el.findall(".//{*}TextLine")
             if get_text_equiv(l).strip()]

    if not lines:
        return fw

    # Zeile 1
    t0 = lines[0]
    collect_unusual(t0)
    if fw.get("type") == "header":
        t0n, spaced0 = normalize_header_text(t0)
        fw.text = t0n
        if spaced0:
            fw.set("rend", "spaced")
    else:
        fw.text = t0

    # Folgezeilen
    for t in lines[1:]:
        collect_unusual(t)
        if page_state is not None:
            page_state["line_no"] += 1
            lb = next_lb(fw, page_state["line_no"])
        else:
            lb = etree.SubElement(fw, tei("lb"))
        if fw.get("type") == "header":
            tn, spacedN = normalize_header_text(t)
            lb.tail = tn
            if spacedN and "rend" not in fw.attrib:
                fw.set("rend", "spaced")
        else:
            lb.tail = t
            collect_unusual(t)
    return fw

def add_figure(parent, zone_id, region_el, fig_type=None):
    fig = etree.SubElement(parent, tei("figure"))
    t = (fig_type or region_el.get("type") or "graphic").lower()
    fig.set("type", t)
    fig.set("facs", f"#{zone_id}")
    return fig

def add_music(parent, zone_id, region_el, fig_type=None):
    music = etree.SubElement(parent, tei("notatedMusic"))
    music.set("facs", f"#{zone_id}")
    return music

def build_reading_order(root):
    order = []
    ro = root.find(".//{*}ReadingOrder/{*}OrderedGroup")
    if ro is None:
        return order
    for ref in ro.findall(".//{*}RegionRefIndexed"):
        try:
            idx = int(ref.get("index"))
        except (TypeError, ValueError):
            continue
        order.append((idx, ref.get("regionRef")))
    order.sort(key=lambda x: x[0])
    return [rid for _, rid in order]

def first(el, path):
    return el.find(path)

def main():
    
    page_state = {"line_no": 0, "after_pb": False}

    tei_root = etree.Element(tei("TEI"), nsmap={None: TEI_NS})
    tei_header = etree.SubElement(tei_root, tei("teiHeader"))

    # <fileDesc>
    fileDesc = etree.SubElement(tei_header, tei("fileDesc"))

    # <titleStmt>
    titleStmt = etree.SubElement(fileDesc, tei("titleStmt"))
    etree.SubElement(titleStmt, tei("title"), type="main")
    etree.SubElement(titleStmt, tei("title"), n="1.1")
    author = etree.SubElement(titleStmt, tei("author"))
    a_pers = etree.SubElement(author, tei("persName"), ref="https://d-nb.info/gnd/119000695")
    etree.SubElement(a_pers, tei("surname")).text = "Pontio"
    etree.SubElement(a_pers, tei("forename")).text = "Pietro"
    editor = etree.SubElement(titleStmt, tei("editor"), corresp="#MusicoPratico")
    e_pers = etree.SubElement(editor, tei("persName"))
    etree.SubElement(e_pers, tei("surname"))
    etree.SubElement(e_pers, tei("forename"))
    respStmt = etree.SubElement(titleStmt, tei("respStmt"))
    etree.SubElement(respStmt, tei("orgName"))
    resp = etree.SubElement(respStmt, tei("resp"))
    etree.SubElement(resp, tei("note"), type="remarkResponsibility")
    etree.SubElement(resp, tei("ref"), target="https://example.com/")

    # <editionStmt>
    editionStmt = etree.SubElement(fileDesc, tei("editionStmt"))
    etree.SubElement(editionStmt, tei("edition"))

    # <publicationStmt>
    publicationStmt = etree.SubElement(fileDesc, tei("publicationStmt"))
    publisher = etree.SubElement(publicationStmt, tei("publisher"), **{XML_ID: "musico-pratico"})
    etree.SubElement(publisher, tei("orgName"), role="hostingInstitution")
    etree.SubElement(publisher, tei("orgName"), role="project")
    etree.SubElement(publisher, tei("email"))
    etree.SubElement(publisher, tei("email"))
    address = etree.SubElement(publisher, tei("address"))
    etree.SubElement(address, tei("addrLine"))
    etree.SubElement(publicationStmt, tei("pubPlace"))
    etree.SubElement(publicationStmt, tei("date"), type="publication")
    availability = etree.SubElement(publicationStmt, tei("availability"))
    licence = etree.SubElement(availability, tei("licence"), target="http://creativecommons.org/licenses/by-nc-sa/4.0/")
    etree.SubElement(licence, tei("p"))
    idno_wrap = etree.SubElement(publicationStmt, tei("idno"))
    etree.SubElement(idno_wrap, tei("idno"), resp="example")

    # <sourceDesc>
    sourceDesc = etree.SubElement(fileDesc, tei("sourceDesc"))
    biblFull = etree.SubElement(sourceDesc, tei("biblFull"))
    bf_titleStmt = etree.SubElement(biblFull, tei("titleStmt"))
    etree.SubElement(bf_titleStmt, tei("title"), level="m")
    bf_author = etree.SubElement(bf_titleStmt, tei("author"))
    bf_pers = etree.SubElement(bf_author, tei("persName"), ref="https://d-nb.info/gnd/119000695")
    etree.SubElement(bf_pers, tei("surname"))
    etree.SubElement(bf_pers, tei("forename"))
    bf_editionStmt = etree.SubElement(biblFull, tei("editionStmt"))
    etree.SubElement(bf_editionStmt, tei("edition"))
    bf_publicationStmt = etree.SubElement(biblFull, tei("publicationStmt"))
    etree.SubElement(bf_publicationStmt, tei("publisher"))
    etree.SubElement(bf_publicationStmt, tei("pubPlace"))
    etree.SubElement(bf_publicationStmt, tei("date"), type="publication", when="1588")
    etree.SubElement(bf_publicationStmt, tei("date"), type="firstPublication", when="1588")
    msDesc = etree.SubElement(sourceDesc, tei("msDesc"))
    msIdentifier = etree.SubElement(msDesc, tei("msIdentifier"))
    etree.SubElement(msIdentifier, tei("settlement"))
    etree.SubElement(msIdentifier, tei("repository"))
    physDesc = etree.SubElement(msDesc, tei("physDesc"))
    typeDesc = etree.SubElement(physDesc, tei("typeDesc"))
    etree.SubElement(typeDesc, tei("p"))

    # <encodingDesc>
    encodingDesc = etree.SubElement(tei_header, tei("encodingDesc"))
    editorialDecl = etree.SubElement(encodingDesc, tei("editorialDecl"))
    etree.SubElement(editorialDecl, tei("p"))
    etree.SubElement(editorialDecl, tei("p"))

    # <profileDesc>
    profileDesc = etree.SubElement(tei_header, tei("profileDesc"))
    langUsage = etree.SubElement(profileDesc, tei("langUsage"))
    etree.SubElement(langUsage, tei("language"), ident="ita")

    # --- Ende TEI-Header ---

    text = etree.SubElement(tei_root, tei("text"))
    body = etree.SubElement(text, tei("body"))
    facs = etree.SubElement(tei_root, tei("facsimile"))

    xml_files = sorted(SOURCE_DIR.glob("*.xml"))
    if not xml_files:
        print(f"Keine XML-Dateien in {SOURCE_DIR}")
        return
    

    for pageno, xml_path in enumerate(xml_files, start=1):
        try:
            root = etree.parse(str(xml_path)).getroot()
        except Exception as e:
            print(f"Übersprungen: {xml_path.name} ({e})")
            continue

        page_el = first(root, ".//{*}Page")
        page_id = f"s{pageno:03d}"

        # facsimile/surface + graphic
        surface = etree.SubElement(facs, tei("surface"))
        surface.set(XML_ID, page_id)
        img = page_el.get("imageFilename") if page_el is not None else None
        if img:
            g = etree.SubElement(surface, tei("graphic"))
            g.set("url", img)

        # Seitenumbruch zuerst
        pb = etree.SubElement(body, tei("pb"))
        pb.set("n", str(pageno)); pb.set("facs", f"#{page_id}")
        page_state["line_no"] = 0
        page_state["after_pb"] = True

        # Zonen erzeugen
        regions_by_id = {}
        for tag, default_type in (
            ("TextRegion", "text"), 
            ("GraphicRegion", "graphic"), 
            ("SeparatorRegion", "separator"),
            ("MusicRegion", "music"),
            ("TableRegion", "table"),
            ):
            for r in root.findall(f".//{{*}}{tag}"):
                rid = r.get("id")
                if not rid:
                    continue
                regions_by_id[rid] = (r, default_type)
                add_zone(surface, page_id, r, default_type=default_type)

        # Reading Order
        ro_ids = build_reading_order(root)

        # Positionen für Fallback sammeln
        positions = {}
        for rid, (r, _default) in regions_by_id.items():
            c = r.find(".//{*}Coords")
            pts, bbox = parse_points(c.get("points") if c is not None else "")
            # bbox = (ulx, uly, lrx, lry); Fallback weit nach unten, wenn fehlt
            positions[rid] = (bbox[1], bbox[0]) if bbox else (10**9, 10**9)

        ordered = []
        seen = set()

        # 1) falls vorhanden: ReadingOrder strikt einhalten
        for rid in ro_ids:
            if rid in regions_by_id and rid not in seen:
                ordered.append(rid); seen.add(rid)

        # 2) Rest: nach (uly, ulx) sortieren, unabhängig vom Region-Typ
        for rid in sorted((r for r in regions_by_id if r not in seen),
                        key=lambda r: positions[r]):
            ordered.append(rid)


        # div pro Überschrift, damit pro <div> genau ein <head>
        current_section = None

        for rid in ordered:
            region_el, default_type = regions_by_id[rid]
            zone_id = f"z-{page_id}-{rid}"
            rtype_lc = (region_el.get("type") or "").lower()

            # Laufkopf direkt unter body als <fw type="header">
            if rtype_lc == "header":
                add_fw(body, zone_id, region_el, rtype_lc)
                continue

            # Überschrift startet neue Abschnitts-<div> unter body
            elif rtype_lc == "heading":
                current_section = etree.SubElement(body, tei("div"))
                current_section.set("type", "section")
                add_multiline_head(current_section, zone_id, region_el, page_state)
                page_state["after_pb"] = False
                continue

            # Ziel-Elternteil: laufende Abschnitts-<div> oder body
            parent = current_section if current_section is not None else ensure_section(body, current_section)

            if rtype_lc in {"page-number", "catch_word", "catch-word", "signature-mark"}:
                parent = body  # fw ist unter body erlaubt
                add_fw(parent, zone_id, region_el, rtype_lc)

            elif "graphic" in region_el.tag.lower() or default_type in {"graphic", "table"}:
                parent = body  # figure ist unter body erlaubt
                fig_type = "table" if default_type == "table" else "graphic"
                add_figure(parent, zone_id, region_el, fig_type=fig_type)

            elif default_type == "music":
                parent = body  # notatedMusic ist unter body erlaubt
                notated = etree.SubElement(parent, tei("notatedMusic"))
                notated.set("facs", f"#{zone_id}")

            else:
                # nach Seitenumbruch an vorherigen Absatz anhängen, falls vorhanden
                merge = bool(page_state["after_pb"] and len(parent) and parent[-1].tag == tei("p"))
                add_paragraph(parent, zone_id, region_el, page_state, merge_into_prev=merge)
                page_state["after_pb"] = False

    # leere DIVs entfernen
    for div in body.findall(".//{*}div[@type='section']"):
        if len(div) == 0:  # keine Kindelemente
            div.getparent().remove(div)


    if UNUSUAL:
        hdr = tei_root.find("./{*}teiHeader")
        prof = hdr.find("./{*}encodingDesc") if hdr is not None else None
        if prof is None and hdr is not None:
            prof = etree.SubElement(hdr, tei("encodingDesc"))
        if prof is not None:
            p = etree.SubElement(prof, tei("p"))
            lst = etree.SubElement(p, tei("list"))
            lst.set("type", "unusualChars")
            # sortiert nach Häufigkeit, dann Codepunkt
            for ch, cnt in sorted(UNUSUAL.items(), key=lambda kv: (-kv[1], ord(kv[0]))):
                item = etree.SubElement(lst, tei("item"))
                # U+XXXX und Unicode-Name hinzufügen
                cp = f"U+{ord(ch):04X}"
                try:
                    name = unicodedata.name(ch)
                except ValueError:
                    name = "UNNAMED"
                item.text = f"{ch}\t{cp}\t({cnt})\t{name}"

    tree = etree.ElementTree(tei_root)
    tree.write(str(OUTPUT), encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"OK: {OUTPUT}")

if __name__ == "__main__":
    main()
