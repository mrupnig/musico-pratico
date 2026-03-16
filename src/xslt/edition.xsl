<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    expand-text="yes">
    
    <xsl:output method="html" html-version="5" indent="yes"/>
    <xsl:strip-space elements="*"/>
    
    <!-- ========================================================= -->
    <!-- KEY: Elemente einer Seite über @facs zuordnen             -->
    <!-- z.B. #z-s033-r8  →  s033                                   -->
    <!-- ========================================================= -->
    <xsl:key name="by-page"
        match="tei:notatedMusic 
            | tei:figure[@type=('graphic','table')]"
        use="substring-before(substring-after(@facs, '#z-'), '-r')"/>
    
    <!-- ========================================================= -->
    <!-- ROOT                                                      -->
    <!-- ========================================================= -->
    <xsl:template match="/tei:TEI">
        <html lang="it">
            <head>
                <meta charset="UTF-8"/>
                <title>
                    {tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[@type='main']}
                </title>
                <style>
                    <xsl:text>
                        
                        /* =================================
                        LAYOUT
                        ================================= */
                        
                        body {{
                        width: 100%;
                        margin: 0;
                        padding: 1.5rem 3rem;
                        font-family: system-ui, sans-serif;
                        background: #f8f8fb;
                        line-height: 1.4;
                        }}

                        
                        header.tei-header {{
                        margin-bottom: 2rem;
                        border-bottom: 2px solid #ccc;
                        padding-bottom: 0.5rem;
                        }}
                        
                        header.tei-header h1 {{
                        margin: 0 0 0.25rem;
                        }}
                        
                        header.tei-header .author {{
                        margin: 0;
                        font-style: italic;
                        color: #555;
                        }}
                        
                        
                        /* =================================
                        PAGE OVERVIEW
                        ================================= */
                        
                        #page-overview {{
                        margin-bottom: 2.5rem;
                        padding: 1rem;
                        background: #fff;
                        border-radius: 0.5rem;
                        box-shadow: 0 0.1rem 0.3rem rgba(0,0,0,0.08);
                        }}
                        
                        .page-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(5rem, 1fr));
                        gap: 0.4rem;
                        }}
                        
                        .page-cell-link {{
                        text-decoration: none;
                        color: inherit;
                        display: block;
                        }}
                        
                        .page-cell {{
                        border: 1px solid #ddd;
                        border-radius: 0.35rem;
                        padding: 0.25rem 0.35rem;
                        font-size: 0.8rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        background: #fafafa;
                        cursor: pointer;
                        }}
                        
                        .page-cell.has-music {{
                        border-color: #5c9d5c;
                        background: #eef9ee;
                        }}
                        
                        .page-cell.has-table {{
                        border-color: #4f6fae;
                        background: #edf2fb;
                        }}
                        
                        .page-cell.has-graphic {{
                        border-color: #b87b2c;
                        background: #fff4e0;
                        }}
                        
                        .page-icons {{
                        display: flex;
                        gap: 0.25rem;
                        }}
                        
                        /* =================================
                        PAGE BLOCKS
                        ================================= */

                        #edition {{
                        margin-top: 2rem;
                        }}

                        .page-block {{
                        max-width: 850px;
                        margin-left: auto;
                        margin-right: auto;
                        margin-bottom: 4rem;
                        padding: 2rem 3rem;
                        background: #fff;
                        border-radius: 0.6rem;
                        box-shadow: 0 0.15rem 0.4rem rgba(0,0,0,0.08);
                        border-left: 4px solid #ccc;
                        }}

                        .mei-panel {{
                        width: 100%;
                        margin: 1rem 0;
                        overflow: hidden;
                        }}

                        .mei-panel svg {{
                        width: 100%;
                        height: auto;
                        display: block;
                        }}

                        
                        /* =================================
                        INLINE ELEMENT BOXES
                        ================================= */

                        .element-box {{
                        margin: 1.4rem 0;
                        padding: 0.8rem 1rem;
                        border-radius: 0.6rem;
                        border: 1px solid #ddd;
                        background: #fafafa;
                        }}

                        .element-header {{
                        font-size: 0.85rem;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                        display: flex;
                        align-items: center;
                        gap: 0.4rem;
                        }}

                        .element-music {{
                        border-color: #5c9d5c;
                        background: #eef9ee;
                        }}

                        .element-table {{
                        border-color: #4f6fae;
                        background: #edf2fb;
                        }}

                        .element-graphic {{
                        border-color: #b87b2c;
                        background: #fff4e0;
                        }}
                        
                        /* =================================
                        PAGE BREAK
                        ================================= */
                        
                        hr.pb {{
                        border: none;
                        border-top: 3px solid #b0b0b0;
                        margin: 0 0 0.8rem;
                        position: relative;
                        }}
                        
                        hr.pb::before {{
                        content: "Seite " attr(data-page);
                        position: absolute;
                        top: -1.3rem;
                        left: 0;
                        font-size: 0.8rem;
                        font-weight: 600;
                        color: #555;
                        }}
                        
                        br.lb[data-n]::after {{
                        content: attr(data-n);
                        font-size: 0.6rem;
                        color: #aaa;
                        vertical-align: super;
                        margin-left: 0.2rem;
                        }}
                        
                        
                        /* =================================
                        FW LAYOUT
                        ================================= */
                        
                        .fw-header-folnum {{
                        display: flex;
                        justify-content: space-between;
                        border-bottom: 1px solid #ddd;
                        margin-bottom: 0.4rem;
                        font-size: 0.75rem;
                        }}
                        
                        .fw-sig-catch {{
                        display: flex;
                        margin-top: 0.8rem;
                        font-size: 0.75rem;
                        }}
                        
                        .fw-sig {{
                        flex: 1;
                        text-align: center;
                        font-style: italic;
                        }}
                        
                        .fw-catch {{
                        flex: 1;
                        text-align: right;
                        font-style: italic;
                        }}

                    </xsl:text>
                </style>
                
                
                <script src="https://www.verovio.org/javascript/latest/verovio-toolkit-wasm.js" defer="defer"/>
                <script src="https://cdn.jsdelivr.net/combine/npm/tone@14.7.58,npm/@magenta/music@1.23.1/es6/core.js,npm/html-midi-player@1.5.0" defer="defer"/>
                <script>
                    <xsl:text>
                        document.addEventListener("DOMContentLoaded", () => {{
                            verovio.module.onRuntimeInitialized = async () => {{
                                const tk = new verovio.toolkit();
                                const containers = document.querySelectorAll('[data-mei]');
                                for (const container of containers) {{
                                    await renderMei(tk, container);
                                }}
                            }};
                        }});

                        async function renderMei(tk, container) {{
                            const fileName = container.dataset.mei;
                            const url = `https://raw.githubusercontent.com/fabianmoss/pontio-examples/main/examples/${{fileName}}`;
                            const scale = parseInt(container.dataset.scale || "40");
                            const width = Math.max(100, Math.round(container.clientWidth * 2.5));

                            try {{
                                const resp = await fetch(url);
                                if (!resp.ok) throw new Error(`HTTP ${{resp.status}}`);
                                const meiText = await resp.text();

                                tk.setOptions({{
                                    scale: scale,
                                    pageWidth: width,
                                    adjustPageHeight: true,
                                    breaks: "auto"
                                }});

                                tk.loadData(meiText);
                                container.innerHTML = tk.renderToSVG(1);

                                const pageCount = tk.getPageCount();
                                for (let p = 2; p &lt;= pageCount; p++) {{
                                    container.innerHTML += tk.renderToSVG(p);
                                }}

                                const midiBase64 = tk.renderToMIDI();
                                if (midiBase64) {{
                                    const player = document.createElement('midi-player');
                                    player.setAttribute('src', `data:audio/midi;base64,${{midiBase64}}`);
                                    player.setAttribute('sound-font', 'https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
                                    container.appendChild(player);
                                }}
                            }} catch (e) {{
                                console.error('MEI konnte nicht geladen werden:', e);
                                container.textContent = `Fehler beim Laden von ${{fileName}}: ${{e.message}}`;
                            }}
                        }}
                    </xsl:text>
                </script>
                
            </head>
            
            
            <body>
                
                <!-- Titelbereich -->
                <header class="tei-header">
                    <h1>
                        {tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[@type='main']}
                    </h1>
                    <p class="author">
                        {tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author/tei:persName/tei:forename}
                        {tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author/tei:persName/tei:surname}
                    </p>
                </header>
                
                <!-- Seitenübersicht -->
                <xsl:call-template name="page-overview"/>
                
                <!-- Edition -->
                <section id="edition">
                    <xsl:apply-templates select="tei:text/tei:body"/>
                </section>
                
            </body>
        </html>
    </xsl:template>
    
    <!-- ========================================================= -->
    <!-- SEITENÜBERSICHT (klickbar)                                -->
    <!-- ========================================================= -->
    <xsl:template name="page-overview">
        <section id="page-overview">
            <h2>Page overview</h2>
            
            <div class="page-grid">
                <xsl:for-each select="tei:facsimile/tei:surface">
                    
                    <xsl:variable name="id" select="@xml:id"/>
                    <xsl:variable name="pbn"
                        select="/tei:TEI//tei:pb[@facs = '#' || $id][1]/@n"/>
                    
                    <a href="#page-{$id}" class="page-cell-link">
                        <div class="page-cell
                                    {if (tei:zone[@type='music']) then ' has-music' else ''}
                                {if (tei:zone[@type='table']) then ' has-table' else ''}
                                {if (tei:zone[@type='graphic']) then ' has-graphic' else ''}">
                            
                            <span class="page-label">
                                S.{if ($pbn) then $pbn else $id}
                            </span>
                            
                            <span class="page-icons">
                                <xsl:if test="tei:zone[@type='music']">
                                    <span class="icon-music">&#9835;</span>
                                </xsl:if>
                                <xsl:if test="tei:zone[@type='table']">
                                    <span class="icon-table">&#9633;</span>
                                </xsl:if>
                                <xsl:if test="tei:zone[@type='graphic']">
                                    <span class="icon-graphic">&#128444;</span>
                                </xsl:if>
                            </span>
                            
                        </div>
                    </a>
                    
                </xsl:for-each>
            </div>
        </section>
    </xsl:template>
    
    <!-- ========================================================= -->
    <!-- BODY → seitenweise gruppieren                             -->
    <!-- ========================================================= -->
    <xsl:template match="tei:body">
        
        <div class="body">
            
            <xsl:for-each-group
                select="tei:pb | tei:head | tei:p | tei:fw
                      | tei:div[@type='chapter']/(tei:pb | tei:head | tei:p | tei:fw)"
                group-starting-with="tei:pb">
                
                <xsl:variable name="pb" select="current-group()[1]"/>
                <xsl:variable name="page-id"
                    select="substring-after($pb/@facs, '#')"/>
                
                <div class="page-block" id="page-{$page-id}">

                    <hr class="pb"
                        data-page="{$pb/@n}"
                        data-facs="{$pb/@facs}"/>

                    <xsl:apply-templates
                        select="current-group()[position() gt 1
                                and not(self::tei:fw[@type=('sig','catch')])]"/>

                    <!-- sig + catch -->
                    <xsl:variable name="sig"
                        select="current-group()[self::tei:fw[@type='sig']][1]"/>
                    <xsl:variable name="catch"
                        select="current-group()[self::tei:fw[@type='catch']][1]"/>

                    <xsl:if test="$sig or $catch">
                        <div class="fw-line fw-sig-catch">
                            <span class="fw fw-sig">
                                <xsl:value-of select="$sig"/>
                            </span>
                            <span class="fw fw-catch">
                                <xsl:value-of select="$catch"/>
                            </span>
                        </div>
                    </xsl:if>

                </div>
                
            </xsl:for-each-group>
            
        </div>
        
    </xsl:template>
    
    
    <!-- ========================================================= -->
    <!-- STRUKTUR-ELEMENTE                                         -->
    <!-- ========================================================= -->
    <xsl:template match="tei:notatedMusic[@mei]">
        <div class="page-block">
            <div class="mei-panel" data-mei="{@mei}.mei"/>
        </div>
    </xsl:template>

    <xsl:template match="tei:notatedMusic">
        <div class="element-box element-music">
            <div class="element-header">
                <span class="icon-music">&#9835;</span>
                Notierte Musik
            </div>
        </div>
    </xsl:template>
    
    <xsl:template match="tei:figure[@type='table']">
        
        <div class="element-box element-table">
            
            <div class="element-header">
                <span class="icon-table">&#9633;</span>
                Tabelle
            </div>
            
            <div class="figure-content"
                 data-facs="{substring-after(@facs,'#')}">
            </div>
            
        </div>
        
    </xsl:template>
    
    <xsl:template match="tei:figure[@type='graphic']">
        
        <div class="element-box element-graphic">
            
            <div class="element-header">
                <span class="icon-graphic">&#128444;</span>
                Grafik
            </div>
            
            <div class="figure-content"
                 data-facs="{substring-after(@facs,'#')}">
            </div>
            
        </div>
        
    </xsl:template>
    
    
    <xsl:template match="tei:p">
        <p><xsl:apply-templates/></p>
    </xsl:template>
    
    <xsl:template match="tei:head">
        <h2><xsl:apply-templates/></h2>
    </xsl:template>
    
    <xsl:template match="tei:lb">
        <br class="lb" data-n="{@n}"/>
    </xsl:template>
    
    <xsl:template match="tei:pb"/>
    
    <!-- header + folNum -->
    <xsl:template match="tei:fw[@type='header']">
        <div class="fw-line fw-header-folnum">
            <span class="fw fw-header"><xsl:apply-templates/></span>
            <span class="fw fw-folnum">
                <xsl:value-of select="following-sibling::tei:fw[@type='folNum'][1]"/>
            </span>
        </div>
    </xsl:template>
    
    <xsl:template match="tei:fw[@type='folNum']"/>
    
    <xsl:template match="tei:fw[@type='sig']"/>
    <xsl:template match="tei:fw[@type='catch']"/>
    
    <xsl:template match="tei:fw">
        <span class="fw"><xsl:apply-templates/></span>
    </xsl:template>
    
    
    <xsl:template match="text()">
        <xsl:value-of select="."/>
    </xsl:template>
    
</xsl:stylesheet>
