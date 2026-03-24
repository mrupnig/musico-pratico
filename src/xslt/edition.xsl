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

                        /* =================================
                        MEI TRIGGER (SVG-Vorschau)
                        ================================= */

                        .mei-trigger {{
                        display: block;
                        cursor: pointer;
                        margin: 1rem 0;
                        }}

                        .mei-preview-svg {{
                        width: 100%;
                        min-height: 40px;
                        }}

                        .mei-preview-svg svg {{
                        width: 100%;
                        height: auto;
                        display: block;
                        transition: opacity 0.15s, outline 0.15s;
                        }}

                        .mei-trigger:hover .mei-preview-svg svg {{
                        opacity: 0.88;
                        outline: 2px solid #5c9d5c;
                        outline-offset: 2px;
                        }}

                        .mei-preview-loading {{
                        font-size: 0.8rem;
                        color: #aaa;
                        padding: 0.5rem 0;
                        }}

                        .mei-trigger-label {{
                        font-size: 0.75rem;
                        color: #5c9d5c;
                        text-align: center;
                        margin-top: 0.3rem;
                        }}

                        /* =================================
                        MEI MODAL
                        ================================= */

                        #mei-modal {{
                        position: fixed;
                        inset: 0;
                        z-index: 1000;
                        display: flex;
                        align-items: flex-start;
                        justify-content: center;
                        padding: 2rem;
                        background: rgba(0,0,0,0.65);
                        overflow-y: auto;
                        }}

                        #mei-modal[hidden] {{
                        display: none;
                        }}

                        #mei-modal-content {{
                        background: #fff;
                        border-radius: 0.6rem;
                        padding: 2rem 2.5rem;
                        width: 100%;
                        max-width: 1400px;
                        position: relative;
                        box-shadow: 0 0.5rem 2rem rgba(0,0,0,0.3);
                        }}

                        #mei-modal-close {{
                        position: absolute;
                        top: 0.75rem;
                        right: 1rem;
                        font-size: 1.8rem;
                        line-height: 1;
                        background: none;
                        border: none;
                        cursor: pointer;
                        color: #888;
                        padding: 0;
                        }}

                        #mei-modal-close:hover {{
                        color: #222;
                        }}

                        #mei-modal-render svg {{
                        width: 100%;
                        height: auto;
                        display: block;
                        }}

                        #mei-modal-render midi-player {{
                        margin-top: 1rem;
                        display: block;
                        }}

                        g.note.playing {{
                        fill: crimson;
                        }}

                        /* =================================
                        TRACK CONTROLS
                        ================================= */

                        #mei-track-controls {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 0.5rem 1rem;
                        align-items: center;
                        padding: 0.6rem 0.8rem;
                        margin-bottom: 1rem;
                        background: #f4f4f6;
                        border-radius: 0.4rem;
                        font-size: 0.85rem;
                        }}

                        #mei-track-controls:empty {{
                        display: none;
                        }}

                        .track-label {{
                        font-weight: 600;
                        color: #555;
                        }}

                        .track-checkbox {{
                        display: flex;
                        align-items: center;
                        gap: 0.3rem;
                        cursor: pointer;
                        user-select: none;
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
                        let highlightFrame = null;
                        let currentMeiText = null;

                        // ── Toolkit: einmalige Initialisierung, dann Vorschau-SVGs rendern ──
                        const tkReady = new Promise(resolve => {{
                            document.addEventListener("DOMContentLoaded", () => {{
                                verovio.module.onRuntimeInitialized = () => {{
                                    const tk = new verovio.toolkit();
                                    resolve(tk);
                                    renderAllPreviews(tk);
                                }};
                            }});
                        }});

                        // ── Vorschau-SVGs ──
                        async function renderAllPreviews(tk) {{
                            for (const trigger of document.querySelectorAll('.mei-trigger')) {{
                                await renderPreview(tk, trigger);
                            }}
                        }}

                        async function renderPreview(tk, trigger) {{
                            const meiFile = trigger.dataset.mei;
                            const url = `https://raw.githubusercontent.com/fabianmoss/pontio-examples/main/examples/${{meiFile}}`;
                            try {{
                                const resp = await fetch(url);
                                if (!resp.ok) return;
                                const meiText = await resp.text();
                                const width = Math.max(100, Math.round(trigger.clientWidth * 2.5));
                                tk.setOptions({{ scale: 40, pageWidth: width, adjustPageHeight: true, breaks: "auto" }});
                                tk.loadData(meiText);
                                let html = tk.renderToSVG(1);
                                const pageCount = tk.getPageCount();
                                for (let p = 2; p &lt;= pageCount; p++) {{ html += tk.renderToSVG(p); }}
                                const previewDiv = trigger.querySelector('.mei-preview-svg');
                                if (previewDiv) previewDiv.innerHTML = html;
                            }} catch (e) {{
                                console.warn(`Vorschau für ${{meiFile}} fehlgeschlagen:`, e);
                            }}
                        }}

                        // ── MEI-Hilfsfunktionen ──
                        function extractStaves(meiText) {{
                            const doc = new DOMParser().parseFromString(meiText, 'application/xml');
                            const ns = 'http://www.music-encoding.org/ns/mei';
                            return [...doc.getElementsByTagNameNS(ns, 'staffDef')].map(def => ({{
                                n:     def.getAttribute('n'),
                                label: def.getAttribute('label') || `Stimme ${{def.getAttribute('n')}}`
                            }}));
                        }}

                        function applyStaffFilter(meiText, hiddenStaves) {{
                            if (hiddenStaves.size === 0) return meiText;
                            const doc = new DOMParser().parseFromString(meiText, 'application/xml');
                            const ns = 'http://www.music-encoding.org/ns/mei';
                            for (const el of [...doc.getElementsByTagNameNS(ns, 'staffDef')]) {{
                                if (hiddenStaves.has(el.getAttribute('n'))) el.parentNode.removeChild(el);
                            }}
                            for (const el of [...doc.getElementsByTagNameNS(ns, 'staff')]) {{
                                if (hiddenStaves.has(el.getAttribute('n'))) el.parentNode.removeChild(el);
                            }}
                            return new XMLSerializer().serializeToString(doc);
                        }}

                        // ── Modal-Rendering ──
                        async function renderMeiInModal(tk, meiText) {{
                            if (highlightFrame) {{ cancelAnimationFrame(highlightFrame); highlightFrame = null; }}
                            const renderDiv = document.getElementById('mei-modal-render');
                            const width = Math.max(100, Math.round(
                                document.getElementById('mei-modal-content').clientWidth * 2.5
                            ));
                            tk.setOptions({{ scale: 40, pageWidth: width, adjustPageHeight: true, breaks: "auto" }});
                            tk.loadData(meiText);
                            let html = tk.renderToSVG(1);
                            const pageCount = tk.getPageCount();
                            for (let p = 2; p &lt;= pageCount; p++) {{ html += tk.renderToSVG(p); }}
                            renderDiv.innerHTML = html;
                            const midiBase64 = tk.renderToMIDI();
                            if (midiBase64) {{
                                const player = document.createElement('midi-player');
                                player.setAttribute('src', `data:audio/midi;base64,${{midiBase64}}`);
                                player.setAttribute('sound-font', 'https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus');
                                renderDiv.appendChild(player);
                                startHighlighting(tk, player, renderDiv);
                            }}
                        }}

                        function renderTrackControls(staves) {{
                            const container = document.getElementById('mei-track-controls');
                            if (staves.length &lt;= 1) {{ container.innerHTML = ''; return; }}
                            let html = '&lt;span class="track-label"&gt;Stimmen:&lt;/span&gt;';
                            for (const s of staves) {{
                                html += `&lt;label class="track-checkbox"&gt;&lt;input type="checkbox" checked data-staff="${{s.n}}"&gt; ${{s.label}}&lt;/label&gt;`;
                            }}
                            container.innerHTML = html;
                            container.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
                                cb.addEventListener('change', async () => {{
                                    const hidden = new Set(
                                        [...container.querySelectorAll('input[type="checkbox"]:not(:checked)')].map(i => i.dataset.staff)
                                    );
                                    const tk = await tkReady;
                                    await renderMeiInModal(tk, applyStaffFilter(currentMeiText, hidden));
                                }});
                            }});
                        }}

                        // ── Klick-Handler &amp; Modal ──
                        document.addEventListener("DOMContentLoaded", () => {{
                            document.querySelectorAll('.mei-trigger').forEach(trigger => {{
                                trigger.addEventListener('click', () => openModal(trigger.dataset.mei));
                            }});
                            const modal = document.getElementById('mei-modal');
                            document.getElementById('mei-modal-close').addEventListener('click', closeModal);
                            modal.addEventListener('click', e => {{ if (e.target === modal) closeModal(); }});
                            document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});
                        }});

                        function closeModal() {{
                            if (highlightFrame) {{ cancelAnimationFrame(highlightFrame); highlightFrame = null; }}
                            document.getElementById('mei-modal').setAttribute('hidden', '');
                            document.body.style.overflow = '';
                            document.getElementById('mei-modal-render').innerHTML = '';
                            document.getElementById('mei-track-controls').innerHTML = '';
                            currentMeiText = null;
                        }}

                        async function openModal(meiFile) {{
                            const modal     = document.getElementById('mei-modal');
                            const renderDiv = document.getElementById('mei-modal-render');
                            renderDiv.innerHTML = '&lt;p style="padding:1rem;color:#666"&gt;Wird geladen …&lt;/p&gt;';
                            document.getElementById('mei-track-controls').innerHTML = '';
                            modal.removeAttribute('hidden');
                            document.body.style.overflow = 'hidden';
                            try {{
                                const tk  = await tkReady;
                                const url = `https://raw.githubusercontent.com/fabianmoss/pontio-examples/main/examples/${{meiFile}}`;
                                const resp = await fetch(url);
                                if (!resp.ok) throw new Error(`HTTP ${{resp.status}}`);
                                currentMeiText = await resp.text();
                                renderTrackControls(extractStaves(currentMeiText));
                                await renderMeiInModal(tk, currentMeiText);
                            }} catch (e) {{
                                console.error('MEI konnte nicht geladen werden:', e);
                                renderDiv.textContent = `Fehler beim Laden von ${{meiFile}}: ${{e.message}}`;
                            }}
                        }}

                        function startHighlighting(tk, player, renderDiv) {{
                            function step() {{
                                if (player.playing) {{
                                    const timeMs = player.currentTime * 1000;
                                    const elements = tk.getElementsAtTime(timeMs);
                                    renderDiv.querySelectorAll('g.note.playing').forEach(n => n.classList.remove('playing'));
                                    if (elements &amp;&amp; elements.notes) {{
                                        for (const noteId of elements.notes) {{
                                            const el = renderDiv.querySelector(`#${{noteId}}`);
                                            if (el) el.classList.add('playing');
                                        }}
                                    }}
                                }}
                                highlightFrame = requestAnimationFrame(step);
                            }}
                            highlightFrame = requestAnimationFrame(step);
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

                <!-- MEI Modal -->
                <div id="mei-modal" hidden="">
                    <div id="mei-modal-content">
                        <button id="mei-modal-close" aria-label="Schließen">&#215;</button>
                        <div id="mei-track-controls"/>
                        <div id="mei-modal-render"/>
                    </div>
                </div>

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
        <div class="mei-trigger" data-mei="{@mei}.mei">
            <div class="mei-preview-svg">
                <span class="mei-preview-loading">Notenbeispiel wird geladen …</span>
            </div>
            <div class="mei-trigger-label">&#9835; Zum Abspielen klicken</div>
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
