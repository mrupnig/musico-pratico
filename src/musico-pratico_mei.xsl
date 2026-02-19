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
                        max-width: 1100px;
                        margin: 0 auto;
                        padding: 1rem 2rem;
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
                        width: 100%;
                        margin-bottom: 2rem;
                        padding: 1.2rem 1.6rem;
                        background: #fff;
                        border-radius: 0.6rem;
                        box-shadow: 0 0.15rem 0.4rem rgba(0,0,0,0.08);
                        border-left: 4px solid #ccc;
                        }}

                        .page-main-full {{
                        width: 100%;
                        max-width: 100%;
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

                        /* =================================
                        MEI LAYOUT
                        ================================= */

                        .mei-panel {{
                        border: 1px solid lightgray;
                        min-height: 800px;
                        width: 100%;
                        overflow: auto;
                        margin: 1.5rem 0;
                        }}

                        
                    </xsl:text>
                </style>
                <script type="module">
                    <xsl:text>
                        import 'https://editor.verovio.org/javascript/app/verovio-app.js';

                        /**
                        * Lädt eine MEI‑Datei und rendert sie im übergebenen DIV.
                        */
                        async function renderMei(container) {{
                            const fileName = container.dataset.mei;       
                            const url      = `mei/${{fileName}}`;   

                            try {{
                                const resp = await fetch(url);
                                if (!resp.ok) throw new Error(`HTTP ${{resp.status}}`);

                                const meiText = await resp.text();

                                // Verovio‑Instanz anlegen.
                                // hideControls:true entfernt den Browse‑Button und das Lade‑Overlay.
                                const app = new Verovio.App(container, {{
                                    hideControls: true,     
                                    scale: 40, 
                                    pageHeight: 800,
                                    pageWidth: 600
                                }});

                                // Daten einspielen und rendern
                                app.loadData(meiText);
                            }} catch (e) {{
                                console.error('MEI‑Datei konnte nicht geladen werden:', e);
                                container.textContent = `Fehler beim Laden von ${{url}}`;
                            }}
                        }}

                        // Alle DIVs mit dem data‑mei‑Attribut automatisch rendern
                        document.querySelectorAll('[data-mei]').forEach(renderMei);
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
                select=".//tei:pb | .//tei:head | .//tei:p | .//tei:fw"
                group-starting-with="tei:pb">
                
                <xsl:variable name="pb" select="current-group()[1]"/>
                <xsl:variable name="page-id"
                    select="substring-after($pb/@facs, '#')"/>
                
                <div class="page-block page-fullwidth" id="page-{$page-id}">
                    
                    <div class="page-main-full">
                        
                        <hr class="pb"
                            data-page="{$pb/@n}"
                            data-facs="{$pb/@facs}"/>
                        
                        <!-- Alles in Dokumentreihenfolge -->
                        <xsl:apply-templates
                            select="current-group()[position() gt 1
                                    and not(self::tei:fw[@type=('sig','catch')])]"/>
                        
                        <!-- sig + catch unten -->
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
                    
                </div>
                
            </xsl:for-each-group>
        </div>
        
    </xsl:template>

    
    <!-- ========================================================= -->
    <!-- STRUKTUR-ELEMENTE                                         -->
    <!-- ========================================================= -->
    <xsl:template match="tei:notatedMusic">
        
        <div class="element-box element-music">
            
            <div class="element-header">
                <span class="icon-music">&#9835;</span>
                Notierte Musik
            </div>
        </div>
        <div class="mei-panel"
             data-mei="{substring-after(@source,'#')}.mei">
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
