# Musico Pratico

A digital edition project for Pietro Pontio's *Ragionamento di musica* (1588), a Renaissance music theory treatise. The project provides tooling to convert transcribed PAGE XML files into TEI-encoded XML, and from there into an HTML edition via XSLT.

## Workflow

```
PAGE XML (OCR output)  →  TEI XML     →  HTML edition
    data/pages/           data/tei/      data/edition/
    (page2tei)            (XSLT)
```

1. **PAGE → TEI**: The `page2tei` script reads PAGE XML files produced by OCR4all, extracts text regions, headings, marginalia, figures, music regions, and geometry, and writes a single TEI XML document.
2. **TEI → HTML**: The XSLT stylesheets in `src/xslt/` transform the TEI output into a browsable HTML edition.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python ≥ 3.12

## Installation

```bash
git clone <repo-url>
cd musico-pratico
uv sync
```

`uv sync` installs all dependencies (including `lxml`) into an isolated virtual environment and makes the `page2tei` command available.

## Usage

### PAGE to TEI conversion

Run the converter with default paths (`data/pages/` → `data/tei/`):

```bash
uv run page2tei
```

To specify custom input and output paths:

```bash
uv run page2tei --input path/to/page-xml/ --output path/to/output/
# short form
uv run page2tei -i path/to/page-xml/ -o path/to/output/
```

| Option | Default | Description |
|---|---|---|
| `-i` / `--input` | `data/pages/` | Directory containing PAGE XML files |
| `-o` / `--output` | `data/tei/` | Output directory for the TEI XML file |

The script processes all `.xml` files in the input directory in alphabetical order and writes a single TEI file. Any characters outside the expected Latin/German alphabet are catalogued in a `<charDecl>` section of the TEI header for review.

### TEI to HTML

Apply the XSLT stylesheet using Saxon or a compatible XSLT 3.0 processor:

```bash
java -jar saxon.jar -s:data/tei/<file>.xml -xsl:src/xslt/edition.xsl -o:data/edition/edition.html
```

## Project structure

```
musico-pratico/
├── src/
│   ├── page2tei/
│   │   └── pageXML_to_TEI.py   # PAGE → TEI conversion script
│   └── xslt/
│       └── edition.xsl          # TEI → HTML (main edition)
├── data/
│   ├── pages/                   # input: PAGE XML files (not versioned)
│   ├── tei/                     # output: generated TEI XML (not versioned)
│   └── edition/                 # output: generated HTML (not versioned)
├── pyproject.toml
└── uv.lock
```

## Source material

Pietro Pontio: *Ragionamento di musica* (Parma, 1588).
GND: [https://d-nb.info/gnd/119000695](https://d-nb.info/gnd/119000695)
