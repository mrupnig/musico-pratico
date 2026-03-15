from pathlib import Path
from lxml import etree
import argparse
import re
import unicodedata

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# Liste aller gängigen erlaubten Zeichen
ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789äöüÄÖÜſß.,;:-?!§$%&/()=\"_–'#*+")
UNUSUAL = {}  # dict[char] -> count

def collect_unusual(s: str):
    """
    Record characters that are not part of the globally allowed character set.

    This function inspects each character in the provided string and updates
    the global dictionary UNUSUAL, mapping each unexpected character to the
    number of times it has been encountered across the entire conversion run.

    Parameters
    ----------
    s : str | None
        The string to inspect. If None or empty, the function performs no action.

    Side Effects
    ------------
    Modifies the global dictionary UNUSUAL.
    """

    if not s:
        return
    for ch in s:
        if ch.isspace():
            continue
        if ch not in ALLOWED:
            UNUSUAL[ch] = UNUSUAL.get(ch, 0) + 1

def base_mapping(ch: str) -> str | None: 
    """
    Return a normalized Latin base character for a given Unicode character.

    The function decomposes the character using NFD normalization and removes
    all combining diacritics. If the resulting base character is a single
    Latin letter (A–Z or a–z), its lowercase form is returned; otherwise
    `None` is returned.

    Parameters
    ----------
    ch : str
        A single Unicode character.

    Returns
    -------
    str | None
        The lowercase base Latin character, or None if no valid mapping exists.
    """

    # NFD: Buchstabe + kombinierende Zeichen
    decomp = unicodedata.normalize("NFD", ch)
    # nur Zeichen mit combining class 0 (Grundbuchstaben) nehmen
    base_chars = [c for c in decomp if unicodedata.combining(c) == 0]
    if not base_chars:
        return None
    base = "".join(base_chars)
    # Wenn das Ergebnis kein lateinischer Buchstabe mehr ist, lieber None zurückgeben
    if not re.fullmatch(r"[A-Za-z]", base):
        return None
    return base.lower()

def next_lb(parent, n: int):
    """
    Insert a TEI <lb> (line break) element into the given parent element.

    A newline is inserted before the new element. If the parent already has
    child nodes, the newline is appended to the tail of the last child;
    otherwise, it is written into the parent's text. The <lb> receives an
    `@n` attribute containing the line number.

    Parameters
    ----------
    parent : etree._Element
        The TEI parent element to append to.
    n : int | str
        Line number or identifier to assign to the <lb>.

    Returns
    -------
    etree._Element
        The newly created <lb> element.
    """

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
    """
    Return the fully qualified TEI tag name for a given local tag.

    Parameters
    ----------
    tag : str
        Local tag name without namespace.

    Returns
    -------
    str
        Fully namespaced TEI tag name.
    """

    return f"{{{TEI_NS}}}{tag}"

def get_text_equiv(line):
    """
    Extract the textual content of a PAGE <TextLine>.

    The function prioritizes TextEquiv elements in the following order:
    1. TextEquiv[@index="0"] (ground truth)
    2. TextEquiv[@index="1"] (prediction)
    3. The first available <Unicode> child

    Parameters
    ----------
    line : etree._Element
        PAGE <TextLine> element.

    Returns
    -------
    str
        The extracted textual content, or an empty string if no text is available.
    """

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
    """
    Parse a PAGE @points attribute into coordinate tuples and compute a bounding box.

    The input string typically contains coordinate pairs such as:
        "12.0,45.0 30.5,47.2 ..."

    Coordinates are converted to integers via int(float(x)).

    Parameters
    ----------
    coords_str : str
        The PAGE points string.

    Returns
    -------
    (list[tuple[int, int]], (int, int, int, int) | None)
        A list of (x, y) tuples and a bounding box (min_x, min_y, max_x, max_y).
        Returns None for the bounding box if no points could be parsed.
    """

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

def is_near_table(y, table_y_ranges, tol=3):
    """
    Determine whether a given vertical position lies close to a table region.

    This is used to assign alphabetical suffixes (a/b/c) for lines located on
    the same vertical level inside or near table regions.

    Parameters
    ----------
    y : float | int
        The vertical coordinate to test.
    table_y_ranges : Iterable[tuple[int, int]]
        A list of (y_min, y_max) tuples representing table region extents.
    tol : int
        Pixel tolerance added to both ends of each range.

    Returns
    -------
    bool
        True if `y` falls within any (y_min - tol, y_max + tol) interval.
    """
    for y_min, y_max in table_y_ranges:
        if y_min - tol <= y <= y_max + tol:
            return True
    return False

def add_zone(parent_surface, page_id, region_el, default_type="text"):
    """
    Create a TEI <zone> for a PAGE region and attach it to a given <surface>.

    The <zone> reflects both the geometry and the functional type of the PAGE
    region. Bounding boxes and point lists are copied when available.

    Parameters
    ----------
    parent_surface : etree._Element
        The TEI <surface> to append the <zone> to.
    page_id : str
        The internal page identifier (e.g., "s001").
    region_el : etree._Element
        The PAGE region element.
    default_type : str
        A fallback type if the PAGE region has no @type.

    Returns
    -------
    etree._Element
        The created <zone> element.
    """

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
    """
    Ensure that a <div type="section"> exists inside the TEI <body>.

    If `current_section` already exists, it is returned. Otherwise, a new
    section <div> is created.

    Parameters
    ----------
    body : etree._Element
        The TEI <body> element.
    current_section : etree._Element | None
        Existing section or None.

    Returns
    -------
    etree._Element
        The existing or newly created <div type="section">.
    """

    if current_section is None:
        sec = etree.SubElement(body, tei("div"))
        sec.set("type", "section")
        return sec
    return current_section

def get_baseline_xy(line_el):
    """
    Compute a representative (x, y) position for a PAGE <TextLine>.

    The function prefers Baseline/@points when available, falling back to
    Coords/@points. The x-coordinate is the leftmost point, and the y-coordinate
    is the average of all y-values.

    Used for ordering text lines within a region.

    Parameters
    ----------
    line_el : etree._Element
        PAGE <TextLine> element.

    Returns
    -------
    tuple[float | None, float | None]
        The (x, y) position, or (None, None) if no usable coordinates exist.
    """

    bl = line_el.find(".//{*}Baseline")
    if bl is not None and bl.get("points"):
        pts, bbox = parse_points(bl.get("points"))
    else:
        coords_el = line_el.find(".//{*}Coords")
        if coords_el is None or not coords_el.get("points"):
            return None, None
        pts, bbox = parse_points(coords_el.get("points"))

    if not pts:
        return None, None

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    y = sum(ys) / len(ys)
    x = min(xs)
    return x, y

def add_paragraph(parent, zone_id, region_el, page_state, merge_into_prev=False):
    """
    Create or extend a TEI paragraph (<p>) from a PAGE TextRegion.

    This function:
    - Creates a new <p> or merges into the previous one (for cross-page text)
    - Sorts text lines by their geometric order (y, then x)
    - Assigns line numbers via <lb> elements, including a/b/c suffixes near tables
    - Extracts textual content and records unusual characters
    - Moves marginalia (<fw>) and page breaks (<pb>) into the paragraph when merging

    Parameters
    ----------
    parent : etree._Element
        The TEI element (e.g., a chapter <div>) receiving the paragraph.
    zone_id : str
        ID of the associated <zone>.
    region_el : etree._Element
        PAGE TextRegion.
    page_state : dict
        Includes:
            - "line_no": integer counter for TEI <lb> numbers
            - "table_y_ranges": list of table vertical extents
            - "current_pb": reference to the <pb> element
    merge_into_prev : bool
        Whether this paragraph continues the previous one.

    Returns
    -------
    etree._Element
        The newly created or extended <p>.
    """

    if merge_into_prev:
        # letzten <p> im parent suchen
        p = None
        for child in reversed(parent):
            if child.tag == tei("p"):
                p = child
                break
        if p is None:
            p = etree.SubElement(parent, tei("p"))
            p.set("facs", f"#{zone_id}")

        # pb und ggf. catch/sig vor pb in den Absatz ziehen
        pb = page_state.get("current_pb")
        if pb is not None and pb.getparent() is parent:
            pb_pid = page_id_from_facs(pb.get("facs"))

            siblings = list(parent)
            pb_idx = siblings.index(pb)

            to_move_fw = []
            if pb_idx > 0:
                for i in range(pb_idx - 1, -1, -1):
                    sib = siblings[i]
                    if sib.tag == tei("fw") and sib.get("type") in {"catch", "sig"}:
                        to_move_fw.append(sib)
                    else:
                        break

            for fw in reversed(to_move_fw):
                parent.remove(fw)
                # vor dem fw einen Zeilenumbruch einfügen
                if len(p):
                    last = p[-1]
                    last.tail = (last.tail or "") + "\n"
                else:
                    p.text = (p.text or "") + "\n"
                p.append(fw)

            # jetzt pb bewegen – ebenfalls mit Zeilenumbruch davor
            if pb_idx != -1:
                parent.remove(pb)
                if len(p):
                    last = p[-1]
                    last.tail = (last.tail or "") + "\n"
                else:
                    p.text = (p.text or "") + "\n"
                p.append(pb)

    else:
        p = etree.SubElement(parent, tei("p"))
        p.set("facs", f"#{zone_id}")

    lines = region_el.findall(".//{*}TextLine")
    info = []
    for line in lines:
        x, y = get_baseline_xy(line)
        if y is None:
            continue
        info.append({"el": line, "x": x, "y": y})

    if not info:
        return p

    # erst nach y, dann nach x sortieren
    info.sort(key=lambda d: (round(d["y"]), d["x"]))

    y_eps = 6  # Toleranz in Pixeln – etwas großzügiger, damit "geteilte" Zeilen zusammenfallen
    groups = []
    current_group = [info[0]]
    current_y = info[0]["y"]

    for d in info[1:]:
        if abs(d["y"] - current_y) <= y_eps:
            current_group.append(d)
        else:
            groups.append(current_group)
            current_group = [d]
            current_y = d["y"]
    groups.append(current_group)

    table_y_ranges = page_state.get("table_y_ranges", [])

    for group in groups:
        # innerhalb der Gruppe links→rechts sortieren
        group.sort(key=lambda d: d["x"])

        # repräsentative y-Höhe der Gruppe
        group_y = sum(d["y"] for d in group) / len(group)
        near_table = is_near_table(group_y, table_y_ranges)

        # Wenn mehrere Segmente auf gleicher Höhe und in TableRegion:
        # gleiche Grundnummer + a/b/c-Suffix
        if len(group) > 1 and near_table:
            page_state["line_no"] += 1
            base_no = page_state["line_no"]
            for idx, d in enumerate(group):
                suffix = chr(ord("a") + idx)   # a, b, c ...
                lb = next_lb(p, f"{base_no}{suffix}")
                text = get_text_equiv(d["el"]).rstrip()
                if not text:
                    continue
                collect_unusual(text)
                lb.tail = (lb.tail or "") + text
        else:
            # normale Zeilen: jede Zeile eigene Nummer
            for d in group:
                page_state["line_no"] += 1
                lb = next_lb(p, page_state["line_no"])
                text = get_text_equiv(d["el"]).rstrip()
                if not text:
                    continue
                collect_unusual(text)
                lb.tail = (lb.tail or "") + text

    return p


def add_heading_lines(head, region_el, page_state):
    """
    Insert heading lines from a PAGE heading region into a TEI <head>.

    Each PAGE text line produces:
    - a numbered <lb>
    - text inserted as the tail of that <lb>
    - a call to collect_unusual() for character tracking

    Parameters
    ----------
    head : etree._Element
        TEI <head> element.
    region_el : etree._Element
        PAGE heading region.
    page_state : dict
        Contains the "line_no" counter.
    """

    for line in region_el.findall(".//{*}TextLine"):
        txt = get_text_equiv(line)
        if not txt:
            continue
        page_state["line_no"] += 1
        lb = next_lb(head, page_state["line_no"])
        lb.tail = txt
        collect_unusual(lb.tail)

def page_id_from_facs(facs_val: str | None) -> str | None:
    """
    Extract a page identifier (e.g., "s001") from a TEI @facs attribute.

    Supported patterns:
    - "#z-sNNN-rX"
    - "#sNNN"

    Parameters
    ----------
    facs_val : str | None
        The @facs value.

    Returns
    -------
    str | None
        The extracted page ID or None if no valid pattern is found.
    """

    if not facs_val:
        return None
    first = facs_val.split()[0]
    if first.startswith("#z-"):
        # #z-sNNN-rX
        frag = first[3:]              # "sNNN-rX"
        return frag.split("-")[0]     # "sNNN"
    if first.startswith("#s"):
        return first[1:]              # "sNNN"
    return None

def is_near_table(y, table_y_ranges, tol=3):
    for y_min, y_max in table_y_ranges:
        if y_min - tol <= y <= y_max + tol:
            return True
    return False

LETTER = r"[0-9A-Za-zÀ-ÖØ-öø-ſß]"
SEP = r"[.\u00B7·,:;·\-–—]"  # Punkt, Mittelpunkt, Komma, Doppelpunkt, Strichvarianten
SPACED_BETWEEN = re.compile(rf"{LETTER}\s*(?:{SEP}\s*)+\s*{LETTER}|{LETTER}\s+{LETTER}", re.IGNORECASE)
TRAIL_PUNCT = re.compile(rf"\s*(?:{SEP})+\s*$")

def normalize_header_text(text: str) -> tuple[str, bool]:
    """
    Normalize header text and detect whether the text appears letter-spaced.

    Normalization includes:
    - Unicode NFKC folding
    - Whitespace reduction
    - Detection of spaced-out letter sequences
    - Removal of trailing punctuation
    - Extraction of a letter-only "core" value for canonicalization

    Parameters
    ----------
    text : str
        The original header text.

    Returns
    -------
    tuple[str, bool]
        (normalized_uppercase_text, spaced_flag)
    """

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
    """
    Create a TEI <fw> element from a PAGE marginal/folio/header region.

    Behavior:
    - Maps PAGE region types to TEI fw types (header, folNum, sig, catch, other)
    - Normalizes header text via normalize_header_text()
    - Joins multiple text lines when present
    - Records unusual characters
    - Sets @facs to the corresponding <zone>

    Parameters
    ----------
    parent : etree._Element
        TEI element to append the <fw> to.
    zone_id : str
        ID of the associated <zone>.
    region_el : etree._Element
        PAGE region.
    rtype_lc : str
        Region type in lowercase.
    page_state : dict | None
        Optional page state (reserved for future use).

    Returns
    -------
    etree._Element
        The created <fw> element.
    """

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

    # erste Zeile
    t0 = lines[0]
    collect_unusual(t0)
    if fw.get("type") == "header":
        t0n, spaced0 = normalize_header_text(t0)
        fw.text = t0n
        if spaced0:
            fw.set("rend", "spaced")
    else:
        fw.text = t0

    # Folgelinien einfach anhängen (ohne lb, ohne line_no++)
    for t in lines[1:]:
        collect_unusual(t)
        if fw.get("type") == "header":
            tn, spacedN = normalize_header_text(t)
            fw.text = (fw.text or "") + " " + tn
            if spacedN and "rend" not in fw.attrib:
                fw.set("rend", "spaced")
        else:
            fw.text = (fw.text or "") + " " + t

    return fw

def add_figure(parent, zone_id, region_el, fig_type=None):
    """
    Insert a TEI <figure> element representing a PAGE graphic/table region.

    A newline is inserted before the <figure> for readability. The type is
    derived from:
    - fig_type argument (if provided)
    - else PAGE @type
    - else "graphic"

    Parameters
    ----------
    parent : etree._Element
        The TEI element receiving the figure.
    zone_id : str
        Associated zone ID.
    region_el : etree._Element
        PAGE region.
    fig_type : str | None
        Optional override type.

    Returns
    -------
    etree._Element
        The created <figure>.
    """

    fig = insert_with_newline(parent, "figure")
    t = (fig_type or region_el.get("type") or "graphic").lower()
    fig.set("type", t)
    fig.set("facs", f"#{zone_id}")
    return fig

def add_music(parent, zone_id, region_el, fig_type=None):
    """
    Insert a TEI <notatedMusic> element for PAGE MusicRegion objects.

    The element serves as a placeholder linking the TEI document to a musical
    notation graphic via @facs.

    Parameters
    ----------
    parent : etree._Element
        TEI insertion point.
    zone_id : str
        Associated zone ID.
    region_el : etree._Element
        PAGE MusicRegion.
    fig_type : str | None
        Reserved for later extensions.

    Returns
    -------
    etree._Element
        The created <notatedMusic> element.
    """

    music = etree.SubElement(parent, tei("notatedMusic"))
    music.set("facs", f"#{zone_id}")
    return music

def build_reading_order(root):
    """
    Extract the reading order of regions from a PAGE XML document.

    The function returns regionRef values ordered by their numeric index
    in <RegionRefIndexed> elements.

    Parameters
    ----------
    root : etree._Element
        Root element of the PAGE document.

    Returns
    -------
    list[str]
        Ordered list of regionRef identifiers.
    """

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
    """
    Convenience wrapper around Element.find().

    Parameters
    ----------
    el : etree._Element
        The context element for the search.
    path : str
        The XPath expression.

    Returns
    -------
    etree._Element | None
        The first matching element or None.
    """

    return el.find(path)

def insert_with_newline(parent, tag, ns=tei, **attrib):
    """
    Insert a newline before creating a new TEI child element.

    The newline is added to the tail of the last child or to the parent's
    text if empty. The new element is created with the specified tag and
    attributes.

    Parameters
    ----------
    parent : etree._Element
        Parent element.
    tag : str
        Local tag name.
    ns : Callable[[str], str]
        Namespace wrapper, typically `tei`.
    **attrib :
        Additional element attributes.

    Returns
    -------
    etree._Element
        The created child element.
    """

    # Zeilenumbruch vor dem Element
    if len(parent) > 0:
        last = parent[-1]
        last.tail = (last.tail or "") + "\n"
    else:
        parent.text = (parent.text or "") + "\n"

    # Element erzeugen
    elem = etree.SubElement(parent, ns(tag))
    for k, v in attrib.items():
        elem.set(k, v)
    return elem

def main():

    """
    Execute the PAGE-to-TEI conversion workflow.

    High-level responsibilities:
    - Construct TEI header, body, and facsimile structure
    - Iterate through PAGE XML files and convert each to a TEI page representation
    - Create <surface> and <zone> elements mirroring PAGE geometry
    - Insert text, marginalia, figures, tables, and music regions into TEI
    - Build paragraphs with detailed line-number assignment and table-aware suffixing
    - Maintain per-page state (line numbering, table ranges, current <pb>)
    - Populate a <charDecl> section if unusual characters were encountered
    - Write the final TEI XML document to disk

    Side Effects
    ------------
    Reads PAGE XML sources, writes a TEI XML output file, and updates the
    global UNUSUAL dictionary.
    """

    parser = argparse.ArgumentParser(description="Konvertiert PAGE XML nach TEI.")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("data/pages"),
        help="Verzeichnis mit PAGE XML-Dateien (Standard: data/pages)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("data/tei"),
        help="Ausgabepfad der TEI XML-Datei (Standard: data/tei)",
    )
    parser.add_argument(
        "--start-folio", "-sf",
        type=int,
        default=1,
        help="Erste Folio-Nummer für fw[@type='folNum']/@n (Standard: 1)",
    )
    args = parser.parse_args()

    SOURCE_DIR = args.input
    if args.output is not None:
        OUTPUT = args.output
    else:
        OUTPUT = Path("data/tei") / f"{SOURCE_DIR.name}.xml"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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

    # <profileDesc>
    profileDesc = etree.SubElement(tei_header, tei("profileDesc"))
    langUsage = etree.SubElement(profileDesc, tei("langUsage"))
    etree.SubElement(langUsage, tei("language"), ident="ita")

    # --- Ende TEI-Header ---

    text = etree.SubElement(tei_root, tei("text"))
    body = etree.SubElement(text, tei("body"))
    facs = etree.SubElement(tei_root, tei("facsimile"))

    # Page-State hier initialisieren
    page_state = {
        "line_no": 0,
        "after_pb": False,
        "current_pb": None,
        "table_y_ranges": [],   # wird pro Seite im Loop gesetzt
    }

    xml_files = sorted(SOURCE_DIR.glob("*.xml"))
    if not xml_files:
        print(f"Keine XML-Dateien in {SOURCE_DIR}")
        return

    folio_no = args.start_folio

    current_chapter = None
    heading_open = False
    heading_head = None
    in_chapter_body = False

    for pageno, xml_path in enumerate(xml_files, start=1):
        try:
            root = etree.parse(str(xml_path)).getroot()
        except Exception as e:
            print(f"Übersprungen: {xml_path.name} ({e})")
            continue

        table_y_ranges = []
        for t in root.findall(".//{*}TableRegion"):
            coords_el = t.find(".//{*}Coords")
            if coords_el is None or not coords_el.get("points"):
                continue
            pts, bbox = parse_points(coords_el.get("points"))
            if not pts:
                continue
            ys = [p[1] for p in pts]
            y_min, y_max = min(ys), max(ys)
            table_y_ranges.append((y_min, y_max))

        # Page-State für diese Seite aktualisieren
        page_state["table_y_ranges"] = table_y_ranges

        page_fw_headers = []  # Liste von <fw> für diese Seite

        page_el = first(root, ".//{*}Page")
        page_id = f"s{pageno:03d}"

        # facsimile/surface + graphic
        surface = etree.SubElement(facs, tei("surface"))
        surface.set(XML_ID, page_id)
        img = page_el.get("imageFilename") if page_el is not None else None
        if img:
            g = etree.SubElement(surface, tei("graphic"))
            g.set("url", img)

        pb_parent = current_chapter if current_chapter is not None else body

        if len(pb_parent) > 0:
         # Es gibt schon Elemente → der Zeilenumbruch kommt in die tail des letzten Elements
            last = pb_parent[-1]
            last.tail = (last.tail or "") + "\n\n"
        else:
            # Kein Kind vorhanden → der Zeilenumbruch kommt in die .text des Parents
            pb_parent.text = (pb_parent.text or "") + "\n\n"

        pb = etree.SubElement(pb_parent, tei("pb"))
        pb.set("n", str(pageno))
        pb.set("facs", f"#{page_id}")

        page_state["line_no"] = 0
        page_state["after_pb"] = True
        page_state["current_pb"] = pb
        

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
        last_paragraph = None
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

            # Ziel-Eltern für alles, was zum Kapitel gehört
            chapter_parent = current_chapter if current_chapter is not None else body

            # 1) Laufkopf (fw type="header")
            if rtype_lc == "header":
                fw = add_fw(chapter_parent, zone_id, region_el, rtype_lc)
                # aus Parent entfernen, wir verankern erst am Seitenende
                parent_fw = fw.getparent()
                if parent_fw is not None:
                    parent_fw.remove(fw)
                page_fw_headers.append(fw)
                continue

            # 2) Seitenzahl: TextRegion type="page-number" → ebenfalls puffern
            if rtype_lc == "page-number":
                fw = add_fw(chapter_parent, zone_id, region_el, rtype_lc)
                fw.set("n", str(folio_no))
                folio_no += 1
                parent_fw = fw.getparent()
                if parent_fw is not None:
                    parent_fw.remove(fw)
                page_fw_headers.append(fw)
                continue

            # 2) Kapitelüberschriften (heading)
            if rtype_lc == "heading":
                if not heading_open:
                    # Neue Heading-Gruppe → neues Kapitel ab *dieser* Heading
                    current_chapter = etree.SubElement(body, tei("div"))
                    current_chapter.set("type", "chapter")
                    chapter_parent = current_chapter  # für Vollständigkeit
                    in_chapter_body = False

                    # neues <head> für diese Gruppe
                    heading_head = etree.SubElement(current_chapter, tei("head"))
                    heading_head.set("facs", f"#{zone_id}")
                    heading_open = True
                else:
                    # weitere heading derselben Gruppe → ins gleiche <head>
                    old_facs = heading_head.get("facs", "")
                    heading_head.set("facs", (old_facs + " " + f"#{zone_id}").strip())

                add_heading_lines(heading_head, region_el, page_state)
                page_state["after_pb"] = False
                continue

            # Ab hier: keine heading → wir sind im Kapitelkörper (falls Kapitel existiert)
            if heading_open:
                heading_open = False  # Heading-Gruppe ist beendet

            # 3) Marginalien: Seitezahl, Kustode, Bogensignatur
            if rtype_lc in {"catch_word", "catch-word", "signature-mark"}:
                target = last_paragraph if last_paragraph is not None else chapter_parent

                # für Lesbarkeit: neue Zeile vor dem Marginal-fw, falls im Absatz
                if target is last_paragraph:
                    if len(target):
                        last_child = target[-1]
                        last_child.tail = (last_child.tail or "") + "\n"
                    else:
                        target.text = (target.text or "") + "\n"

                add_fw(target, zone_id, region_el, rtype_lc)
                continue

            # 4) Grafiken / Tabellen
            if "graphic" in region_el.tag.lower() or default_type in {"graphic", "table"}:
                target = last_paragraph if last_paragraph is not None else chapter_parent

                if target is last_paragraph:
                    if len(target):
                        last_child = target[-1]
                        last_child.tail = (last_child.tail or "") + "\n"
                    else:
                        target.text = (target.text or "") + "\n"

                fig_type = "table" if default_type == "table" else "graphic"
                add_figure(target, zone_id, region_el, fig_type=fig_type)
                continue

            if default_type == "music":
                target = last_paragraph if last_paragraph is not None else chapter_parent

                if target is last_paragraph:
                    if len(target):
                        last_child = target[-1]
                        last_child.tail = (last_child.tail or "") + "\n"
                    else:
                        target.text = (target.text or "") + "\n"

                add_music(target, zone_id, region_el)
                continue

            

            p = add_paragraph(chapter_parent, zone_id, region_el, page_state, merge_into_prev=False)
            last_paragraph = p
            page_state["after_pb"] = False
            if current_chapter is not None:
                in_chapter_body = True
        
        # --- Ende dieser Seite: header/folNum direkt hinter das pb dieser Seite setzen ---
        pb_el = page_state.get("current_pb")
        if pb_el is not None and page_fw_headers:
            pb_parent = pb_el.getparent()
            if pb_parent is not None:
                siblings = list(pb_parent)
                try:
                    idx_pb = siblings.index(pb_el)
                except ValueError:
                    idx_pb = -1

                if idx_pb != -1:
                    # In der Reihenfolge der Liste hintereinander einfügen
                    insert_pos = idx_pb + 1
                    for fw in page_fw_headers:
                        pb_parent.insert(insert_pos, fw)
                        # Zeilenumbrüche für Lesbarkeit
                        if insert_pos == idx_pb + 1:
                            pb_el.tail = (pb_el.tail or "") + "\n"
                        fw.tail = (fw.tail or "") + "\n"
                        insert_pos += 1

    # leere DIVs entfernen
    for div in body.findall(".//{*}div[@type='section']"):
        if len(div) == 0:  # keine Kindelemente
            div.getparent().remove(div)


    if UNUSUAL:
        hdr = tei_root.find("./{*}teiHeader")
        enc = hdr.find("./{*}encodingDesc") if hdr is not None else None
        if enc is None and hdr is not None:
            enc = etree.SubElement(hdr, tei("encodingDesc"))

        chdecl = enc.find("./{*}charDecl") if enc is not None else None
        if chdecl is None and enc is not None:
            chdecl = etree.SubElement(enc, tei("charDecl"))

        if chdecl is not None:
            for ch, cnt in sorted(UNUSUAL.items(), key=lambda kv: (-kv[1], ord(kv[0]))):
                cp = f"U+{ord(ch):04X}"
                try:
                    uname = unicodedata.name(ch)
                except ValueError:
                    uname = "UNNAMED"

                char_el = etree.SubElement(chdecl, tei("char"))
                char_el.set(XML_ID, f"char-{ord(ch):04X}")

                # Name, Codepoint, Häufigkeit
                etree.SubElement(
                    char_el, tei("localProp"),
                    name="name", value=uname
                )
                etree.SubElement(
                    char_el, tei("localProp"),
                    name="codepoint", value=cp
                )
                etree.SubElement(
                    char_el, tei("localProp"),
                    name="frequency", value=str(cnt)
                )

                # mapping: standard = Originalzeichen
                etree.SubElement(
                    char_el, tei("mapping"),
                    type="standard"
                ).text = ch

                # mapping: base = Grundbuchstabe, falls bestimmbar
                base = base_mapping(ch)
                if base is not None:
                    etree.SubElement(
                        char_el, tei("mapping"),
                        type="base"
                    ).text = base

    tree = etree.ElementTree(tei_root)
    tree.write(str(OUTPUT), encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"OK: {OUTPUT}")

if __name__ == "__main__":
    main()