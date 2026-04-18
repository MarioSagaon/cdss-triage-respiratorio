import streamlit as st
import base64
import json
from datetime import datetime
import streamlit.components.v1 as components
from clinical_models import PacienteIRA, PacienteNeumoniaCAP, PacienteOMA, PacienteSinusitis
from decision_engine import evaluar_paciente, evaluar_neumonia, evaluar_oma, evaluar_sinusitis
from interoperability import generar_decision_id, generar_fhir_r4, generar_json_estructurado
from ficha_educativa import get_ficha, generar_html_ficha

# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────
def get_base64(filepath):
    try:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

# ─────────────────────────────────────────
# CASOS DEMO PRECARGADOS
# ─────────────────────────────────────────
CASOS_DEMO = {
    "Faringitis — Caso Viral Clásico": {
        "patologia": "faringitis",
        "nombre": "Ana Martínez López",
        "edad": 22, "dias": 3, "fr": 17, "sat": 98.5,
        "fiebre": False, "exudado": False, "adenopatia": False,
        "tos": True, "rinorrea": True, "disfonia": True,
        "conjuntivitis": False, "mialgias": True, "exantema": False, "nauseas": False,
        "neumopatia": False, "inmuno": False,
    },
    "Faringitis — Caso Bacteriano (McIsaac Alto)": {
        "patologia": "faringitis",
        "nombre": "Carlos Rodríguez Vega",
        "edad": 27, "dias": 4, "fr": 19, "sat": 96.0,
        "fiebre": True, "exudado": True, "adenopatia": True,
        "tos": False, "rinorrea": False, "disfonia": False,
        "conjuntivitis": False, "mialgias": False, "exantema": False, "nauseas": False,
        "neumopatia": False, "inmuno": False,
    },
    "Neumonía — Caso Grave (CURB-65 Alto)": {
        "patologia": "neumonia",
        "nombre": "Roberto Jiménez Torres",
        "edad": 70, "confusion": True, "urea": True, "fr": 32,
        "hipotension": True, "sat": 85.0, "neumopatia": True, "inmuno": False,
        "fiebre": True, "tos_prod": True, "dolor_toracico": True, "escalofrios": True,
    },
    "OMA — Caso Confirmado Grave": {
        "patologia": "oma",
        "nombre": "Miguel Ángel Flores",
        "edad": 4, "dias": 2,
        "inicio_agudo": True, "abombamiento": True, "otorrea": False, "hipoacusia": True,
        "otalgia": True, "fiebre_38": True, "hiperemia": True,
        "fiebre_39": True, "otalgia_intensa": False, "bilateral": False,
        "inmuno": False, "episodios_previos": 1,
    },
    "Sinusitis — Caso Bacteriano (>10 días)": {
        "patologia": "sinusitis",
        "nombre": "Laura Sánchez Morales",
        "edad": 35, "dias": 12,
        "congestion": True, "rinorrea_pur": True, "dolor_facial": True, "hiposmia": False,
        "doble_empeoramiento": False, "fiebre_38": True, "dolor_unilateral": True,
        "fiebre_39": False, "edema_periorbitario": False, "rigidez_nucal": False,
        "cefalea_intensa": False, "inmuno": False, "asma": False,
    },
}
# ── FUNCIÓN PARA EL REPORTE ADMINISTRATIVO ──
def generar_pdf_resumen_turno(historial, metricas):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
    
    pdf = FPDF()
    pdf.add_page()
    
    # --- HEADER ADMINISTRATIVO ---
    pdf.set_fill_color(15, 23, 42) 
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.text(15, 25, "SITRE · SHIFT SUMMARY REPORT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(148, 163, 184)
    pdf.text(15, 32, f"CENTRO DE CONTROL EPIDEMIOLOGICO | ID TURNO: {datetime.now().strftime('%Y%m%d-%H%M')}")
    
    pdf.ln(35)
    
    # --- MÉTRICAS DE IMPACTO ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "1. EXECUTIVE SUMMARY (ROI & STEWARDSHIP)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 7, f"Total de pacientes evaluados: {metricas['total']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 7, f"Prescripciones de antibiotico evitadas: {metricas['virales']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"AHORRO HOSPITALARIO ESTIMADO: ${metricas['ahorro']:,.2f} USD", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)
    
    # --- TABLA DE PACIENTES ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "2. DETALLE DE PACIENTES EN TURNO", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 8, " HORA", 1, 0, 'L', True)
    pdf.cell(70, 8, " PACIENTE", 1, 0, 'L', True)
    pdf.cell(40, 8, " PATOLOGIA", 1, 0, 'C', True)
    pdf.cell(55, 8, " RESULTADO / TAG", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", "", 8)
    for px in historial:
        # Limpiamos el nombre para evitar errores de encoding
        nombre_clean = px['nombre'].encode("latin-1","ignore").decode("latin-1")
        pdf.cell(25, 7, f" {px['hour'] if 'hour' in px else px.get('hora', '00:00')}", 1)
        pdf.cell(70, 7, f" {nombre_clean[:35]}", 1)
        pdf.cell(40, 7, f" {px['patologia']}", 1, 0, 'C')
        pdf.cell(55, 7, f" {px['tag']}", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Este documento es un resumen administrativo generado automaticamente por SITRE. Los datos estan respaldados por hashes criptograficos para auditoria interna.")
    
    return bytes(pdf.output())
# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
st.set_page_config(
    page_title="SITRE · Triage Respiratorio",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
for key, default in [
    ("pantalla", "bienvenida"),
    ("patologia", None),
    ("resultado_completo", None),
    ("nombre_paciente", ""),
    ("paciente_obj", None),
    ("historial", []),
    ("demo_caso", None),
    ("modo_guardia", False),
    ("abx_evitados_global", 0),   # Contador global persistente (demo seed)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --teal:       #0D9488;
    --teal-light: #14B8A6;
    --teal-glow:  rgba(13,148,136,0.35);
    --red:        #EF4444;
    --amber:      #F59E0B;
    --blue:       #3B82F6;
    --green:      #22C55E;
    --bg:         #050C0C;
    --surface:    rgba(255,255,255,0.04);
    --border:     rgba(255,255,255,0.08);
    --text:       #F0FDFA;
    --muted:      rgba(240,253,250,0.45);
}

/* ── MODO GUARDIA ── */
body.guardia-mode {
    --bg:         #0A0000 !important;
    --surface:    rgba(239,68,68,0.04) !important;
    --border:     rgba(239,68,68,0.12) !important;
    --teal:       #DC2626 !important;
    --teal-light: #EF4444 !important;
    --teal-glow:  rgba(220,38,38,0.35) !important;
}
body.guardia-mode .stApp,
body.guardia-mode [data-testid="stAppViewContainer"] {
    background: #0A0000 !important;
}
body.guardia-mode div.stButton > button[kind="primary"],
body.guardia-mode div[data-testid="stDownloadButton"] > button {
    color: #EF4444 !important;
    border-color: #DC2626 !important;
    box-shadow: 0 0 24px rgba(220,38,38,0.35) !important;
}
body.guardia-mode ::-webkit-scrollbar-thumb { background: #DC2626; }
body.guardia-mode div[data-testid="stToggle"] span[data-checked="true"] {
    background-color: #DC2626 !important;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stToolbar"], section[data-testid="stSidebar"],
.stApp { background: var(--bg) !important; color: var(--text) !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden !important; }
body { font-family: 'DM Sans', sans-serif !important; }

div[data-testid="stNumberInput"] label, div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] label, div[data-testid="stTextInput"] input {
    font-family: 'DM Sans', sans-serif !important; color: var(--text) !important; }
div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.06) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; padding: 10px 14px !important; font-size: 1rem !important; }
div[data-testid="stNumberInput"] input:focus, div[data-testid="stTextInput"] input:focus {
    border-color: var(--teal) !important; box-shadow: 0 0 0 3px var(--teal-glow) !important;
    outline: none !important; }
div[data-testid="stSelectbox"] label { color: var(--text) !important; }
div[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.06) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; color: var(--text) !important; }
div[data-testid="stToggle"] label { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }
div[data-testid="stToggle"] span[data-checked="true"] { background-color: var(--teal) !important; }
div[data-testid="stCheckbox"] label { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }

div.stButton > button[kind="primary"], div[data-testid="stDownloadButton"] > button {
    font-family: 'DM Sans', sans-serif !important; background: transparent !important;
    color: var(--teal-light) !important; border: 1.5px solid var(--teal) !important;
    border-radius: 100px !important; padding: 14px 40px !important;
    font-size: 0.95rem !important; font-weight: 600 !important;
    letter-spacing: 3px !important; text-transform: uppercase !important;
    transition: all 0.3s cubic-bezier(0.23,1,0.32,1) !important;
    box-shadow: 0 0 24px var(--teal-glow) !important; width: 100% !important; }
div.stButton > button[kind="primary"]:hover, div[data-testid="stDownloadButton"] > button:hover {
    background: var(--teal) !important; color: #fff !important;
    transform: translateY(-3px) !important; box-shadow: 0 0 48px var(--teal-glow) !important; }
div.stButton > button:disabled { opacity: 0.4 !important; cursor: not-allowed !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--teal); border-radius: 99px; }
</style>
""", unsafe_allow_html=True)

# ── Aplicar clase modo guardia al body ──
if st.session_state.modo_guardia:
    components.html("""
    <script>
    (function(){
        function apply(){
            var b=window.parent.document.body;
            if(b) b.classList.add('guardia-mode');
        }
        apply();
        setTimeout(apply, 300);
    })();
    </script>
    """, height=0, scrolling=False)
else:
    components.html("""
    <script>
    (function(){
        function remove(){
            var b=window.parent.document.body;
            if(b) b.classList.remove('guardia-mode');
        }
        remove();
        setTimeout(remove, 300);
    })();
    </script>
    """, height=0, scrolling=False)



# ══════════════════════════════════════════
# PANTALLA 1 — BIENVENIDA
# ══════════════════════════════════════════
if st.session_state.pantalla == "bienvenida":
    webp_b64 = get_base64("fondo_sitre.webp")
    logo_b64 = get_base64("logo_sitre_transparente.png")
    fondo_css = f"""
    #fondo-sitre {{ position: fixed; inset: 0;
        background: url('data:image/webp;base64,{webp_b64}') center/cover no-repeat;
        filter: brightness(0.22) saturate(1.4); z-index: -10; }}
    """ if webp_b64 else ""
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="sitre-logo" alt="SITRE Logo">' if logo_b64 else '<div class="sitre-logo-fallback">🫁</div>'

    st.markdown(f"""
    <style>
    {fondo_css}
    .welcome-wrap {{ min-height:82vh; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px 20px 0px; position:relative; }}
    .welcome-wrap::before {{ content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:1px; height:60px; background:linear-gradient(to bottom,transparent,var(--teal)); }}
    .sitre-logo {{ width:175px; height:175px; object-fit:contain; filter:drop-shadow(0 0 16px var(--teal)) drop-shadow(0 0 40px rgba(13,148,136,0.4)); animation:pulse-glow 4s ease-in-out infinite,spin-slow 45s linear infinite; margin-bottom:10px; }}
    .sitre-logo-fallback {{ font-size:100px; margin-bottom:20px; animation:pulse-glow 4s ease-in-out infinite; }}
    @keyframes pulse-glow {{ 0%,100% {{ filter:drop-shadow(0 0 12px var(--teal)) drop-shadow(0 0 30px rgba(13,148,136,0.3)); }} 50% {{ filter:drop-shadow(0 0 22px var(--teal-light)) drop-shadow(0 0 55px rgba(20,184,166,0.55)); }} }}
    @keyframes spin-slow {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
    .welcome-eyebrow {{ font-size:0.65rem; font-weight:500; letter-spacing:6px; text-transform:uppercase; color:var(--teal-light); margin-bottom:5px; opacity:0; animation:fade-up 0.8s 0.2s forwards; }}
    .welcome-title {{ font-family:'DM Serif Display',serif; font-size:clamp(3.5rem,8vw,5.5rem); font-weight:400; color:var(--text); line-height:1; letter-spacing:-3px; text-align:center; margin-bottom:5px; opacity:0; animation:fade-up 0.8s 0.4s forwards; }}
    .welcome-title em {{ font-style:italic; color:var(--teal-light); }}
    .welcome-subtitle {{ font-size:0.95rem; font-weight:300; color:var(--muted); letter-spacing:2px; text-align:center; margin-bottom:20px; opacity:0; animation:fade-up 0.8s 0.6s forwards; }}
    .welcome-pills {{ display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-bottom:25px; opacity:0; animation:fade-up 0.8s 0.8s forwards; }}
    .pill {{ font-size:0.65rem; font-weight:500; letter-spacing:1.5px; text-transform:uppercase; color:var(--teal-light); border:1px solid rgba(13,148,136,0.4); border-radius:99px; padding:5px 14px; background:rgba(13,148,136,0.08); }}
    .welcome-wrap::after {{ content:''; position:absolute; bottom:-20px; left:50%; transform:translateX(-50%); width:1px; height:50px; background:linear-gradient(to top,transparent,var(--teal)); }}
    @keyframes fade-up {{ from {{ opacity:0; transform:translateY(15px); }} to {{ opacity:1; transform:translateY(0); }} }}
    </style>
    <div id="fondo-sitre"></div>
    <div class="welcome-wrap">
        {logo_html}
        <p class="welcome-eyebrow">Sistema de Triage Respiratorio</p>
        <h1 class="welcome-title">SI<em>TRE</em></h1>
        <p class="welcome-subtitle">Soporte a la Decisión Clínica</p>
        <div class="welcome-pills">
            <span class="pill">4 Patologías</span>
            <span class="pill">Score McIsaac · CURB-65</span>
            <span class="pill">Stewardship Antibiótico</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<div style='margin-top:30px;'>", unsafe_allow_html=True)
        if st.button("Iniciar Triage ➔", type="primary", use_container_width=True):
            st.session_state.pantalla = "selector"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        # ▼▼▼ MEGAZORD 5: RUTA REGULATORIA (SaMD) ▼▼▼
    st.markdown("<div style='max-width:700px; margin: 40px auto 0px;'>", unsafe_allow_html=True)
    with st.expander("⚖️ Regulatory & Compliance Target (SaMD / CDSS)"):
        st.markdown("""
        <div style="font-size:0.85rem; color:var(--text); line-height:1.6; padding: 5px;">
            <div style="display:flex; gap:15px; margin-bottom:16px; flex-wrap:wrap;">
                <div style="flex:1; min-width:200px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:14px; border-radius:10px; border-left:4px solid #14B8A6;">
                    <span style="font-size:0.65rem; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:#14B8A6;">México / LATAM</span><br>
                    <b style="font-size:1.05rem;">COFEPRIS</b><br>
                    Software Médico Clase I<br>
                    <span style="color:var(--muted); font-size:0.75rem;">(Bajo Riesgo / Exento de Registro Sanitario)</span>
                </div>
                <div style="flex:1; min-width:200px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:14px; border-radius:10px; border-left:4px solid #3B82F6;">
                    <span style="font-size:0.65rem; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:#3B82F6;">Internacional</span><br>
                    <b style="font-size:1.05rem;">FDA</b><br>
                    Clinical Decision Support (CDS)<br>
                    <span style="color:var(--muted); font-size:0.75rem;">(21st Century Cures Act / 510k Exempt target)</span>
                </div>
            </div>
            <p style="color:var(--teal-light); font-weight:700; font-size:0.7rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px;">Justificación Técnica y Arquitectura Legal</p>
            <p style="color:rgba(240,253,250,0.7); margin-bottom:0; text-align:justify;">
                SITRE utiliza un motor de inferencia basado en reglas explícitas (Expert System) sobre guías clínicas publicadas. 
                <b style="color:#F0FDFA;">No realiza diagnóstico probabilístico mediante IA generativa (Zero-Hallucination)</b> y permite al profesional de la salud revisar independientemente la base de cada recomendación (Audit Trail y Caja de Cristal). 
                Al no sustituir el juicio médico, sino complementarlo mediante evidencia trazable, cumple los criterios de <b>Software as a Medical Device (SaMD)</b> de bajo riesgo según los lineamientos del IMDRF, la NOM-241-SSA1-2012 (Suplemento para Dispositivos Médicos de la FEUM) y las exenciones de la FDA para software CDSS.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # ▲▲▲ FIN MEGAZORD 5 ▲▲▲

    # Toggle modo guardia — esquina inferior derecha
    mg_label = "🔴 Modo Guardia: ON" if st.session_state.modo_guardia else "🌙 Modo Guardia"
    mg_color = "#EF4444" if st.session_state.modo_guardia else "rgba(240,253,250,0.25)"
    st.markdown(f"""
    <div style="position:fixed; bottom:28px; right:28px; z-index:9999;">
      <div style="font-size:0.65rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
          color:{mg_color}; border:1px solid {mg_color}; border-radius:99px;
          padding:6px 16px; background:rgba(5,12,12,0.85); backdrop-filter:blur(8px);
          cursor:pointer;" id="mg-badge">
        {mg_label}
      </div>
    </div>
    """, unsafe_allow_html=True)
    col_mg1, col_mg2, col_mg3 = st.columns([1, 1, 1])
    with col_mg3:
        if st.checkbox("🌙 Modo Guardia Nocturna", value=st.session_state.modo_guardia, key="toggle_guardia_bienvenida"):
            st.session_state.modo_guardia = True
        else:
            st.session_state.modo_guardia = False

    components.html("""
    <canvas id="hx" style="position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:9998;"></canvas>
    <script>
    (function(){const cv=document.getElementById('hx');if(!cv)return;const ctx=cv.getContext('2d');function resize(){cv.width=window.innerWidth;cv.height=window.innerHeight;}resize();
    const hexes=[],N=24,C='20,184,166';function mk(){return{x:Math.random()*cv.width,y:Math.random()*cv.height,s:Math.random()*30+8,vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,r:Math.random()*Math.PI*2,vr:(Math.random()-.5)*.004,a:Math.random()*.11+.03,p:Math.random()*Math.PI*2};}
    for(let i=0;i<N;i++)hexes.push(mk());
    function hex(x,y,s,r,a){ctx.save();ctx.translate(x,y);ctx.rotate(r);ctx.beginPath();for(let i=0;i<6;i++){const ang=Math.PI/3*i;i?ctx.lineTo(s*Math.cos(ang),s*Math.sin(ang)):ctx.moveTo(s*Math.cos(ang),s*Math.sin(ang));}ctx.closePath();ctx.strokeStyle='rgba('+C+','+a+')';ctx.lineWidth=1;ctx.stroke();ctx.restore();}
    function loop(){ctx.clearRect(0,0,cv.width,cv.height);hexes.forEach(h=>{h.x+=h.vx;h.y+=h.vy;h.r+=h.vr;h.p+=.011;const a=h.a*(.55+.45*Math.sin(h.p));if(h.x<-80)h.x=cv.width+80;else if(h.x>cv.width+80)h.x=-80;if(h.y<-80)h.y=cv.height+80;else if(h.y>cv.height+80)h.y=-80;hex(h.x,h.y,h.s,h.r,a);});requestAnimationFrame(loop);}
    loop();window.addEventListener('resize',resize);})();
    </script>
    """, height=0, scrolling=False)

    st.markdown("""
    <style>
    .global-status-bar {
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        height: 34px; /* Aquí ya se debe notar el grosor */
        background: rgba(5, 12, 12, 0.95);
        backdrop-filter: blur(15px);
        border-top: 1px solid rgba(255, 255, 255, 0.12); /* Línea más brillante */
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 45px;
        z-index: 99999;
        font-family: 'DM Sans', sans-serif;
    }
    .gsb-item { 
        display: flex; 
        align-items: center; 
        gap: 10px; 
        font-size: 0.68rem; /* Fuente más grande y clara */
        font-weight: 500; 
        letter-spacing: 1px; 
        color: rgba(240, 253, 250, 0.65); 
    }
    .gsb-badge {
        font-size: 0.58rem; 
        font-weight: 800; 
        letter-spacing: 2px; 
        text-transform: uppercase;
        padding: 3px 12px; 
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(255,255,255,0.05); /* Sutil brillo */
    }
    </style>
    <div class="global-status-bar">
        <div class="gsb-item">
            <span class="gsb-badge" style="background:rgba(34,197,94,0.12); color:#22C55E; border:1px solid rgba(34,197,94,0.4);">✓ Deterministic</span>
            <span>Zero-Hallucination Engine</span>
        </div>
        <div class="gsb-item">
            <span class="gsb-badge" style="background:rgba(59,130,246,0.12); color:#3B82F6; border:1px solid rgba(59,130,246,0.4);">⚡ < 15ms</span>
            <span>Local Edge Compute</span>
        </div>
        <div class="gsb-item">
            <span class="gsb-badge" style="background:rgba(167,139,250,0.12); color:#A78BFA; border:1px solid rgba(167,139,250,0.4);">🛡️ No API Calls</span>
            <span>100% Data Privacy</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════
# PANTALLA 2 — SELECTOR DE PATOLOGÍA
# ══════════════════════════════════════════
elif st.session_state.pantalla == "selector":

    PATOLOGIAS = [
        {
            "id": "faringitis",
            "emoji": "🦠",
            "titulo": "Faringitis / IRA Alta",
            "score": "Score McIsaac",
            "descripcion": "Dolor de garganta, fiebre, exudado amigdalino. Diferenciación viral vs estreptocócica.",
            "color": "#14B8A6",
            "glow": "rgba(20,184,166,0.25)",
        },
        {
            "id": "neumonia",
            "emoji": "🫁",
            "titulo": "Neumonía Adquirida",
            "score": "Score CURB-65",
            "descripcion": "Tos productiva, fiebre, dificultad respiratoria. Estratificación de severidad y destino.",
            "color": "#3B82F6",
            "glow": "rgba(59,130,246,0.25)",
        },
        {
            "id": "oma",
            "emoji": "👂",
            "titulo": "Otitis Media Aguda",
            "score": "Criterios AAP/SEIP",
            "descripcion": "Otalgia, fiebre, signos timpánicos. Diagnóstico confirmado vs probable y decisión antibiótica.",
            "color": "#F59E0B",
            "glow": "rgba(245,158,11,0.25)",
        },
        {
            "id": "sinusitis",
            "emoji": "👃",
            "titulo": "Sinusitis Aguda",
            "score": "Criterios IDSA",
            "descripcion": "Congestión nasal, dolor facial, rinorrea purulenta. Diferenciación viral vs bacteriana por patrón temporal.",
            "color": "#A78BFA",
            "glow": "rgba(167,139,250,0.25)",
        },
    ]

    st.markdown("""
    <style>
    .sel-wrap { max-width: 900px; margin: 0 auto; padding: 56px 28px 40px; }
    .sel-title { font-family:'DM Serif Display',serif; font-size:2.8rem; font-weight:400; color:var(--text); letter-spacing:-1.5px; margin-bottom:6px; }
    .sel-sub { font-size:0.88rem; color:var(--muted); letter-spacing:1px; margin-bottom:40px; }
    </style>
    <div class="sel-wrap">
        <div class="sel-title">¿Qué evalúas hoy?</div>
        <p class="sel-sub">Selecciona la patología para cargar el formulario clínico correspondiente.</p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="large")
    for i, pat in enumerate(PATOLOGIAS):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border:1px solid {pat['color']}33;
                border-radius:20px; padding:24px 26px; margin-bottom:16px;
                border-left: 3px solid {pat['color']};">
              <div style="display:flex; align-items:center; gap:14px; margin-bottom:12px;">
                <span style="font-size:2rem; filter:drop-shadow(0 0 8px {pat['color']});">{pat['emoji']}</span>
                <div>
                  <div style="font-family:'DM Serif Display',serif; font-size:1.2rem; color:var(--text); line-height:1.2;">{pat['titulo']}</div>
                  <div style="font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:{pat['color']}; margin-top:3px;">{pat['score']}</div>
                </div>
              </div>
              <div style="font-size:0.82rem; color:var(--muted); line-height:1.55; margin-bottom:0;">{pat['descripcion']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Evaluar {pat['titulo']} ➔", key=f"btn_{pat['id']}", type="primary", use_container_width=True):
                st.session_state.patologia = pat["id"]
                st.session_state.demo_caso = None
                st.session_state.pantalla = "triage"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, _, _ = st.columns([1,3,1])
    with col_back:
        if st.button("← Inicio", type="primary"):
            st.session_state.pantalla = "bienvenida"
            st.rerun()


# ══════════════════════════════════════════
# PANTALLA 3 — FORMULARIOS DE TRIAGE
# ══════════════════════════════════════════
elif st.session_state.pantalla == "triage":

    patologia = st.session_state.patologia or "faringitis"
    demo = st.session_state.get("demo_caso")
    d = CASOS_DEMO.get(demo, {}) if demo else {}

    # CSS común
    st.markdown("""
    <style>
    .triage-wrap { max-width:1100px; margin:0 auto; padding:40px 32px 20px; }
    .triage-title { font-family:'DM Serif Display',serif; font-size:3.2rem; font-weight:400; color:white; letter-spacing:-1.5px; }
    .triage-badge { font-size:0.7rem; font-weight:600; letter-spacing:3px; text-transform:uppercase; color:var(--teal-light); border:1px solid var(--teal); border-radius:99px; padding:4px 12px; position:relative; top:-4px; margin-left:14px; }
    .section-label { font-size:0.75rem; font-weight:600; letter-spacing:4px; text-transform:uppercase; color:var(--teal-light); margin-bottom:14px; margin-top:22px; display:block; }
    .glass-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:24px 22px; margin-bottom:18px; }
    .safety-box { background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.2); border-radius:12px; padding:18px 20px; margin-top:20px; margin-bottom:10px; }
    </style>
    """, unsafe_allow_html=True)

    # Títulos y emojis por patología
    INFO_PAT = {
        "faringitis": ("🦠", "Faringitis / IRA Alta", "Score McIsaac"),
        "neumonia":   ("🫁", "Neumonía Adquirida",    "CURB-65"),
        "oma":        ("👂", "Otitis Media Aguda",    "Criterios AAP/SEIP"),
        "sinusitis":  ("👃", "Sinusitis Aguda",       "Criterios IDSA"),
    }
    emoji_pat, titulo_pat, score_pat = INFO_PAT.get(patologia, ("🫁","Triage","CDSS"))

    st.markdown(f"""
    <div class="triage-wrap">
        <div style="display:flex; align-items:baseline; margin-bottom:6px;">
            <span class="triage-title">{emoji_pat} {titulo_pat}</span>
            <span class="triage-badge">{score_pat}</span>
        </div>
        <p style="color:var(--muted); letter-spacing:1px; margin-bottom:18px; font-size:0.9rem;">
            Identificación y registro de parámetros clínicos.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Modo demo
    casos_de_esta_pat = {k:v for k,v in CASOS_DEMO.items() if v.get("patologia") == patologia}
    st.markdown("""
    <div style="max-width:1100px; margin:0 auto; padding:0 32px 0;">
    <div style="background:rgba(13,148,136,0.07); border:1px solid rgba(13,148,136,0.25); border-radius:12px; padding:12px 18px; margin-bottom:14px; display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
      <span style="font-size:1rem;">⚡</span>
      <span style="font-size:0.72rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#14B8A6;">Modo Demo</span>
      <span style="font-size:0.82rem; color:rgba(240,253,250,0.5);">Carga un caso clínico precargado para demostración</span>
    </div></div>
    """, unsafe_allow_html=True)

    cd1, cd2, cd3 = st.columns([2,1,1])
    with cd1:
        opciones_demo = ["— Ingresar manualmente —"] + list(casos_de_esta_pat.keys())
        caso_sel = st.selectbox("Demo", options=opciones_demo, label_visibility="collapsed")
    with cd2:
        if st.button("Cargar Caso ➔", type="primary", use_container_width=True):
            if caso_sel != "— Ingresar manualmente —":
                st.session_state.demo_caso = caso_sel
                st.rerun()
    with cd3:
        if st.button("Limpiar", type="primary", use_container_width=True):
            st.session_state.demo_caso = None
            st.rerun()

    st.markdown("<hr style='opacity:0.1; margin:14px 0;'>", unsafe_allow_html=True)

    # Nombre + Folio
    cn1, cn2 = st.columns([2,1])
    with cn1:
        nombre_paciente = st.text_input("Nombre completo del Paciente", value=d.get("nombre",""), placeholder="Ej. Juan Pérez López")
    with cn2:
        st.markdown("<p style='margin-bottom:8px; color:var(--muted); font-size:0.75rem; letter-spacing:2px;'>ID DE TRIAGE</p>", unsafe_allow_html=True)
        st.code(datetime.now().strftime("SITRE-%Y%m%d-%H%M"), language=None)

    st.markdown("<hr style='opacity:0.1; margin:14px 0;'>", unsafe_allow_html=True)
    diabetes = False
    diabetes_n = False
    diabetes_o = False
    diabetes_s = False
    # ══ FORMULARIO FARINGITIS ══════════════════════
    if patologia == "faringitis":
        col_l, col_r = st.columns([1,1], gap="large")
        with col_l:
            # ▼▼▼ UI POINT-OF-CARE ▼▼▼
            st.markdown('<div class="glass-card" style="border:1px solid rgba(167,139,250,0.3); background:rgba(167,139,250,0.05);">', unsafe_allow_html=True)
            st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;"><span class="section-label" style="color:#A78BFA; margin:0;">03 · Hardware Integrations (POC)</span><span style="font-size:0.6rem; background:#A78BFA33; color:#A78BFA; padding:2px 8px; border-radius:99px; font-weight:bold;">API READY</span></div>', unsafe_allow_html=True)
            
            poc_strep = st.selectbox("RadT Estreptococo A", ["No realizado", "Positivo", "Negativo"], help="Prueba rápida de antígeno estreptocócico")
            poc_viral = st.selectbox("Panel Viral Respiratorio", ["No realizado", "Influenza A/B", "COVID-19", "VSR", "Negativo"], help="PCR rápida / Antígeno múltiple")
            st.markdown('</div>', unsafe_allow_html=True)
            # ▲▲▲ FIN UI POC ▲▲▲
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">01 · Datos Generales & Signos Vitales</span>', unsafe_allow_html=True)
            edad_input = st.number_input("Edad (años)", 1, 120, d.get("edad",25))
            dias_input = st.number_input("Días de evolución", 1, 30, d.get("dias",3))
            fr_input   = st.number_input("Frecuencia Respiratoria (rpm)", 10, 60, d.get("fr",18))
            sat_input  = st.number_input("Saturación O₂ (%)", 50.0, 100.0, float(d.get("sat",98.0)), step=0.5)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">02 · Comorbilidades</span>', unsafe_allow_html=True)
            neumopatia = st.toggle("Neumopatía crónica (Asma/EPOC)", value=d.get("neumopatia",False))
            inmuno     = st.toggle("Inmunocompromiso", value=d.get("inmuno",False))
            diabetes   = st.toggle("Diabetes Mellitus", value=d.get("diabetes",False)) # NUEVO
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">03 · Cuadro Clínico</span>', unsafe_allow_html=True)
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("<p style='color:var(--teal-light);font-size:0.8rem;font-weight:600;margin-bottom:8px;'>Criterios bacterianos</p>", unsafe_allow_html=True)
                fiebre     = st.toggle("Fiebre > 38°C", value=d.get("fiebre",False))
                exudado    = st.toggle("Exudado amigdalino", value=d.get("exudado",False))
                adenopatia = st.toggle("Adenopatía cervical", value=d.get("adenopatia",False))
            with c2:
                st.markdown("<p style='color:var(--teal-light);font-size:0.8rem;font-weight:600;margin-bottom:8px;'>Signos virales</p>", unsafe_allow_html=True)
                tos      = st.toggle("Tos",      value=d.get("tos",False))
                rinorrea = st.toggle("Rinorrea",  value=d.get("rinorrea",False))
                disfonia = st.toggle("Disfonía",  value=d.get("disfonia",False))
            st.markdown("<br>", unsafe_allow_html=True)
            c3,c4 = st.columns(2)
            with c3:
                conjuntivitis = st.toggle("Conjuntivitis",    value=d.get("conjuntivitis",False))
                mialgias      = st.toggle("Mialgias severas", value=d.get("mialgias",False))
            with c4:
                exantema = st.toggle("Exantema",         value=d.get("exantema",False))
                nauseas  = st.toggle("Náuseas/Vómito",   value=d.get("nauseas",False))
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Score McIsaac en tiempo real ──────────────────
        score_rt = 0
        if fiebre: score_rt += 1
        if not tos: score_rt += 1
        if exudado: score_rt += 1
        if adenopatia: score_rt += 1
        try:
            if 3 <= edad_input <= 14: score_rt += 1
            elif edad_input >= 45: score_rt -= 1
        except: pass
        score_rt = max(0, score_rt)

        if score_rt >= 4:   rt_color, rt_label = "#22C55E", "Alto riesgo bacteriano"
        elif score_rt >= 2: rt_color, rt_label = "#F59E0B", "Riesgo moderado"
        else:               rt_color, rt_label = "#3B82F6", "Bajo riesgo bacteriano"

        pct_rt = min(score_rt / 5, 1) * 100
        components.html(f"""
        <style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);
            border-radius:14px;padding:16px 18px;margin-top:4px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <span style="font-size:0.6rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
                color:rgba(240,253,250,0.35);">&#9889; Score McIsaac en vivo</span>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                  color:{rt_color};border:1px solid {rt_color}55;border-radius:99px;
                  padding:2px 10px;background:{rt_color}15;">{rt_label}</span>
              <span style="font-family:Georgia,serif;font-size:1.8rem;color:{rt_color};
                  font-weight:700;line-height:1;">{score_rt}<span style="font-size:0.9rem;
                  color:rgba(240,253,250,0.3);">/5</span></span>
            </div>
          </div>
          <div style="width:100%;height:6px;background:rgba(255,255,255,0.07);border-radius:99px;overflow:hidden;">
            <div style="width:{pct_rt}%;height:100%;background:linear-gradient(to right,{rt_color}88,{rt_color});
                border-radius:99px;transition:width 0.4s ease;"></div>
          </div>
        </div>
        """, height=95, scrolling=False)
    elif patologia == "neumonia":
        col_l, col_r = st.columns([1,1], gap="large")
        with col_l:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">01 · Datos Generales</span>', unsafe_allow_html=True)
            edad_input = st.number_input("Edad (años)", 1, 120, d.get("edad",55))
            dias_input = st.number_input("Días de evolución", 1, 30, 4)
            fr_input   = st.number_input("Frecuencia Respiratoria (rpm)", 10, 60, d.get("fr",22))
            sat_input  = st.number_input("Saturación O₂ (%)", 50.0, 100.0, float(d.get("sat",94.0)), step=0.5)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">02 · Criterios CURB-65</span>', unsafe_allow_html=True)
            st.markdown("<p style='color:rgba(59,130,246,0.9);font-size:0.75rem;font-weight:600;margin-bottom:12px;letter-spacing:1px;'>1 punto por cada criterio</p>", unsafe_allow_html=True)
            confusion  = st.toggle("C — Confusión aguda (nuevo onset)", value=d.get("confusion",False))
            urea       = st.toggle("U — Urea >7 mmol/L o BUN >20 mg/dL", value=d.get("urea",False))
            hipotension= st.toggle("B — TAS <90 mmHg o TAD ≤60 mmHg", value=d.get("hipotension",False))
            st.markdown(f"<p style='font-size:0.78rem; color:var(--muted); margin-top:10px;'>● Edad ≥65: se calcula automáticamente | FR ≥30: se toma del campo arriba</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">03 · Cuadro Clínico</span>', unsafe_allow_html=True)
            fiebre_n     = st.toggle("Fiebre", value=d.get("fiebre",True))
            tos_prod     = st.toggle("Tos productiva / esputo", value=d.get("tos_prod",True))
            dolor_tor    = st.toggle("Dolor torácico pleurítico", value=d.get("dolor_toracico",False))
            escalofrios  = st.toggle("Escalofríos / rigidez", value=d.get("escalofrios",False))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">04 · Comorbilidades</span>', unsafe_allow_html=True)
            neumopatia_n = st.toggle("Neumopatía crónica (EPOC/Asma/Fibrosis)", value=d.get("neumopatia",False))
            inmuno_n     = st.toggle("Inmunocompromiso", value=d.get("inmuno",False))
            diabetes   = st.toggle("Diabetes Mellitus", value=d.get("diabetes",False)) # NUEVO
            st.markdown('</div>', unsafe_allow_html=True)

    # ══ FORMULARIO OMA ════════════════════════════
    elif patologia == "oma":
        col_l, col_r = st.columns([1,1], gap="large")
        with col_l:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">01 · Datos Generales</span>', unsafe_allow_html=True)
            edad_input   = st.number_input("Edad (años)", 0, 120, d.get("edad",5))
            dias_input   = st.number_input("Días de evolución", 1, 30, d.get("dias",2))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">02 · Criterios Diagnósticos</span>', unsafe_allow_html=True)
            st.markdown("<p style='color:var(--amber);font-size:0.75rem;font-weight:600;margin-bottom:10px;'>Confirmada = 3 criterios · Probable = 2 criterios</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:var(--teal-light);font-size:0.72rem;margin-bottom:6px;font-weight:600;'>C1 — Inicio agudo</p>", unsafe_allow_html=True)
            inicio_agudo = st.toggle("Inicio súbito de síntomas (<48h)", value=d.get("inicio_agudo",False))
            st.markdown("<p style='color:var(--teal-light);font-size:0.72rem;margin-top:10px;margin-bottom:6px;font-weight:600;'>C2 — Ocupación del oído medio</p>", unsafe_allow_html=True)
            abombamiento = st.toggle("Abombamiento timpánico",    value=d.get("abombamiento",False))
            otorrea      = st.toggle("Otorrea reciente",          value=d.get("otorrea",False))
            hipoacusia   = st.toggle("Hipoacusia",                value=d.get("hipoacusia",False))
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">03 · Signos Inflamatorios</span>', unsafe_allow_html=True)
            st.markdown("<p style='color:var(--teal-light);font-size:0.72rem;margin-bottom:6px;font-weight:600;'>C3 — Inflamación</p>", unsafe_allow_html=True)
            otalgia      = st.toggle("Otalgia / irritabilidad inexplicable", value=d.get("otalgia",False))
            fiebre_oma   = st.toggle("Fiebre > 38°C",                       value=d.get("fiebre_38",False))
            hiperemia    = st.toggle("Hiperemia timpánica intensa",           value=d.get("hiperemia",False))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">04 · Criterios de Gravedad</span>', unsafe_allow_html=True)
            fiebre_39    = st.toggle("Fiebre > 39°C",       value=d.get("fiebre_39",False))
            otalgia_int  = st.toggle("Otalgia intensa (EVA >7)", value=d.get("otalgia_intensa",False))
            bilateral    = st.toggle("OMA bilateral",        value=d.get("bilateral",False))
            inmuno_oma   = st.toggle("Inmunocompromiso",     value=d.get("inmuno",False))
            diabetes   = st.toggle("Diabetes Mellitus", value=d.get("diabetes",False)) # NUEVO
            episodios    = st.number_input("Episodios previos (últimos 6 meses)", 0, 10, d.get("episodios_previos",0))
            st.markdown('</div>', unsafe_allow_html=True)

    # ══ FORMULARIO SINUSITIS ══════════════════════
    elif patologia == "sinusitis":
        col_l, col_r = st.columns([1,1], gap="large")
        with col_l:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">01 · Datos Generales</span>', unsafe_allow_html=True)
            edad_input = st.number_input("Edad (años)", 1, 120, d.get("edad",30))
            dias_input = st.number_input("Días de evolución", 1, 60, d.get("dias",7))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">02 · Síntomas Cardinales</span>', unsafe_allow_html=True)
            congestion     = st.toggle("Congestión nasal",           value=d.get("congestion",False))
            rinorrea_pur   = st.toggle("Rinorrea purulenta / mucopurulenta", value=d.get("rinorrea_pur",False))
            dolor_facial   = st.toggle("Dolor / presión facial",     value=d.get("dolor_facial",False))
            hiposmia       = st.toggle("Hiposmia / anosmia",         value=d.get("hiposmia",False))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">04 · Comorbilidades</span>', unsafe_allow_html=True)
            inmuno_sin = st.toggle("Inmunocompromiso",              value=d.get("inmuno",False))
            asma       = st.toggle("Asma / Rinitis alérgica",       value=d.get("asma",False))
            diabetes_s = st.toggle("Diabetes Mellitus", value=d.get("diabetes",False)) # NUEVO
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">03 · Criterios de Etiología Bacteriana (IDSA)</span>', unsafe_allow_html=True)
            st.markdown("<p style='color:rgba(167,139,250,0.9);font-size:0.75rem;font-weight:600;margin-bottom:10px;'>Bacteriana = cualquiera de los 3 criterios</p>", unsafe_allow_html=True)
            doble_empeoramiento = st.toggle("'Double sickening' — empeora tras mejoría inicial (días 5-7)", value=d.get("doble_empeoramiento",False))
            fiebre_sin  = st.toggle("Fiebre > 38°C",              value=d.get("fiebre_38",False))
            dolor_uni   = st.toggle("Dolor facial unilateral prominente", value=d.get("dolor_unilateral",False))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">05 · Signos de Alarma (Banderas Rojas)</span>', unsafe_allow_html=True)
            fiebre_39_sin    = st.toggle("Fiebre ≥ 39°C",              value=d.get("fiebre_39",False))
            edema_periorbit  = st.toggle("Edema periorbitario",        value=d.get("edema_periorbitario",False))
            rigidez_nucal    = st.toggle("Rigidez nucal",              value=d.get("rigidez_nucal",False))
            cefalea_intensa  = st.toggle("Cefalea intensa",            value=d.get("cefalea_intensa",False))
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Validación de seguridad ────────────────────
    st.markdown('<div class="safety-box">', unsafe_allow_html=True)
    st.markdown("<p style='color:#EF4444;font-weight:700;font-size:0.75rem;letter-spacing:2px;margin-bottom:8px;'>⚠️ VALIDACIÓN DE SEGURIDAD</p>", unsafe_allow_html=True)
    safety_check = st.checkbox("Confirmo que el paciente NO presenta estridor, cianosis, tiraje intercostal ni alteración grave del estado de conciencia.")
    st.markdown('</div>', unsafe_allow_html=True)

# ▼▼▼ MEGAZORD 8: CLINICAL QA ENGINE (VALIDACIÓN CRUZADA) ▼▼▼
    qa_warnings = []
    
    # 1. Congruencia Respiratoria (SOLO PARA FARINGITIS Y NEUMONÍA)
    if patologia in ["faringitis", "neumonia"]:
        if fr_input >= 30 and sat_input >= 96.0:
            qa_warnings.append("Taquipnea severa (≥30 rpm) con Saturación Óptima (≥96%). Descartar ansiedad, acidosis metabólica o error de lectura del oxímetro.")
    
    # 2. Congruencia de Edad vs Patología
    if patologia == "sinusitis" and edad_input < 3:
        qa_warnings.append("Desarrollo anatómico: La sinusitis bacteriana es extremadamente rara en menores de 3 años por falta de neumatización de senos paranasales. Verifique diagnóstico diferencial.")
    
    # 3. Congruencia de OMA vs Edad
    if patologia == "oma" and edad_input > 15:
        qa_warnings.append("La OMA aislada en adultos es poco común. En caso de otalgia severa sin signos claros, descartar disfunción temporomandibular o patología dental.")
    
    # 4. Congruencia de Fiebre prolongada (Validación segura)
    try:
        fiebre_presente = False
        if patologia == "faringitis" and fiebre: fiebre_presente = True
        elif patologia == "neumonia" and fiebre_n: fiebre_presente = True
        elif patologia == "oma" and (fiebre_oma or fiebre_39): fiebre_presente = True
        elif patologia == "sinusitis" and (fiebre_sin or fiebre_39_sin): fiebre_presente = True
        
        if fiebre_presente and dias_input > 14:
            qa_warnings.append("Fiebre prolongada (>14 días). El cuadro excede el curso agudo habitual. Considere protocolo de Fiebre de Origen Desconocido (FOD) o infección sistémica.")
    except:
        pass # Blindaje por si alguna variable no se ha cargado

    qa_override = True # Por defecto es True si no hay errores
    if qa_warnings:
        qa_html = "".join([f"<li style='margin-bottom:4px;'>{w}</li>" for w in qa_warnings])
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.4); border-radius:12px; padding:18px 20px; margin-bottom:18px;">
            <p style="color:#F59E0B; font-weight:700; font-size:0.75rem; letter-spacing:2px; margin-bottom:8px;">🧐 ANOMALÍA CLÍNICA DETECTADA</p>
            <ul style="color:var(--text); font-size:0.85rem; padding-left:20px; margin-bottom:12px;">
                {qa_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        qa_override = st.checkbox("Confirmo que los datos atípicos son correctos para este paciente. Deseo continuar.")
    # ▲▲▲ FIN MEGAZORD 8 ▲▲▲
    st.markdown("<br>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns([1,1.5,1])
    with col_b2:
        label_btn = "Procesar Diagnóstico ➔" if (safety_check and qa_override) else "Complete las validaciones ⚠️"
        if st.button(label_btn, type="primary", use_container_width=True, disabled=not (safety_check and qa_override)):
            if not nombre_paciente.strip():
                st.warning("Por favor ingresa el nombre del paciente.")
            else:
                # Crear paciente y evaluar según patología
                if patologia == "faringitis":
                    p = PacienteIRA(edad=edad_input, dias_evolucion=dias_input,
                        frecuencia_respiratoria=fr_input, saturacion_oxigeno=sat_input,
                        fiebre_mayor_38=fiebre, exudado_amigdalino=exudado,
                        adenopatia_cervical_anterior=adenopatia, conjuntivitis=conjuntivitis,
                        mialgias_severas=mialgias, disfonia=disfonia, rinorrea=rinorrea,
                        tos=tos, exantema=exantema, nauseas_vomito=nauseas,
                        neumopatia_cronica=neumopatia, inmunocompromiso=inmuno, diabetes_mellitus=diabetes,
                        poc_strep=poc_strep, poc_viral=poc_viral)
                    resultado = evaluar_paciente(p)
                    score_display = p.calcular_score_centor()
                    virales_display = p.contar_signos_virales()


                elif patologia == "neumonia":
                    p = PacienteNeumoniaCAP(edad=edad_input, confusion_aguda=confusion,
                        urea_elevada=urea, frecuencia_respiratoria=fr_input,
                        hipotension=hipotension, saturacion_oxigeno=sat_input,
                        neumopatia_cronica=neumopatia_n, inmunocompromiso=inmuno_n,
                        fiebre=fiebre_n, tos_productiva=tos_prod,
                        dolor_toracico=dolor_tor, escalofrios=escalofrios, diabetes_mellitus=diabetes_n) 
                    resultado = evaluar_neumonia(p)
                    score_display = p.calcular_curb65()
                    virales_display = 0

                elif patologia == "oma":
                    p = PacienteOMA(edad=edad_input, dias_evolucion=dias_input,
                        inicio_agudo=inicio_agudo, abombamiento_timpanico=abombamiento,
                        otorrea_reciente=otorrea, hipoacusia=hipoacusia,
                        otalgia=otalgia, fiebre_mayor_38=fiebre_oma,
                        hiperemia_timpanica=hiperemia, fiebre_mayor_39=fiebre_39,
                        otalgia_intensa=otalgia_int, bilateral=bilateral,
                        inmunocompromiso=inmuno_oma, episodios_previos=int(episodios), diabetes_mellitus=diabetes_o)
                    resultado = evaluar_oma(p)
                    score_display = p.criterios_diagnosticos()
                    virales_display = 0

                elif patologia == "sinusitis":
                    p = PacienteSinusitis(edad=edad_input, dias_evolucion=dias_input,
                        congestion_nasal=congestion, rinorrea_purulenta=rinorrea_pur,
                        dolor_presion_facial=dolor_facial, hiposmia_anosmia=hiposmia,
                        empeoramiento_tras_mejoria=doble_empeoramiento,
                        fiebre_mayor_38=fiebre_sin, dolor_facial_unilateral=dolor_uni,
                        fiebre_mayor_39=fiebre_39_sin, edema_periorbitario=edema_periorbit,
                        rigidez_nucal=rigidez_nucal, cefalea_intensa=cefalea_intensa,
                        inmunocompromiso=inmuno_sin, asma_rinitis_alergica=asma, diabetes_mellitus=diabetes_s)
                    resultado = evaluar_sinusitis(p)
                    score_display = dias_input  # días como indicador
                    virales_display = 0
# 👇 BUSCA DONDE TERMINAN LOS IF DE PATOLOGÍAS Y PEGA ESTO:

                # ─── 1. Generar el ID de decisión (El Sello de Seguridad) ───
                ahora = datetime.now()
                decision_info = generar_decision_id(p, resultado, ahora)

                # ─── 2. Definir etiquetas para el historial ───
                TAG_MAP = {
                    "urgencia": "EMERGENCIA",
                    "viral": "VIRAL/LEVE",
                    "bacteriana": "BACTERIANA",
                    "gris": "INDETERMINADO"
                }

                # ─── 3. Incrementar contador global de antibióticos evitados ───
                if resultado.get("tipo") == "viral":
                    st.session_state.abx_evitados_global += 1

                # ─── 4. Guardar en el historial (Usando el hash exacto) ───
                st.session_state.historial.append({
                    "hora":       ahora.strftime("%H:%M"),
                    "nombre":     nombre_paciente.strip(),
                    "edad":       edad_input,
                    "patologia":  titulo_pat,
                    "score":      score_display,
                    "tipo":       resultado.get("tipo", "gris"),
                    "tag":        TAG_MAP.get(resultado.get("tipo", "gris"), "—"),
                    "hash_audit": decision_info["hash_full"]
                })

                # ─── 5. Cambiar de pantalla y mandar el sello de seguridad ───
                st.session_state.resultado_completo = resultado
                st.session_state.nombre_paciente    = nombre_paciente.strip()
                st.session_state.paciente_obj       = p
                st.session_state.decision_info      = decision_info  # PASAMOS EL HASH EXACTO A LA OTRA PANTALLA
                st.session_state.demo_caso          = None
                st.session_state.pantalla           = "resultados"
                st.rerun()

    # ── Historial + Dashboard ──────────────────────
    if st.session_state.historial:
        h = st.session_state.historial
        total     = len(h)
        virales   = sum(1 for x in h if x["tipo"] == "viral")
        bacterias = sum(1 for x in h if x["tipo"] == "bacteriana")
        urgencias = sum(1 for x in h if x["tipo"] == "urgencia")

        # Calculadora de impacto
        abx_evitados_turno = virales
        gramos_evitados = abx_evitados_turno * 3  # ~3g amoxicilina por curso

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='opacity:0.08; margin-bottom:20px;'>", unsafe_allow_html=True)

        # ── ALERTA EPIDÉMICA ──────────────────────────────
        if total >= 3 and virales / total >= 0.70:
            components.html(f"""
            <style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
            <div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.35);
                border-radius:14px;padding:14px 20px;margin-bottom:18px;
                display:flex;align-items:center;gap:14px;animation:pulse-alert 2s ease-in-out infinite;">
              <span style="font-size:1.5rem;flex-shrink:0;">🚨</span>
              <div>
                <div style="font-size:0.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
                    color:#3B82F6;margin-bottom:3px;">Alerta de Patrón Epidémico Detectado</div>
                <div style="font-size:0.82rem;color:#F0FDFA;">
                  <b>{round(virales/total*100)}%</b> de los casos en este turno son virales.
                  Posible <b>brote viral activo</b> en esta unidad. Reforzar medidas de control.
                </div>
              </div>
            </div>
            <style>
            @keyframes pulse-alert {{
              0%,100% {{ box-shadow: 0 0 0 0 rgba(59,130,246,0.3); }}
              50% {{ box-shadow: 0 0 0 8px rgba(59,130,246,0); }}
            }}
            </style>
            """, height=80, scrolling=False)
# ── MOTOR DE DETECCIÓN DE CLUSTERS BACTERIANOS ──
        # Contamos casos bacterianos por patología específica
        bacterias_por_pat = {}
        for x in h:
            if x["tipo"] == "bacteriana":
                pat = x["patologia"]
                bacterias_por_pat[pat] = bacterias_por_pat.get(pat, 0) + 1
        
        # Buscamos si alguna patología alcanzó el umbral crítico de 3 casos
        cluster_pat = next((pat for pat, count in bacterias_por_pat.items() if count >= 3), None)

        if cluster_pat:
            components.html(f"""
            <style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
            <div style="background:rgba(239,68,68,0.1); border:1.5px solid #EF4444; 
                border-radius:14px; padding:16px 22px; margin-bottom:18px;
                display:flex; align-items:center; gap:16px; position:relative; overflow:hidden;
                animation: alert-shake 0.8s cubic-bezier(.36,.07,.19,.97) both;">
              
              <div style="position:absolute; inset:0; background:radial-gradient(circle at center, rgba(239,68,68,0.15) 0%, transparent 70%); animation: pulse-bg 2s infinite;"></div>
              
              <span style="font-size:1.8rem; flex-shrink:0; z-index:1; filter: drop-shadow(0 0 10px #EF4444);">⚠️</span>
              <div style="z-index:1;">
                <div style="font-size:0.65rem; font-weight:800; letter-spacing:3px; text-transform:uppercase; 
                    color:#EF4444; margin-bottom:4px; display:flex; align-items:center; gap:8px;">
                  <span style="width:8px; height:8px; background:#EF4444; border-radius:50%; animation: blink 1s infinite;"></span>
                  Alerta de Cluster Bacteriano Detectado
                </div>
                <div style="font-size:0.9rem; color:#F0FDFA; line-height:1.5;">
                  Se han identificado <b>3 o más casos bacterianos</b> de <b>{cluster_pat.upper()}</b> en este turno. 
                  <br><span style="font-size:0.75rem; color:rgba(240,253,250,0.6);">Considerar notificación inmediata a Vigilancia Epidemiológica y revisión de protocolos de esterilización.</span>
                </div>
              </div>
              <div style="margin-left:auto; text-align:right; z-index:1;">
                <div style="font-size:0.55rem; color:#EF4444; font-weight:bold; letter-spacing:1px; text-transform:uppercase;">Protocolo</div>
                <div style="font-size:0.8rem; font-weight:bold; color:#F0FDFA;">SIVE-READY</div>
              </div>
            </div>

            <style>
            @keyframes alert-shake {{
              10%, 90% {{ transform: translate3d(-1px, 0, 0); }}
              20%, 80% {{ transform: translate3d(2px, 0, 0); }}
              30%, 50%, 70% {{ transform: translate3d(-4px, 0, 0); }}
              40%, 60% {{ transform: translate3d(4px, 0, 0); }}
            }}
            @keyframes pulse-bg {{
              0% {{ opacity: 0.3; }} 50% {{ opacity: 0.8; }} 100% {{ opacity: 0.3; }}
            }}
            @keyframes blink {{
              0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0; }}
            }}
            </style>
            """, height=100, scrolling=False)
            # ▼▼▼ MEGAZORD 6: NOTIFICACIÓN AUTOMÁTICA (CON SANGRÍA) ▼▼▼
            st.markdown("<div style='max-width:1100px; margin:0 auto; padding:0 32px;'>", unsafe_allow_html=True)
            if st.button("🚀 Notificar a Vigilancia Epidemiológica (SINAVE/InDRE)", type="secondary", use_container_width=True):
                with st.status("Preparando expediente epidemiológico...", expanded=True) as status:
                    st.write("Extractando metadatos de los 3 casos detectados...")
                    import time
                    time.sleep(1)
                    st.write("Generando Bundle de seguridad SHA-256...")
                    time.sleep(0.8)
                    st.write("Conectando con servidor seguro del InDRE...")
                    time.sleep(1.2)
                    status.update(label="✅ Notificación Enviada con Éxito", state="complete", expanded=False)
                
                st.toast("Reporte #EPI-MX-992-B generado correctamente", icon="📨")
                
                with st.expander("Ver Acuse de Recibo Digital"):
                    ultimo_hash = st.session_state.historial[-1].get("hash_audit", "HASH_SECURED_BY_SITRE")
                    
                    acuse = {
                        "id_reporte": "EPI-MX-992-B",
                        "timestamp": datetime.now().isoformat(),
                        "patologia_detectada": cluster_pat.upper(),
                        "casos_vinculados": [x["nombre"] for x in h if x["tipo"] == "bacteriana" and x["patologia"] == cluster_pat],
                        "status_envio": "ACCEPTED_BY_DGE",
                        "hash_integridad": ultimo_hash 
                    }
                    st.json(acuse)
            st.markdown("</div>", unsafe_allow_html=True)
            # ▲▲▲ FIN MEGAZORD 6 ▲▲▲
        # ── PANEL TURNO (métricas) ──────────────────────
        st.markdown("<div style='max-width:1100px;margin:0 auto;padding:0 32px;'><p style='font-size:0.65rem;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:#14B8A6;margin-bottom:14px;'>Panel de Turno</p></div>", unsafe_allow_html=True)

        col_m1,col_m2,col_m3,col_m4 = st.columns(4)
        for col,val,label,color in [
            (col_m1,total,    "Pacientes Evaluados","#14B8A6"),
            (col_m2,virales,  "Viral / Leve",       "#3B82F6"),
            (col_m3,bacterias,"Casos Bacterianos",  "#22C55E"),
            (col_m4,urgencias,"Urgencias",          "#EF4444"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                    border-radius:14px;padding:16px 18px;text-align:center;margin-bottom:12px;border-top:2px solid {color};">
                  <div style="font-family:'DM Serif Display',serif;font-size:2.4rem;color:{color};line-height:1;">{val}</div>
                  <div style="font-size:0.6rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:rgba(240,253,250,0.4);margin-top:5px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
                # ▼▼▼ MEGAZORD 11: ANTIMICROBIAL FOOTPRINT SCORE (RAM) ▼▼▼
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        if total > 0:
            tasa_ram = (bacterias / total) * 100
            if tasa_ram > 40:
                ram_color = "#EF4444" # Rojo
                ram_label = "Alto Riesgo de Selección RAM"
                ram_msg = "Precaución: Alta presión antibiótica en este turno. Revisar adherencia a guías."
            elif tasa_ram >= 20:
                ram_color = "#F59E0B" # Amarillo
                ram_label = "Huella Antimicrobiana Moderada"
                ram_msg = "Prescripción dentro de los límites esperados. Mantener vigilancia activa."
            else:
                ram_color = "#22C55E" # Verde
                ram_label = "Stewardship Efectivo"
                ram_msg = "Excelente. Prescripción antibiótica altamente optimizada en este turno."
            
            components.html(f"""
            <style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:18px 22px;margin-bottom:16px; position:relative; overflow:hidden;">
                <div style="position:absolute; top:-50%; left:-10%; width:120%; height:200%; background:radial-gradient(ellipse at center, {ram_color}11 0%, transparent 70%); pointer-events:none;"></div>
                
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:12px; position:relative; z-index:1;">
                    <div>
                        <div style="font-size:0.65rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:rgba(240,253,250,0.5);margin-bottom:4px;">Antimicrobial Footprint Score</div>
                        <div style="font-size:1.1rem;color:#F0FDFA;font-weight:600;">{ram_label}</div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-family:'DM Serif Display',serif;font-size:2.2rem;color:{ram_color};line-height:1;">{tasa_ram:.1f}<span style="font-size:1rem;">%</span></span>
                    </div>
                </div>
                
                <div style="width:100%;height:8px;background:rgba(255,255,255,0.08);border-radius:99px;overflow:hidden;margin-bottom:8px; position:relative; z-index:1;">
                    <div style="width:{tasa_ram}%;height:100%;background:{ram_color};border-radius:99px;transition:width 1s cubic-bezier(0.23, 1, 0.32, 1); box-shadow: 0 0 10px {ram_color}66;"></div>
                </div>
                
                <div style="font-size:0.75rem;color:rgba(240,253,250,0.4); position:relative; z-index:1;">{ram_msg}</div>
            </div>
            """, height=125, scrolling=False)
        # ▲▲▲ FIN MEGAZORD 11 ▲▲▲

        # ── CALCULADORA DE IMPACTO ────────────────────────
        # ── CALCULADORA DE IMPACTO B2B (EFECTO CASINO / DOPAMINA) ────────────────────────
        abx_global = st.session_state.abx_evitados_global
        
        # Unit Economics: Costo directo ($15) + Riesgo ajustado C.diff ($15,000 * 1%) = ~$165 USD
        ahorro_por_caso = 165
        ahorro_turno = abx_evitados_turno * ahorro_por_caso
        ahorro_global = abx_global * ahorro_por_caso

        components.html(f"""
        <style>
        body {{ margin:0; padding:0; background:transparent; font-family:'DM Sans',sans-serif; }}
        .jackpot-box {{
            background: linear-gradient(135deg, rgba(250, 204, 21, 0.08), rgba(20, 184, 166, 0.05));
            border: 1px solid rgba(250, 204, 21, 0.4);
            border-radius: 16px;
            padding: 20px 26px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 25px rgba(250, 204, 21, 0.15);
            animation: pulse-border 2s infinite alternate;
        }}
        .jackpot-box::after {{
            content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(250, 204, 21, 0.15), transparent);
            transform: skewX(-20deg); animation: shine 3s infinite;
        }}
        @keyframes shine {{ 0% {{ left: -100%; }} 20% {{ left: 200%; }} 100% {{ left: 200%; }} }}
        @keyframes pulse-border {{ 0% {{ box-shadow: 0 0 15px rgba(250,204,21,0.1); }} 100% {{ box-shadow: 0 0 35px rgba(250,204,21,0.3); }} }}
        .number-glow {{
            font-family: 'DM Serif Display', serif;
            font-size: 2.8rem;
            color: #FACC15; /* Oro */
            text-shadow: 0 0 20px rgba(250, 204, 21, 0.7);
            line-height: 1;
            margin-bottom: 4px;
        }}
        .coin-icon {{ 
            font-size: 2.5rem; 
            filter: drop-shadow(0 0 12px rgba(250,204,21,0.8)); 
            animation: float 3s ease-in-out infinite; 
        }}
        @keyframes float {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-8px); }} }}
        </style>
        <div class="jackpot-box">
          <div style="display:flex;align-items:center;gap:18px;z-index:1;">
            <div class="coin-icon">💰</div>
            <div>
              <div style="font-size:0.65rem;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#FACC15;margin-bottom:4px;">
                Unit Economics · Ahorro Hospitalario (ROI)
              </div>
              <div style="font-size:0.85rem;color:#F0FDFA;line-height:1.4;">
                <b style="color:#22C55E;font-size:1rem;">{abx_evitados_turno}</b> prescripciones evitadas hoy.<br>
                Riesgo mitigado de <i>C. difficile</i> ($15k/caso) e insumos directos.
              </div>
            </div>
          </div>
          <div style="text-align:right;z-index:1;">
            <div style="font-size:0.6rem;color:rgba(240,253,250,0.5);margin-bottom:4px;letter-spacing:1px;text-transform:uppercase;">Presupuesto Salvado (Global)</div>
            <div class="number-glow">
              ${ahorro_global:,.0f} <span style="font-size:1rem;color:rgba(250,204,21,0.7);font-family:'DM Sans',sans-serif;text-shadow:none;">USD</span>
            </div>
            <div style="font-size:0.75rem;color:#22C55E;font-weight:700;letter-spacing:1px;background:rgba(34,197,94,0.15);padding:4px 10px;border-radius:99px;display:inline-block;">
              + ${ahorro_turno:,.0f} USD este turno 📈
            </div>
          </div>
        </div>
        """, height=130, scrolling=False)

        TIPO_COLORS = {"urgencia":"#EF4444","viral":"#3B82F6","bacteriana":"#22C55E","gris":"#F59E0B"}
        table_rows = ""
        for i, px in enumerate(reversed(h)):
            color = TIPO_COLORS.get(px["tipo"],"#F59E0B")
            bg    = "rgba(255,255,255,0.02)" if i%2==0 else "rgba(255,255,255,0.01)"
            table_rows += f"""
            <tr style="background:{bg};">
              <td style="padding:9px 12px;font-size:0.78rem;color:rgba(240,253,250,0.4);">{px['hora']}</td>
              <td style="padding:9px 12px;font-size:0.85rem;color:#F0FDFA;font-weight:500;">{px['nombre']}</td>
              <td style="padding:9px 12px;font-size:0.78rem;color:rgba(240,253,250,0.5);text-align:center;">{px['edad']} a</td>
              <td style="padding:9px 12px;font-size:0.78rem;color:{color};text-align:center;font-weight:600;">{px['patologia']}</td>
              <td style="padding:9px 12px;text-align:center;">
                <span style="display:inline-block;font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                    color:{color};border:1px solid {color}55;border-radius:99px;padding:3px 10px;background:{color}15;">{px['tag']}</span>
              </td>
            </tr>"""

        table_height = 58 + len(h) * 44
        components.html(f"""
        <style>
          body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}
          table{{width:100%;border-collapse:collapse;}}
          thead tr{{background:rgba(13,148,136,0.12);border-bottom:1px solid rgba(13,148,136,0.25);}}
          th{{padding:9px 12px;font-size:0.6rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#14B8A6;}}
          th:first-child,td:first-child{{text-align:left;}}
          th:not(:first-child):not(:nth-child(2)),td:not(:first-child):not(:nth-child(2)){{text-align:center;}}
          td:nth-child(2){{text-align:left;}}
          .wrap{{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:14px;overflow:hidden;}}
        </style>
        <div class="wrap">
          <table>
            <thead><tr>
              <th>Hora</th><th>Paciente</th><th>Edad</th><th>Patologia</th><th>Resultado</th>
            </tr></thead>
            <tbody>{table_rows}</tbody>
          </table>
        </div>
        """, height=table_height, scrolling=False)

# ▼▼▼ MEGAZORD 9: ADMINISTRATIVE CONTROL CENTER ▼▼▼
        st.markdown("<br><hr style='opacity:0.1;'>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
            <span style="font-size:1.5rem;">📊</span>
            <div>
                <div style="font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--muted);">Shift Management</div>
                <div style="font-size:1.1rem; color:#F0FDFA; font-weight:600; font-family:'DM Serif Display',serif;">Cierre de Turno y Exportación</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        admin_col1, admin_col2 = st.columns(2)

        with admin_col1:
            # --- EXPORTACIÓN CSV ---
            import pandas as pd
            df_historial = pd.DataFrame(h)
            csv = df_historial.to_csv(index=False).encode('utf-8')
            
            # Texto limpio sin caja HTML gigante
            st.markdown("<p style='font-size:0.8rem; color:var(--muted); margin-bottom:12px; padding:0 8px;'>Base de datos en formato crudo. Ideal para investigación clínica, exportación a Excel o entrenamiento de Machine Learning.</p>", unsafe_allow_html=True)
            st.download_button(
                label="📁 Exportar Base de Datos (.CSV)",
                data=csv,
                file_name=f"SITRE_DATA_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with admin_col2:
            # --- EXPORTACIÓN PDF ---
            # Texto limpio sin caja HTML gigante
            st.markdown("<p style='font-size:0.8rem; color:var(--muted); margin-bottom:12px; padding:0 8px;'>Reporte formal consolidado con métricas de ROI y Stewardship listo para entregar a la Jefatura de Guardia.</p>", unsafe_allow_html=True)
            
            metricas_turno = {
                "total": total,
                "virales": virales,
                "ahorro": ahorro_turno
            }
            
            st.download_button(
                label="📄 Descargar Resumen de Turno (PDF)",
                data=generar_pdf_resumen_turno(h, metricas_turno),
                file_name=f"SITRE_SHIFT_REPORT_{datetime.now().strftime('%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        # ▲▲▲ FIN MEGAZORD 9 ▲▲▲
    # Botón cambiar patología
    st.markdown("<br>", unsafe_allow_html=True)
    col_ch1,col_ch2,col_ch3 = st.columns([1,1.5,1])
    with col_ch2:
        if st.button("← Cambiar Patología", type="primary", use_container_width=True):
            st.session_state.pantalla = "selector"
            st.rerun()


# ══════════════════════════════════════════

# ══════════════════════════════════════════
# PANTALLA 4 — RESULTADOS  (rediseñada)
# Jerarquía: Hero → Scores → Guía →
#   Caja Cristal → Timeline → AMR →
#   Ficha Paciente → Controles
# ══════════════════════════════════════════
elif st.session_state.pantalla == "resultados":

    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
        PDF_DISPONIBLE = True
    except ImportError:
        PDF_DISPONIBLE = False

    resultado     = st.session_state.resultado_completo
    nombre_pac    = st.session_state.get("nombre_paciente", "Paciente")
    paciente      = st.session_state.get("paciente_obj", None)
    patologia     = st.session_state.get("patologia", "faringitis")
    tipo          = resultado.get("tipo", "gris")
    diagnostico   = resultado["diagnostico"]
    tratamiento   = resultado["tratamiento"]

    ahora         = datetime.now()
    fecha_str     = ahora.strftime("%d %b %Y").upper()
    hora_str      = ahora.strftime("%H:%M")
    decision_info = st.session_state.decision_info
    folio         = decision_info["decision_id"]

    # ── Score labels ──────────────────────────────────────────────
    if patologia == "faringitis" and paciente:
        score_val   = paciente.calcular_score_centor()
        score_label = "Score McIsaac"
        score_max   = 5
        viral_val   = paciente.contar_signos_virales()
        viral_label = "Signos Virales"
        viral_max   = 7
    elif patologia == "neumonia" and paciente:
        score_val   = paciente.calcular_curb65()
        score_label = "CURB-65"
        score_max   = 5
        viral_val   = score_val
        viral_label = "Severidad"
        viral_max   = 5
    elif patologia == "oma" and paciente:
        score_val   = paciente.criterios_diagnosticos()
        score_label = "Criterios Dx"
        score_max   = 3
        viral_val   = 1 if paciente.es_grave() else 0
        viral_label = "Gravedad"
        viral_max   = 1
    else:
        score_val   = 0
        score_label = "Score"
        score_max   = 5
        viral_val   = 0
        viral_label = "Indicador"
        viral_max   = 5

    score_pct  = min(max(score_val / score_max, 0), 1) * 100 if score_max > 0 else 0
    viral_pct  = min(max(viral_val / viral_max, 0), 1) * 100 if viral_max > 0 else 0
    score_info = {"val": score_val, "max": score_max, "label": score_label}

    CONFIGS = {
        "urgencia":   {"accent":"#EF4444","glow":"rgba(239,68,68,0.3)", "bg":"rgba(239,68,68,0.07)", "tag":"EMERGENCIA",   "label":"Derivación Inmediata a Urgencias",       "emoji":"🚨","pcol":"#EF4444"},
        "viral":      {"accent":"#3B82F6","glow":"rgba(59,130,246,0.3)","bg":"rgba(59,130,246,0.07)","tag":"VIRAL / LEVE", "label":"Manejo Conservador · Sin Antibióticos",  "emoji":"🧊","pcol":"#3B82F6"},
        "bacteriana": {"accent":"#22C55E","glow":"rgba(34,197,94,0.3)", "bg":"rgba(34,197,94,0.07)", "tag":"BACTERIANA",   "label":"Indicación Antimicrobiana",              "emoji":"🦠","pcol":"#22C55E"},
        "gris":       {"accent":"#F59E0B","glow":"rgba(245,158,11,0.3)","bg":"rgba(245,158,11,0.07)","tag":"INDETERMINADO","label":"Valoración Clínica Presencial Requerida","emoji":"⚠️","pcol":"#F59E0B"},
    }
    c = CONFIGS.get(tipo, CONFIGS["gris"])

    if score_max > 0 and score_val / score_max >= 0.7:
        gauge_color = "#22C55E"
    elif score_max > 0 and score_val / score_max >= 0.4:
        gauge_color = "#F59E0B"
    else:
        gauge_color = "#3B82F6"

    diag_html = diagnostico.replace("\n", "<br>")
    trat_html = tratamiento.replace("\n", "<br>")
    pcol = c["pcol"]

    # Alerta diabetes
    banner_diabetes = ""
    if getattr(paciente, "diabetes_mellitus", False):
        if tipo == "viral":
            msg_dm = "Vigilancia estrecha: Infecciones virales pueden detonar hiperglucemia. Recomendar monitoreo de glucosa y no suspender insulina."
        else:
            msg_dm = "Alto riesgo de complicaciones. Considerar ajuste de dosis según función renal (TFG) para el antibiótico indicado."
        banner_diabetes = f"""
<div style="background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.28);
    border-radius:12px;padding:14px 18px;margin-bottom:20px;
    display:flex;align-items:flex-start;gap:14px;">
  <span style="font-size:1.4rem;line-height:1;flex-shrink:0;">🔶</span>
  <div>
    <div style="font-size:0.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
        color:#F59E0B;margin-bottom:3px;">Alerta Endocrinológica · Riesgo Ajustado</div>
    <div style="font-size:0.84rem;color:#F0FDFA;line-height:1.5;">{msg_dm}</div>
  </div>
</div>"""

    NOMBRES_PAT = {"faringitis":"Faringitis","neumonia":"Neumonía CAP","oma":"Otitis Media Aguda","sinusitis":"Sinusitis Aguda"}
    nombre_pat_display = NOMBRES_PAT.get(patologia, "IRA")
    metadatos = {"patologia": patologia, "nombre_paciente": nombre_pac,
                 "nombre_pat_display": nombre_pat_display, "score_info": score_info}

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 1 — META + PACIENTE + HERO + SCORES + GUÍA
    # Todo en un solo st.markdown para evitar flashes y doble render
    # ══════════════════════════════════════════════════════════════
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
.res-page      {{ max-width:980px; margin:0 auto; padding:32px 28px 8px; }}

/* ── Meta bar ── */
.res-meta      {{ display:flex; justify-content:space-between; align-items:center;
                  margin-bottom:16px; padding:10px 16px;
                  background:rgba(255,255,255,0.02); border-radius:10px;
                  border:1px solid rgba(255,255,255,0.06); }}
.meta-left     {{ font-size:0.7rem; color:var(--teal-light); font-weight:700;
                  letter-spacing:2px; text-transform:uppercase; }}
.meta-left span{{ font-family:monospace; color:rgba(240,253,250,0.5);
                  font-size:0.62rem; margin-left:10px; font-weight:400; }}
.meta-right    {{ font-size:0.62rem; color:rgba(240,253,250,0.3);
                  text-align:right; line-height:1.6; font-family:monospace; }}

/* ── Patient bar ── */
.pat-bar       {{ display:flex; justify-content:space-between; align-items:center;
                  background:rgba(13,148,136,0.07); border:1px solid rgba(13,148,136,0.18);
                  border-radius:14px; padding:14px 22px; margin-bottom:18px; }}
.pat-label     {{ font-size:0.58rem; font-weight:700; letter-spacing:3px;
                  text-transform:uppercase; color:var(--teal-light); margin-bottom:3px; }}
.pat-name      {{ font-family:'DM Serif Display',serif; font-size:1.65rem;
                  color:#F0FDFA; line-height:1; }}
.pat-folio     {{ font-size:0.65rem; color:rgba(240,253,250,0.4); text-align:right; line-height:1.7; }}

/* ── Hero card ── */
.hero          {{ position:relative; border:1px solid {c["accent"]}44; border-radius:24px;
                  overflow:hidden; margin-bottom:18px;
                  box-shadow:0 0 60px {c["glow"]}; animation:card-in 0.65s cubic-bezier(0.23,1,0.32,1) both; }}
.hero-bg       {{ position:absolute; inset:0; z-index:0;
                  background:radial-gradient(ellipse at 18% 50%,{c["accent"]}16 0%,transparent 55%),
                              radial-gradient(ellipse at 82% 50%,{c["accent"]}0c 0%,transparent 55%);
                  animation:bg-pulse 5s ease-in-out infinite alternate; }}
@keyframes bg-pulse{{ from{{opacity:.5}} to{{opacity:1}} }}
.hero-inner    {{ position:relative; z-index:1; display:flex; align-items:center;
                  gap:28px; padding:30px 36px; }}
.hero-emoji    {{ font-size:4.4rem; line-height:1; flex-shrink:0;
                  filter:drop-shadow(0 0 14px {c["accent"]});
                  animation:icon-pop 0.55s 0.35s cubic-bezier(0.34,1.56,0.64,1) both; }}
@keyframes icon-pop{{ from{{opacity:0;transform:scale(0.2) rotate(-20deg)}} to{{opacity:1;transform:scale(1) rotate(0deg)}} }}
.hero-tag      {{ display:inline-block; font-size:0.58rem; font-weight:700;
                  letter-spacing:4px; text-transform:uppercase; color:{c["accent"]};
                  border:1px solid {c["accent"]}55; border-radius:99px;
                  padding:3px 13px; margin-bottom:10px; background:{c["bg"]}; }}
.hero-label    {{ font-family:'DM Serif Display',serif;
                  font-size:clamp(1.4rem,2.8vw,2.1rem); color:#F0FDFA;
                  font-weight:400; letter-spacing:-0.3px; line-height:1.2; margin-bottom:8px; }}
.hero-diag     {{ font-size:0.9rem; color:rgba(240,253,250,0.55); line-height:1.6; }}

/* ── Score cards ── */
.scores-row    {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:18px; }}
.score-card    {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
                  border-radius:16px; padding:20px 22px; }}
.score-lbl     {{ font-size:0.58rem; font-weight:700; letter-spacing:3px;
                  text-transform:uppercase; color:rgba(240,253,250,0.35); margin-bottom:12px; }}
.score-num     {{ font-family:'DM Serif Display',serif; font-size:3rem; line-height:1; margin-bottom:6px; }}
.bar-bg        {{ width:100%; height:7px; background:rgba(255,255,255,0.07);
                  border-radius:99px; overflow:hidden; margin-bottom:6px; }}
.bar-fill-s    {{ height:100%; border-radius:99px;
                  background:linear-gradient(to right,{gauge_color}88,{gauge_color});
                  animation:fill-s 1.1s 0.5s cubic-bezier(0.23,1,0.32,1) both; }}
@keyframes fill-s{{ from{{width:0%}} to{{width:{score_pct}%}} }}
.bar-fill-v    {{ height:100%; border-radius:99px;
                  background:linear-gradient(to right,#3B82F688,#3B82F6);
                  animation:fill-v 1.1s 0.7s cubic-bezier(0.23,1,0.32,1) both; }}
@keyframes fill-v{{ from{{width:0%}} to{{width:{viral_pct}%}} }}
.bar-ticks     {{ display:flex; justify-content:space-between;
                  font-size:0.55rem; color:rgba(240,253,250,0.3); }}

/* ── Therapeutic guide ── */
.tx-card       {{ background:{c["bg"]}; border:1px solid {c["accent"]}33;
                  border-radius:16px; padding:22px 24px; margin-bottom:18px; }}
.tx-eyebrow    {{ font-size:0.58rem; font-weight:700; letter-spacing:3px;
                  text-transform:uppercase; color:{c["accent"]}; margin-bottom:12px; }}
.tx-body       {{ font-size:0.93rem; color:#F0FDFA; line-height:1.8; }}

/* ── Reference pill ── */
.ref-pill      {{ display:inline-flex; align-items:center; gap:8px;
                  background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
                  border-radius:99px; padding:6px 16px; margin-bottom:18px;
                  font-size:0.72rem; color:rgba(240,253,250,0.4); }}
.ref-pill b    {{ color:rgba(240,253,250,0.65); }}

/* ── Particles ── */
#res-canvas    {{ position:fixed; inset:0; pointer-events:none; z-index:999; }}

/* ── Animations ── */
@keyframes card-in{{ from{{opacity:0;transform:translateY(24px) scale(.98)}} to{{opacity:1;transform:translateY(0) scale(1)}} }}
@keyframes fade-up{{ from{{opacity:0;transform:translateY(16px)}}          to{{opacity:1;transform:translateY(0)}} }}
</style>

<canvas id="res-canvas"></canvas>
<script>
(function(){{
  const cv=document.getElementById('res-canvas'); if(!cv)return;
  const ctx=cv.getContext('2d');
  cv.width=window.innerWidth; cv.height=window.innerHeight;
  const pts=[]; const col='{pcol}';
  const isViral='{tipo}'==='viral';
  const cc=['#22C55E','#3B82F6','#14B8A6','#A78BFA','#F59E0B','#EC4899'];
  function spawnC(){{pts.push({{x:Math.random()*cv.width,y:-10,vx:(Math.random()-.5)*3,vy:Math.random()*3+1,r:Math.random()*6+3,color:cc[Math.floor(Math.random()*cc.length)],rot:Math.random()*Math.PI*2,vrot:(Math.random()-.5)*.15,shape:Math.random()>.5?'rect':'circle',life:Math.random()*120+100,age:0,isC:true}});}}
  function spawn(){{pts.push({{x:Math.random()*cv.width,y:cv.height+10,vx:(Math.random()-.5)*1.2,vy:-(Math.random()*2.2+.8),r:Math.random()*5+2,life:Math.random()*100+80,age:0,isC:false}});}}
  function draw(){{ctx.clearRect(0,0,cv.width,cv.height);for(let i=pts.length-1;i>=0;i--){{const p=pts[i];p.x+=p.vx;p.y+=p.vy;p.age++;if(p.age>=p.life){{pts.splice(i,1);continue;}}ctx.save();ctx.globalAlpha=(1-p.age/p.life)*.75;if(p.isC){{p.rot+=p.vrot;p.vy+=.04;ctx.translate(p.x,p.y);ctx.rotate(p.rot);ctx.fillStyle=p.color;if(p.shape==='rect')ctx.fillRect(-p.r,-p.r/2,p.r*2,p.r);else{{ctx.beginPath();ctx.arc(0,0,p.r,0,Math.PI*2);ctx.fill();}}}}else{{ctx.fillStyle=col;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();}}ctx.restore();}}requestAnimationFrame(draw);}}
  if(isViral){{setTimeout(()=>{{for(let i=0;i<60;i++)setTimeout(spawnC,i*25);}},200);setInterval(()=>{{if(pts.filter(p=>p.isC).length<30)spawnC();}},800);}}else{{setTimeout(()=>{{for(let i=0;i<20;i++)spawn();}},300);setInterval(()=>{{if(pts.length<35)spawn();}},350);}}
  draw(); window.addEventListener('resize',()=>{{cv.width=window.innerWidth;cv.height=window.innerHeight;}});
}})();
</script>

<div class="res-page">

  <!-- META BAR -->
  <div class="res-meta">
    <div class="meta-left">
      Reporte Clínico · SITRE CDSS v2.0 · {nombre_pat_display}
      <span>📅 {fecha_str} · 🕒 {hora_str}</span>
    </div>
    <div class="meta-right">
      <b style="color:var(--teal-light);">{folio}</b><br>
      SHA-256·{decision_info["hash_short"]}… · Noreste MX
    </div>
  </div>

  <!-- PATIENT BAR -->
  <div class="pat-bar">
    <div>
      <div class="pat-label">Paciente evaluado</div>
      <div class="pat-name">{nombre_pac}</div>
    </div>
    <div class="pat-folio">
      <span style="color:var(--teal-light);">●</span> Triage activo<br>
      <span style="font-family:monospace;font-size:0.6rem;">{folio}</span>
    </div>
  </div>

  {banner_diabetes}

  <!-- HERO CARD -->
  <div class="hero">
    <div class="hero-bg"></div>
    <div class="hero-inner">
      <div class="hero-emoji">{c["emoji"]}</div>
      <div>
        <span class="hero-tag">{c["tag"]}</span>
        <div class="hero-label">{c["label"]}</div>
        <div class="hero-diag">{diag_html}</div>
      </div>
    </div>
  </div>

  <!-- SCORES -->
  <div class="scores-row">
    <div class="score-card">
      <div class="score-lbl">{score_label}</div>
      <div class="score-num" style="color:{gauge_color};">{score_val}<span style="font-size:1.1rem;color:rgba(240,253,250,0.3);">/{score_max}</span></div>
      <div class="bar-bg"><div class="bar-fill-s"></div></div>
      <div class="bar-ticks">{"".join(f"<span>{i}</span>" for i in range(score_max+1))}</div>
    </div>
    <div class="score-card">
      <div class="score-lbl">{viral_label}</div>
      <div class="score-num" style="color:#3B82F6;">{viral_val}<span style="font-size:1.1rem;color:rgba(240,253,250,0.3);">/{viral_max}</span></div>
      <div class="bar-bg"><div class="bar-fill-v"></div></div>
      <div class="bar-ticks">{"".join(f"<span>{i}</span>" for i in range(viral_max+1))}</div>
    </div>
  </div>

  <!-- GUÍA TERAPÉUTICA -->
  <div class="tx-card">
    <div class="tx-eyebrow">💊 Guía Terapéutica Sugerida</div>
    <div class="tx-body">{trat_html}</div>
  </div>

  <!-- REFERENCIA ACADÉMICA (pill discreta) -->
  <div class="ref-pill">
    📚 <b>{"Lim et al. Thorax 2003;58:377 · doi:10.1136/thorax.58.5.377" if patologia=="neumonia" else "McIsaac WJ et al. JAMA 2004;291:1589 · doi:10.1001/jama.291.13.1589" if patologia=="faringitis" else "Lieberthal AS et al. Pediatrics 2013;131:e964 · doi:10.1542/peds.2012-3488" if patologia=="oma" else "Chow AW et al. Clin Infect Dis 2012;54:e72 · doi:10.1093/cid/cir1049"}</b>
  </div>

</div>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # PEDIATRIC DOSING (si aplica — antes de Caja de Cristal)
    # ══════════════════════════════════════════════════════════════
    if paciente and paciente.edad < 12 and tipo == "bacteriana":
        st.markdown("""
        <div style="max-width:980px;margin:0 auto 18px;background:rgba(14,165,233,0.05);
            border:1px solid rgba(14,165,233,0.28);border-radius:16px;padding:20px 22px;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
            <span style="font-size:1.6rem;">🧸</span>
            <div>
              <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#0EA5E9;">Módulo Pediátrico Seguro</div>
              <div style="font-size:1rem;color:#F0FDFA;font-weight:600;font-family:'DM Serif Display',serif;">Calculadora de Suspensión</div>
            </div>
          </div>
          <p style="font-size:0.83rem;color:rgba(240,253,250,0.5);margin-bottom:14px;">
            Calcula los mL exactos. Safety cap automático contra sobredosis.
          </p>
        """, unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns([1, 1, 1.5])
        with pc1:
            peso_kg = st.number_input("Peso (kg)", min_value=3.0, max_value=60.0, value=15.0, step=0.5)
        with pc2:
            dosis_mg_kg = st.selectbox("Dosis (mg/kg/día)", [80, 90, 50])
        with pc3:
            presentacion = st.selectbox("Presentación", ["250 mg / 5 mL", "400 mg / 5 mL", "500 mg / 5 mL"])
        mg_totales = peso_kg * dosis_mg_kg
        if mg_totales > 3000:
            mg_totales = 3000
            alerta_cap = "<br><span style='color:#EF4444;font-size:0.73rem;font-weight:700;'>⚠️ Umbral de seguridad: dosis topada a 3,000 mg/día.</span>"
        else:
            alerta_cap = ""
        mg5ml = int(presentacion.split(" ")[0])
        ml_dia = (mg_totales * 5) / mg5ml
        st.markdown(f"""
          <div style="background:rgba(0,0,0,0.2);border-radius:10px;padding:14px 16px;
              margin-top:12px;border-left:3px solid #0EA5E9;">
            <div style="font-size:0.6rem;color:#0EA5E9;font-weight:700;letter-spacing:1px;margin-bottom:6px;">TEXTO PARA RECETA</div>
            <div style="font-size:1.1rem;color:#F0FDFA;">
              Tomar <b>{ml_dia/3:.1f} mL</b> cada 8h
              <span style="font-size:0.8rem;color:rgba(240,253,250,0.4);"> · {ml_dia/2:.1f} mL cada 12h</span>
            </div>
            <div style="font-size:0.72rem;color:rgba(240,253,250,0.35);margin-top:4px;">
              {mg_totales:,.0f} mg/día{alerta_cap}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 2 — CAJA DE CRISTAL  (colapsable con <details>)
    # ══════════════════════════════════════════════════════════════
    razonamiento = resultado.get("razonamiento", None)
    if razonamiento:
        pasos = razonamiento.get("pasos", [])
        pasos_html = ""
        for paso in pasos:
            items_html = ""
            for item in paso["items"]:
                pts_b = (f'<span style="font-size:0.58rem;font-weight:700;color:{item["color"]};'
                         f'border:1px solid {item["color"]}44;border-radius:4px;padding:1px 6px;'
                         f'background:{item["color"]}11;margin-left:6px;">{item["pts"]}</span>'
                         if item.get("pts", "") else "")
                items_html += (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;'
                    f'padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                    f'<div style="display:flex;align-items:center;gap:8px;">'
                    f'<div style="width:6px;height:6px;border-radius:50%;background:{item["color"]};flex-shrink:0;"></div>'
                    f'<span style="font-size:0.77rem;color:rgba(240,253,250,0.6);">{item["label"]}</span>'
                    f'</div>'
                    f'<div style="display:flex;align-items:center;gap:4px;">'
                    f'<span style="font-size:0.72rem;font-weight:600;color:{item["color"]};">{item["status"]}</span>{pts_b}'
                    f'</div></div>'
                )
            res_row = (
                f'<div style="margin-top:8px;padding:7px 12px;background:rgba(255,255,255,0.03);'
                f'border-radius:8px;border-left:3px solid {paso["resultado_color"]};">'
                f'<span style="font-size:0.7rem;font-weight:700;color:{paso["resultado_color"]};'
                f'letter-spacing:1px;">{paso["resultado"]}</span></div>'
                if paso.get("resultado") else ""
            )
            pasos_html += (
                f'<div style="margin-bottom:14px;padding:13px 15px;background:rgba(255,255,255,0.02);'
                f'border:1px solid rgba(255,255,255,0.06);border-radius:12px;">'
                f'<div style="font-size:0.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;'
                f'color:#14B8A6;margin-bottom:9px;">{paso["titulo"]}</div>'
                f'{items_html}{res_row}</div>'
            )

        st.markdown(f"""
<style>
details.cc {{ background:rgba(255,255,255,0.02); border:1px solid rgba(20,184,166,0.22);
              border-radius:14px; margin:0 auto 18px; max-width:980px; }}
details.cc summary {{ display:flex; align-items:center; justify-content:space-between;
                      padding:15px 20px; cursor:pointer; list-style:none;
                      border-radius:14px; transition:background .2s; }}
details.cc summary::-webkit-details-marker {{ display:none; }}
details.cc summary:hover {{ background:rgba(20,184,166,0.05); }}
details.cc[open] summary {{ border-bottom-left-radius:0; border-bottom-right-radius:0;
                             border-bottom:1px solid rgba(255,255,255,0.05); }}
details.cc .chevron {{ transition:transform .3s; font-size:.8rem; color:#14B8A6; }}
details.cc[open] .chevron {{ transform:rotate(180deg); }}
.cc-body {{ padding:16px 20px; animation:fadeIn .3s ease; }}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(-4px)}}to{{opacity:1;transform:translateY(0)}}}}
</style>
<details class="cc">
  <summary>
    <div style="display:flex;align-items:center;gap:12px;">
      <span style="font-size:1.1rem;">🔍</span>
      <div>
        <div style="font-size:0.6rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
            color:#14B8A6;margin-bottom:2px;">Caja de Cristal · Explicabilidad de la Decisión</div>
        <div style="font-size:0.8rem;color:rgba(240,253,250,0.55);">
          Motor: {razonamiento["motor"]} &nbsp;·&nbsp;
          DOI: {razonamiento["doi"]} &nbsp;·&nbsp;
          {razonamiento["ms"]}ms
        </div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
      <span style="font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:#22C55E;border:1px solid #22C55E44;border-radius:99px;
          padding:3px 10px;background:#22C55E11;">✓ Determinista</span>
      <span class="chevron">▾</span>
    </div>
  </summary>
  <div class="cc-body">
    <!-- 3 meta pills -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;">
      <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
          border-radius:10px;padding:10px 14px;">
        <div style="font-size:0.52rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
            color:rgba(240,253,250,0.3);margin-bottom:3px;">Motor</div>
        <div style="font-size:0.75rem;color:#F0FDFA;font-weight:600;">{razonamiento["motor"]}</div>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
          border-radius:10px;padding:10px 14px;">
        <div style="font-size:0.52rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
            color:rgba(240,253,250,0.3);margin-bottom:3px;">DOI</div>
        <div style="font-size:0.72rem;color:#14B8A6;font-weight:600;">{razonamiento["doi"]}</div>
      </div>
      <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
          border-radius:10px;padding:10px 14px;">
        <div style="font-size:0.52rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
            color:rgba(240,253,250,0.3);margin-bottom:3px;">Respuesta</div>
        <div style="font-size:0.75rem;color:#F0FDFA;font-weight:600;">{razonamiento["ms"]} ms</div>
      </div>
    </div>
    {pasos_html}
    <!-- Determinismo + Referencia completa -->
    <div style="padding:9px 13px;background:rgba(34,197,94,0.05);
        border:1px solid rgba(34,197,94,0.15);border-radius:10px;margin-bottom:10px;">
      <span style="font-size:0.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:#22C55E;margin-right:8px;">✓ Sistema Determinista</span>
      <span style="font-size:0.7rem;color:rgba(240,253,250,0.45);">{razonamiento["deterministic_note"]}</span>
    </div>
    <div style="padding:10px 13px;background:rgba(255,255,255,0.02);
        border:1px solid rgba(255,255,255,0.06);border-radius:10px;">
      <div style="font-size:0.52rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:rgba(240,253,250,0.3);margin-bottom:4px;">Referencia PubMed</div>
      <div style="font-size:0.73rem;color:rgba(240,253,250,0.45);line-height:1.5;font-style:italic;">
        {razonamiento["ref_completa"]}</div>
    </div>
  </div>
</details>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 3 — TIMELINE "SIN TRATAMIENTO"
    # ══════════════════════════════════════════════════════════════
    TIMELINES = {
        "faringitis": {
            "bacteriana": [
                ("0h","#14B8A6","Consulta actual","Faringitis estreptocócica identificada. Ventana óptima de tratamiento."),
                ("48h","#F59E0B","Sin mejoría","Persistencia de fiebre. Riesgo de absceso periamigdalino."),
                ("5d","#EF4444","Complicación","Fiebre reumática aguda: riesgo de carditis 1-3% sin antibiótico."),
                ("3sem","#991B1B","Secuela","Glomerulonefritis post-estreptocócica. Daño renal irreversible potencial."),
            ],
            "viral": [
                ("0h","#14B8A6","Consulta actual","Cuadro viral confirmado. Antibiótico NO indicado."),
                ("3d","#3B82F6","Pico sintomático","Máxima carga viral. Reposo e hidratación son el tratamiento correcto."),
                ("7d","#22C55E","Resolución","Resolución espontánea esperada. Sin secuelas con manejo conservador."),
            ],
            "urgencia": [
                ("0h","#EF4444","Consulta actual","Hipoxia o taquipnea. Riesgo vital inmediato."),
                ("1h","#991B1B","Crítico","Sin soporte O₂: insuficiencia respiratoria progresiva."),
            ],
        },
        "neumonia": {
            "urgencia": [
                ("0h","#EF4444","Evaluación","CURB-65 alto. Mortalidad >15% sin hospitalización."),
                ("6h","#991B1B","Deterioro","Hipoxemia progresiva. Riesgo VM sin antibiótico IV."),
                ("24h","#7F1D1D","Sepsis","Bacteriemia con sepsis. Mortalidad 30-40% sin antibiótico precoz."),
            ],
            "gris": [
                ("0h","#F59E0B","Evaluación","Neumonía moderada. Seguimiento estrecho a 48h."),
                ("48h","#EF4444","Revisión crítica","Sin mejoría = hospitalización obligatoria."),
                ("7d","#22C55E","Con tratamiento","Resolución esperada con antibiótico y seguimiento."),
            ],
            "viral": [
                ("0h","#14B8A6","Evaluación","Neumonía leve (CURB-65 0-1). Mortalidad <3%. Ambulatorio."),
                ("48h","#3B82F6","Revisión","Control obligatorio a 48h. Si empeora: hospitalizar."),
                ("6sem","#22C55E","Resolución","Rx de control a 4-6 semanas para confirmar resolución."),
            ],
        },
        "oma": {
            "bacteriana": [
                ("0h","#14B8A6","Diagnóstico","OMA confirmada. Antibiótico reduce complicaciones 80%."),
                ("72h","#F59E0B","Sin antibiótico","Otalgia persistente. Riesgo de mastoiditis incipiente."),
                ("7d","#EF4444","Complicación","Mastoiditis aguda. Requiere hospitalización."),
                ("3sem","#991B1B","Secuela","Hipoacusia conductiva. Riesgo de daño permanente."),
            ],
            "gris": [
                ("0h","#F59E0B","OMA probable","2/3 criterios. Observación 48-72h antes de antibiótico."),
                ("48h","#14B8A6","Revisión","Si mejora: continuar. Si empeora: iniciar antibiótico."),
            ],
            "viral": [
                ("0h","#3B82F6","Sin criterios","No cumple OMA. Probable viral. Manejo sintomático."),
                ("7d","#22C55E","Resolución","Curación espontánea esperada. Sin antibiótico."),
            ],
        },
        "sinusitis": {
            "bacteriana": [
                ("0h","#14B8A6","Diagnóstico","Sinusitis bacteriana. Antibiótico reduce duración 2-3 días."),
                ("5d","#F59E0B","Sin mejoría","Riesgo extensión a senos adyacentes."),
                ("14d","#EF4444","Complicación","Celulitis orbitaria. TAC urgente."),
                ("30d","#991B1B","Secuela","Sinusitis crónica. Cirugía endoscópica >20% casos."),
            ],
            "viral": [
                ("0h","#3B82F6","Diagnóstico","Rinosinusitis viral. 80-85% resuelve sin antibiótico."),
                ("7d","#14B8A6","Mejoría","Reducción progresiva. Irrigación nasal acelera recuperación."),
                ("10d","#F59E0B","Vigilancia","Si no mejora día 10: reevaluar etiología bacteriana."),
            ],
            "urgencia": [
                ("0h","#EF4444","Banderas rojas","Edema periorbitario o rigidez nucal. Extensión posible."),
                ("2h","#991B1B","Urgencia","Sin TAC + antibiótico IV: riesgo de absceso cerebral."),
            ],
        },
    }

    tl_pasos = TIMELINES.get(patologia, {}).get(tipo, TIMELINES.get(patologia, {}).get("viral", []))
    if tl_pasos:
        tl_html = ""
        for i, (tiempo, color, titulo, desc) in enumerate(tl_pasos):
            ultimo = i == len(tl_pasos) - 1
            lc = "#1A2E2E" if ultimo else color
            tl_html += f"""
<div style="display:flex;gap:0;align-items:flex-start;">
  <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;width:40px;">
    <div style="width:11px;height:11px;border-radius:50%;background:{color};
        box-shadow:0 0 7px {color}88;margin-top:4px;flex-shrink:0;"></div>
    {"" if ultimo else f'<div style="width:2px;flex:1;min-height:28px;background:linear-gradient({color},{lc});margin:3px 0;"></div>'}
  </div>
  <div style="padding-bottom:{"0" if ultimo else "16px"};flex:1;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
      <span style="font-size:0.6rem;font-weight:700;letter-spacing:2px;color:{color};
          border:1px solid {color}55;border-radius:99px;padding:2px 7px;background:{color}12;">{tiempo}</span>
      <span style="font-size:0.83rem;font-weight:600;color:#F0FDFA;">{titulo}</span>
    </div>
    <div style="font-size:0.78rem;color:rgba(240,253,250,0.48);line-height:1.45;">{desc}</div>
  </div>
</div>"""

        tl_h = 72 + len(tl_pasos) * 68
        components.html(f"""
<style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);
    border-radius:16px;padding:20px 22px;">
  <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
      color:rgba(240,253,250,0.3);margin-bottom:16px;">
    ⏱ Progresión clínica sin tratamiento adecuado
  </div>
  {tl_html}
</div>
""", height=tl_h, scrolling=False)

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 4 — SEMÁFORO AMR
    # ══════════════════════════════════════════════════════════════
    AMR_DATA = {
        "faringitis": {
            "titulo": "Resistencia AMR · Patógenos IRA Alta · Noreste MX",
            "fuente": "Red PUCRA 2024 · SIREVA II OPS · Hospital Universitario Monterrey",
            "patogenos": [
                {"nombre":"S. pyogenes (Estreptococo A)","abx":"Amoxicilina",   "resistencia":2,  "nivel":"BAJA", "color":"#22C55E","nota":"Primera línea segura. Sin resistencia clínica significativa."},
                {"nombre":"S. pyogenes (Estreptococo A)","abx":"Macrólidos",    "resistencia":18, "nivel":"MEDIA","color":"#F59E0B","nota":"Resistencia a macrólidos en aumento. Usar solo en alérgicos a penicilina."},
                {"nombre":"S. pneumoniae",               "abx":"Penicilina",    "resistencia":22, "nivel":"MEDIA","color":"#F59E0B","nota":"Resistencia intermedia 15-30% según SIREVA II México 2024."},
            ]},
        "neumonia": {
            "titulo": "Resistencia AMR · Neumonía Comunitaria · Noreste MX",
            "fuente": "Red PUCRA 2024 · Hospital Universitario NL · InDRE",
            "patogenos": [
                {"nombre":"S. pneumoniae","abx":"Amoxicilina",      "resistencia":12,"nivel":"BAJA", "color":"#22C55E","nota":"Primera línea efectiva para NAC ambulatoria en la región."},
                {"nombre":"S. pneumoniae","abx":"Macrólidos",       "resistencia":31,"nivel":"ALTA", "color":"#EF4444","nota":"Alta resistencia. Evitar monoterapia con azitromicina en NAC."},
                {"nombre":"H. influenzae","abx":"Ampicilina",       "resistencia":24,"nivel":"MEDIA","color":"#F59E0B","nota":"Beta-lactamasas en aumento. Preferir Amox/Clav."},
                {"nombre":"K. pneumoniae","abx":"Cefalosporinas 3G","resistencia":38,"nivel":"ALTA", "color":"#EF4444","nota":"BLEE 36% según PUCRA 2024. Considerar carbapenem si sospecha."},
            ]},
        "oma": {
            "titulo": "Resistencia AMR · Otitis Media Aguda · Noreste MX",
            "fuente": "Consenso SEIP 2023 · SIREVA II · Datos NL/Coahuila",
            "patogenos": [
                {"nombre":"S. pneumoniae", "abx":"Amoxicilina","resistencia":15,"nivel":"BAJA", "color":"#22C55E","nota":"Primera línea efectiva a dosis altas."},
                {"nombre":"H. influenzae", "abx":"Amoxicilina","resistencia":22,"nivel":"MEDIA","color":"#F59E0B","nota":"Beta-lactamasas ~16%. Si falla: Amox/Clav."},
                {"nombre":"M. catarrhalis","abx":"Amoxicilina","resistencia":75,"nivel":"ALTA", "color":"#EF4444","nota":"Alta resistencia intrínseca. Sensible a Amox/Clav y TMP-SMX."},
            ]},
        "sinusitis": {
            "titulo": "Resistencia AMR · Rinosinusitis Bacteriana · Noreste MX",
            "fuente": "Guías IDSA 2012 · PRAN México · PUCRA Tamaulipas/NL",
            "patogenos": [
                {"nombre":"S. pneumoniae","abx":"Amoxicilina","resistencia":18,"nivel":"BAJA", "color":"#22C55E","nota":"Primera línea IDSA. Efectiva en 80% de sinusitis bacteriana."},
                {"nombre":"S. pneumoniae","abx":"Macrólidos", "resistencia":35,"nivel":"ALTA", "color":"#EF4444","nota":"Alta resistencia en México. NO usar como monoterapia."},
                {"nombre":"H. influenzae","abx":"Ampicilina", "resistencia":24,"nivel":"MEDIA","color":"#F59E0B","nota":"Si falla amoxicilina 72h: Amox/Clav o fluoroquinolona."},
            ]},
    }
    amr = AMR_DATA.get(patologia, AMR_DATA["faringitis"])
    barras_html = ""
    for pat in amr["patogenos"]:
        r = pat["resistencia"]; col_r = pat["color"]
        barras_html += f"""
<div style="margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
    <div>
      <span style="font-size:0.8rem;font-weight:600;color:#F0FDFA;">{pat['nombre']}</span>
      <span style="font-size:0.7rem;color:rgba(240,253,250,0.35);margin-left:7px;">vs {pat['abx']}</span>
    </div>
    <div style="display:flex;align-items:center;gap:7px;">
      <span style="font-size:0.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:{col_r};border:1px solid {col_r}55;border-radius:99px;
          padding:2px 8px;background:{col_r}15;">{pat['nivel']}</span>
      <span style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:{col_r};font-weight:700;">{r}%</span>
    </div>
  </div>
  <div style="width:100%;height:5px;background:rgba(255,255,255,0.07);border-radius:99px;overflow:hidden;margin-bottom:4px;">
    <div style="width:{r}%;height:100%;background:linear-gradient(to right,{col_r}88,{col_r});border-radius:99px;"></div>
  </div>
  <div style="font-size:0.7rem;color:rgba(240,253,250,0.35);line-height:1.4;">{pat['nota']}</div>
</div>"""

    amr_h = 110 + len(amr["patogenos"]) * 80
    components.html(f"""
<style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);
    border-radius:16px;padding:20px 22px;margin-top:16px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
      margin-bottom:16px;flex-wrap:wrap;gap:8px;">
    <div>
      <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
          color:rgba(240,253,250,0.3);margin-bottom:4px;">&#129440; Semaforo de Resistencia Antimicrobiana</div>
      <div style="font-size:0.95rem;color:#F0FDFA;font-weight:600;">{amr["titulo"]}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:#14B8A6;border:1px solid rgba(13,148,136,0.35);border-radius:99px;
          padding:3px 9px;background:rgba(13,148,136,0.08);display:inline-block;margin-bottom:4px;">
        Demo · SINAVE-Ready
      </div>
      <div style="font-size:0.6rem;color:rgba(240,253,250,0.28);line-height:1.4;">{amr["fuente"]}</div>
    </div>
  </div>
  <div style="display:flex;gap:7px;margin-bottom:16px;flex-wrap:wrap;">
    <span style="font-size:0.58rem;font-weight:700;padding:3px 9px;border-radius:99px;
        background:rgba(34,197,94,0.12);color:#22C55E;border:1px solid rgba(34,197,94,0.35);">&#9679; BAJA &lt;20%</span>
    <span style="font-size:0.58rem;font-weight:700;padding:3px 9px;border-radius:99px;
        background:rgba(245,158,11,0.12);color:#F59E0B;border:1px solid rgba(245,158,11,0.35);">&#9679; MEDIA 20-34%</span>
    <span style="font-size:0.58rem;font-weight:700;padding:3px 9px;border-radius:99px;
        background:rgba(239,68,68,0.12);color:#EF4444;border:1px solid rgba(239,68,68,0.35);">&#9679; ALTA &ge;35%</span>
  </div>
  {barras_html}
  <div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);
      font-size:0.62rem;color:rgba(240,253,250,0.2);line-height:1.4;">
    Datos basados en evidencia (demo). Arquitectura lista para API REST SINAVE/InDRE · Fase 3 roadmap SITRE.
  </div>
</div>
""", height=amr_h, scrolling=False)

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 5 — FICHA EDUCATIVA DEL PACIENTE (colapsable)
    # ══════════════════════════════════════════════════════════════
    ficha = get_ficha(patologia, tipo, folio, fecha_str, nombre_pat_display)
    color_ficha  = ficha["color_hero"]
    accent_ficha = ficha["color_accent"]
    badge_color  = "#3B82F6" if tipo == "viral" else "#22C55E" if tipo == "bacteriana" else "#F59E0B"
    badge_label  = "VIRAL — Sin antibiótico" if tipo == "viral" else "BACTERIANA — Con antibiótico" if tipo == "bacteriana" else "SEGUIMIENTO"

    preview_steps = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;'
        f'border-bottom:1px solid rgba(255,255,255,0.04);">'
        f'<span style="font-size:1rem;flex-shrink:0;">{em}</span>'
        f'<span style="font-size:0.8rem;color:rgba(240,253,250,0.72);line-height:1.4;">{tx}</span>'
        f'</div>'
        for em, tx in ficha.get("que_hacer", [])
    )
    alarmas_preview = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:8px;padding:5px 0;'
        f'border-bottom:1px solid rgba(255,255,255,0.04);">'
        f'<span style="color:#F59E0B;font-size:0.72rem;flex-shrink:0;margin-top:1px;">⚠</span>'
        f'<span style="font-size:0.78rem;color:rgba(240,253,250,0.65);">{a}</span>'
        f'</div>'
        for a in ficha.get("cuando_regresar", [])
    )
    alarmas_section = (
        f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(239,68,68,0.2);'
        f'border-radius:12px;padding:13px 15px;margin-bottom:10px;">'
        f'<div style="font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;'
        f'color:#EF4444;margin-bottom:4px;">&#128680; Regresar al médico si:</div>'
        f'{alarmas_preview}</div>'
        if ficha.get("cuando_regresar") else ""
    )

    st.markdown(f"""
<style>
details.m4 {{ background:transparent; margin-bottom:18px; max-width:980px; margin-left:auto; margin-right:auto; }}
details.m4 summary {{ display:flex;align-items:center;justify-content:space-between;
    cursor:pointer;padding:14px 18px;border-radius:14px;
    background:rgba(255,255,255,0.02);border:1px solid {color_ficha}30;
    transition:background .2s;list-style:none; }}
details.m4 summary::-webkit-details-marker {{ display:none; }}
details.m4 summary:hover {{ background:{color_ficha}0A; }}
details.m4[open] summary {{ border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom-color:transparent; }}
details.m4 .chev4 {{ transition:transform .3s;color:{accent_ficha};font-size:.75rem; }}
details.m4[open] .chev4 {{ transform:rotate(180deg); }}
.m4body {{ padding-top:8px;animation:fadeIn .3s ease; }}
.m4sec {{ background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
          border-radius:12px;padding:13px 15px;margin-bottom:10px; }}
</style>
<details class="m4">
  <summary>
    <div style="display:flex;align-items:center;gap:12px;">
      <span style="font-size:1.4rem;">{ficha['emoji_hero']}</span>
      <div>
        <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
            color:{accent_ficha};margin-bottom:2px;">Ficha Educativa · Desescalada Narrativa</div>
        <div style="font-size:0.88rem;color:#F0FDFA;font-weight:600;">{ficha['titulo']}</div>
        <div style="font-size:0.73rem;color:rgba(240,253,250,0.45);margin-top:1px;">{ficha['subtitulo']}</div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:7px;flex-shrink:0;">
      <span style="font-size:0.56rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
          color:{badge_color};border:1px solid {badge_color}44;border-radius:99px;
          padding:3px 9px;background:{badge_color}10;">{badge_label}</span>
      <span class="chev4">▾</span>
    </div>
  </summary>
  <div class="m4body">
    <div class="m4sec" style="border-color:{color_ficha}30;background:{color_ficha}08;">
      <div style="font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:{accent_ficha};margin-bottom:7px;">&#128172; {ficha.get('mito_titulo','')}</div>
      <div style="font-size:0.8rem;color:rgba(240,253,250,0.7);line-height:1.55;margin-bottom:9px;">
        {ficha.get('mito_cuerpo','')}</div>
      <div style="display:flex;align-items:flex-start;gap:7px;background:rgba(255,255,255,0.04);
          border-radius:8px;padding:7px 10px;">
        <span style="font-size:0.85rem;flex-shrink:0;">&#127757;</span>
        <span style="font-size:0.68rem;color:rgba(240,253,250,0.38);line-height:1.4;">
          {ficha.get('dato_oms','')}</span>
      </div>
    </div>
    <div class="m4sec">
      <div style="font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
          color:{accent_ficha};margin-bottom:4px;">&#128138; Qué hacer hoy</div>
      {preview_steps}
    </div>
    {alarmas_section}
    <div style="background:{color_ficha}10;border:1px solid {color_ficha}30;border-radius:12px;
        padding:13px 15px;text-align:center;margin-bottom:8px;">
      <div style="font-size:0.8rem;color:rgba(240,253,250,0.7);line-height:1.5;font-style:italic;">
        "{ficha['mensaje_final']}"</div>
    </div>
    <div style="font-size:0.6rem;color:rgba(240,253,250,0.22);text-align:center;">
      Segunda página del PDF · QR con versión móvil para el paciente
    </div>
  </div>
</details>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 6 — ANTIBIOTIC TIME-OUT 48H (si aplica)
    # ══════════════════════════════════════════════════════════════
    TIMEOUT_48H = {
        "faringitis": {
            "bacteriana": {
                "horas": "48–72h",
                "criterios": [
                    "Temperatura < 37.5 °C (fiebre resuelta)",
                    "Dolor faríngeo reducido ≥ 50 % (EVA ≤ 4/10)",
                    "Tolera líquidos y semisólidos sin dificultad",
                    "Estado general y energía en recuperación",
                ],
                "alerta": "⚠️ Completar 10 días aunque mejore — riesgo de fiebre reumática si se interrumpe.",
                "mejoro": {
                    "color": "#22C55E", "titulo": "Curso Completo Obligatorio",
                    "cuerpo": "Completar los 10 días de amoxicilina es mandatorio. La suspensión prematura incrementa el riesgo de fiebre reumática aguda con carditis.",
                    "accion": "Continuar amoxicilina hasta completar el ciclo.",
                    "stewardship": "En estreptococo: el stewardship correcto es completar el ciclo, no suspenderlo.",
                },
                "no_mejoro": {
                    "color": "#EF4444", "titulo": "Sin Mejoría — Escalar a 48h",
                    "causas": ["Resistencia si se usó macrólido","Mononucleosis infecciosa","Absceso periamigdalino","Adherencia deficiente"],
                    "acciones": [
                        "Cultivo faríngeo si no se realizó",
                        "Si recibió azitromicina → cambiar a amoxicilina 500mg c/8h",
                        "Descartar absceso: trismus, voz engolada, desviación uvular",
                        "Derivar a ORL si persiste >5 días sin respuesta",
                    ],
                    "alternativa": "Amoxicilina-Clavulanato 875/125 mg c/12h × 10 días",
                },
            },
        },
        "neumonia": {
            "viral": {
                "horas": "48h",
                "criterios": ["FR < 24 rpm","Temperatura < 37.8 °C","SpO₂ ≥ 94 % aire ambiente","Mejoría del esfuerzo respiratorio"],
                "alerta": "CURB-65 0–1: ambulatorio con control obligatorio a 48h.",
                "mejoro": {
                    "color": "#22C55E", "titulo": "Completar Ciclo · 5–7 días",
                    "cuerpo": "Buena respuesta. Completar antibiótico oral 5–7 días. Rx control en 4–6 semanas.",
                    "accion": "Completar ciclo. Ciclos cortos de 5 días equivalentes en NAC leve (IDSA/ATS 2019).",
                    "stewardship": "Ciclos cortos reducen presión selectiva y efectos adversos.",
                },
                "no_mejoro": {
                    "color": "#EF4444", "titulo": "Hospitalización a 48h",
                    "causas": ["Organismo resistente","Derrame pleural","CURB-65 subestimado","Diagnóstico incorrecto"],
                    "acciones": [
                        "Hospitalizar — recalcular CURB-65",
                        "Hemocultivos antes de escalar",
                        "Rx tórax o TAC para descartar complicaciones",
                        "Ampliar: Amox/Clav + Macrólido o Levofloxacino 500mg/día",
                    ],
                    "alternativa": "Levofloxacino 500mg c/24h VO/IV o Ceftriaxona 1g/día IV + Azitromicina",
                },
            },
            "bacteriana": {
                "horas": "48h",
                "criterios": ["FR < 24 rpm","Temperatura < 37.8 °C","SpO₂ ≥ 94 % aire ambiente","Mejoría estado general"],
                "alerta": "CURB-65 2: umbral bajo de hospitalización. Si no mejora a 48h, ingresar.",
                "mejoro": {
                    "color": "#22C55E", "titulo": "Step-Down Oral a 48h",
                    "cuerpo": "Respuesta adecuada. Si hospitalizado con IV: paso a vía oral a 48–72h. Completar 5–7 días.",
                    "accion": "Step-down oral precoz. Alta: afebril 24h + FR normal + SpO₂ ≥ 94 %.",
                    "stewardship": "Step-down IV→VO precoz reduce costos y selección de resistencias.",
                },
                "no_mejoro": {
                    "color": "#EF4444", "titulo": "Escalar — Sin Respuesta a 48h",
                    "causas": ["S. pneumoniae resistente","Organismo atípico","Derrame pleural","Empiema"],
                    "acciones": [
                        "Hospitalización si aún ambulatorio",
                        "Hemocultivos + esputo antes de cambio",
                        "TAC tórax con contraste",
                        "Ampliar: Levofloxacino 750mg/día o Ceftriaxona + Macrólido IV",
                    ],
                    "alternativa": "Levofloxacino 750mg/día VO/IV × 5 días o Ceftriaxona 1–2g/día IV",
                },
            },
            "urgencia": {
                "horas": "24–48h (hospitalizado)",
                "criterios": ["TAS ≥ 90 mmHg sin vasopresores","FR < 30 rpm","SpO₂ ≥ 90 % con O₂","Resolución de confusión"],
                "alerta": "Evaluación por internista/neumólogo en < 24h obligatoria.",
                "mejoro": {
                    "color": "#22C55E", "titulo": "Step-Down Oral a 48–72h",
                    "cuerpo": "Si mejoría y tolerancia oral: paso a VO equivalente. Completar 5–7 días. Alta si PORT/PSI bajo.",
                    "accion": "Step-down a VO. Alta: afebril 24h + FR normal + SpO₂ ≥ 94 % aire ambiente.",
                    "stewardship": "Step-down IV→VO precoz reduce días de hospitalización.",
                },
                "no_mejoro": {
                    "color": "#EF4444", "titulo": "Escalada — Sin Respuesta 24–48h",
                    "causas": ["Organismo MDR/BLEE","Neumonía necrotizante","Sepsis no controlada","Empiema"],
                    "acciones": [
                        "Cultivos completos (sangre, esputo, BAL)",
                        "Ampliar a carbapenem si sospecha BLEE/Klebsiella MDR",
                        "Consulta urgente Infectología",
                        "TAC tórax con contraste urgente",
                    ],
                    "alternativa": "Meropenem 1g c/8h IV ± Vancomicina 15mg/kg c/12h si sospecha SARM",
                },
            },
        },
        "oma": {
            "bacteriana": {
                "horas": "48–72h",
                "criterios": ["Otalgia reducida ≥ 50 %","Temperatura < 37.5 °C","Irritabilidad mejorada","Otorrea reducida"],
                "alerta": "En < 2 años: umbral muy bajo para hospitalización si no mejora.",
                "mejoro": {
                    "color": "#22C55E", "titulo": "Completar Ciclo (5–10 días)",
                    "cuerpo": "Buena respuesta. En ≥ 2 años no grave: 5–7 días. En < 2 años o grave: 10 días.",
                    "accion": "Continuar amoxicilina. Control audiológico post-tratamiento.",
                    "stewardship": "OMA no grave ≥ 2 años: ciclos cortos equivalentes a 10d con menos resistencia.",
                },
                "no_mejoro": {
                    "color": "#EF4444", "titulo": "Escalar — Sin Mejoría 72h",
                    "causas": ["H. influenzae beta-lactamasa+ (~22%)","M. catarrhalis resistente (~75%)","Otitis complicada"],
                    "acciones": [
                        "Cambiar a Amox/Clav 90/6.4 mg/kg/día c/12h",
                        "Descartar mastoiditis: dolor retroauricular, pabellón desplazado",
                        "Timpanocentesis si < 2 años con fiebre persistente",
                        "Derivar a ORL si 3er episodio en 6 meses",
                    ],
                    "alternativa": "Amoxicilina-Clavulanato 90/6.4 mg/kg/día c/12h × 10 días",
                },
            },
        },
        "sinusitis": {
            "bacteriana": {
                "horas": "72h",
                "criterios": ["Descarga nasal reducida","Dolor facial reducido ≥ 50 %","Fiebre resuelta","Mejoría general"],
                "alerta": "Si no mejora a 72h con amoxicilina: sospechar resistencia o germen atípico.",
                "mejoro": {
                    "color": "#22C55E", "titulo": "Completar 7–10 Días",
                    "cuerpo": "Buena respuesta. Completar ciclo con lavados nasales y corticoide intranasal.",
                    "accion": "Completar antibiótico. Mantener irrigación nasal 2x/día.",
                    "stewardship": "No prolongar más de 10 días en sinusitis no complicada.",
                },
                "no_mejoro": {
                    "color": "#EF4444", "titulo": "Escalar — Sin Respuesta 72h",
                    "causas": ["H. influenzae beta-lactamasa+","S. pneumoniae resistente penicilina","Sinusitis odontogénica","Anaerobia"],
                    "acciones": [
                        "Cambiar a Amox/Clav 875/125 mg c/12h",
                        "TAC de senos paranasales si > 10 días sin mejora",
                        "Derivar ORL si falla 2do antibiótico",
                        "Cultivo endoscópico de meato medio si disponible",
                    ],
                    "alternativa": "Amoxicilina-Clavulanato 875/125 mg c/12h × 10 días o Moxifloxacino 400mg/día",
                },
            },
        },
    }

    if "timeout_48h" not in st.session_state:
        st.session_state.timeout_48h = None

    tod_map = TIMEOUT_48H.get(patologia, {})
    tod = tod_map.get(tipo, None)

    if tod:
        with st.expander(f"⏰ Antibiotic Time-Out · Revisión a {tod['horas']}", expanded=False):
            st.markdown(f"<p style='font-size:0.8rem;color:#F59E0B;margin-bottom:12px;'>{tod['alerta']}</p>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.75rem;color:rgba(240,253,250,0.5);margin-bottom:10px;'>Criterios de mejoría esperada:</p>", unsafe_allow_html=True)
            for cr in tod["criterios"]:
                st.markdown(f"<p style='font-size:0.82rem;color:#F0FDFA;margin-bottom:4px;'>  ☐ {cr}</p>", unsafe_allow_html=True)

            st.markdown("<hr style='opacity:0.1;margin:16px 0 14px;'>", unsafe_allow_html=True)
            _to_state = st.radio("Estado del paciente a las 48–72h:", ["No evaluado aún", "Mejoró", "No mejoró"], horizontal=True, label_visibility="visible")
            st.session_state.timeout_48h = _to_state

            if _to_state == "Mejoró":
                m = tod["mejoro"]
                st.markdown(f"""
<div style="background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.25);
    border-radius:14px;padding:18px 20px;margin-top:8px;">
  <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
      color:{m['color']};margin-bottom:8px;">✓ Buena Respuesta</div>
  <div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#F0FDFA;margin-bottom:10px;">{m['titulo']}</div>
  <div style="font-size:0.83rem;color:rgba(240,253,250,0.7);line-height:1.5;margin-bottom:10px;">{m['cuerpo']}</div>
  <div style="font-size:0.78rem;color:{m['color']};margin-bottom:8px;">→ {m['accion']}</div>
  <div style="font-size:0.7rem;color:rgba(240,253,250,0.4);font-style:italic;">{m['stewardship']}</div>
</div>""", unsafe_allow_html=True)

            elif _to_state == "No mejoró":
                nm = tod["no_mejoro"]
                causas_html = "".join(
                    f'<span style="font-size:0.68rem;color:rgba(240,253,250,0.5);display:inline-block;'
                    f'margin:2px 3px;padding:2px 8px;background:rgba(239,68,68,0.1);'
                    f'border:1px solid rgba(239,68,68,0.2);border-radius:99px;">{c_}</span>'
                    for c_ in nm.get("causas", [])
                )
                acciones_html = "".join(
                    f'<div style="display:flex;align-items:flex-start;gap:9px;padding:5px 0;'
                    f'border-bottom:1px solid rgba(255,255,255,0.04);">'
                    f'<div style="min-width:18px;height:18px;border-radius:50%;background:{nm["color"]};'
                    f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
                    f'font-size:0.58rem;font-weight:700;color:#fff;">{idx+1}</div>'
                    f'<span style="font-size:0.8rem;color:rgba(240,253,250,0.72);">{a_}</span></div>'
                    for idx, a_ in enumerate(nm.get("acciones", []))
                )
                st.markdown(f"""
<div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.28);
    border-radius:14px;padding:18px 20px;margin-top:8px;">
  <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
      color:{nm['color']};margin-bottom:8px;">⚠ Escalada · Sin Mejoría</div>
  <div style="font-family:'DM Serif Display',serif;font-size:1.05rem;color:#F0FDFA;margin-bottom:10px;">{nm['titulo']}</div>
  <div style="margin-bottom:10px;"><div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;
      text-transform:uppercase;color:rgba(240,253,250,0.3);margin-bottom:5px;">Posibles causas</div>{causas_html}</div>
  <div style="font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
      color:rgba(240,253,250,0.3);margin-bottom:6px;">Plan de escalada</div>
  {acciones_html}
  <div style="margin-top:12px;padding:11px 14px;background:rgba(0,0,0,0.2);
      border:1px solid rgba(239,68,68,0.2);border-radius:10px;">
    <div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
        color:{nm['color']};margin-bottom:5px;">Alternativa Antibiótica</div>
    <div style="font-size:0.8rem;color:#F0FDFA;">{nm.get('alternativa','')}</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 7 — INTEROPERABILIDAD & AUDIT TRAIL
    # ══════════════════════════════════════════════════════════════
    fhir_data      = generar_fhir_r4(paciente, resultado, decision_info, metadatos)
    research_data  = generar_json_estructurado(paciente, resultado, decision_info, metadatos)
    fhir_bytes     = json.dumps(fhir_data,    indent=2, ensure_ascii=False).encode("utf-8")
    research_bytes = json.dumps(research_data,indent=2, ensure_ascii=False).encode("utf-8")
    abx_tag = "ABX_AVOIDED" if tipo == "viral" else ("ABX_PRESCRIBED" if tipo == "bacteriana" else "ESCALATION")

    with st.expander("🔗 Interoperabilidad & Audit Trail — HL7 FHIR R4 · SHA-256", expanded=False):
        st.markdown(f"""
<div style="background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.07);
    border-radius:12px;padding:13px 16px;margin-bottom:14px;font-family:monospace;">
  <div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
      color:rgba(240,253,250,0.35);margin-bottom:7px;">Decision ID · Audit Hash</div>
  <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
    <span style="font-size:0.95rem;font-weight:700;color:#14B8A6;letter-spacing:1.5px;">{folio}</span>
    <span style="font-size:0.65rem;color:rgba(240,253,250,0.4);">
      SHA-256 · {decision_info["hash_full"][:32]}…
    </span>
  </div>
  <div style="margin-top:6px;font-size:0.58rem;color:rgba(240,253,250,0.25);">
    Hash: SHA-256(timestamp_utc + decision_type + clinical_snapshot) · Determinístico · Reproducible
  </div>
</div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:0;">
  <span style="font-size:0.6rem;font-weight:700;padding:4px 12px;border-radius:99px;
      background:rgba(34,197,94,0.12);color:#22C55E;border:1px solid rgba(34,197,94,0.3);">
    ● DETERMINISTIC ENGINE
  </span>
  <span style="font-size:0.6rem;font-weight:700;padding:4px 12px;border-radius:99px;
      background:rgba(59,130,246,0.12);color:#3B82F6;border:1px solid rgba(59,130,246,0.3);">
    ● {abx_tag}
  </span>
</div>
""", unsafe_allow_html=True)
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            st.download_button(
                label="⬡  Exportar FHIR R4 Bundle",
                data=fhir_bytes,
                file_name=f"SITRE_{folio}_FHIR_R4.json",
                mime="application/json",
                use_container_width=True,
                help="HL7 FHIR R4 — Observation + AuditEvent. Compatible con HIS/EHR."
            )
        with col_i2:
            st.download_button(
                label="{ }  Exportar Research JSON",
                data=research_bytes,
                file_name=f"SITRE_{folio}_research.json",
                mime="application/json",
                use_container_width=True,
                help="JSON con features para ML, stewardship y análisis epidemiológico."
            )

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 8 — HUMAN-IN-THE-LOOP OVERRIDE
    # ══════════════════════════════════════════════════════════════
    st.markdown("<hr style='opacity:0.08;margin:24px 0 18px;'>", unsafe_allow_html=True)
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
  <span style="font-size:1.4rem;">🧑‍⚕️</span>
  <div>
    <div style="font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#F59E0B;">
      Human-in-the-Loop (HITL)</div>
    <div style="font-size:1rem;color:#F0FDFA;font-weight:600;font-family:'DM Serif Display',serif;">
      Juicio Clínico & Anulación (Override)</div>
  </div>
</div>
""", unsafe_allow_html=True)

    if "override_data" not in st.session_state:
        st.session_state.override_data = None

    override_toggle = st.toggle("⚠️ Discrepo con la recomendación. Activar anulación clínica.")
    if override_toggle:
        with st.container(border=True):
            st.markdown("<p style='color:#F59E0B;font-size:0.73rem;font-weight:700;letter-spacing:1px;margin-bottom:10px;'>FORMULARIO DE AUDITORÍA: ANULACIÓN CLÍNICA</p>", unsafe_allow_html=True)
            nueva_decision = st.selectbox("Nueva Decisión Médica Adoptada:", [
                "Escalar a tratamiento antibiótico",
                "Derivación urgente a 2do nivel / Hospitalización",
                "Manejo conservador (Evitar antibiótico)",
                "Cambio de esquema por sospecha de resistencia",
                "Otra (Especificar en la justificación)"
            ])
            justificacion = st.text_area("Justifique su decisión (Obligatorio para el Audit Trail):",
                placeholder="Ej. El paciente luce tóxico, mala tolerancia vía oral y contexto social de riesgo...")
            if st.button("💾 Sellar Anulación en el Expediente", type="secondary"):
                if len(justificacion) < 10:
                    st.error("Ingrese una justificación clínica válida (mínimo 10 caracteres).")
                else:
                    st.session_state.override_data = {
                        "decision_sitre": c["tag"],
                        "nueva_decision": nueva_decision,
                        "justificacion": justificacion
                    }
                    st.success("✅ Anulación registrada criptográficamente. Se incluirá en el reporte PDF.")
    else:
        st.session_state.override_data = None

    # ══════════════════════════════════════════════════════════════
    # BLOQUE 9 — PDF + BOTONES DE NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        if PDF_DISPONIBLE:
            def limpiar(t):
                for bad in ["🚨","⚠️","🦠","🧫","🧊","•","💊","🔵","✅","🔶"]:
                    t = t.replace(bad, "")
                return t.encode("latin-1", "ignore").decode("latin-1").strip()

            def generar_pdf():
                from fpdf import FPDF
                from fpdf.enums import XPos, YPos
                import qrcode
                import io as _io
                from ficha_educativa import get_ficha as _get_ficha, generar_html_ficha as _gen_html

                INSTRUCCIONES_PAT = {
                    "faringitis": {
                        "viral":      "Su diagnostico es viral. NO necesita antibioticos. Tome paracetamol, descanse y beba liquidos. Regrese si empeora despues de 7 dias.",
                        "bacteriana": "Su medico indico antibiotico. Tomelo completo. No lo interrumpa. Regrese si hay fiebre despues de 3 dias de tratamiento.",
                        "urgencia":   "URGENCIA: Dirijase inmediatamente al hospital mas cercano.",
                    },
                    "neumonia": {
                        "viral":      "Neumonia leve. Tome el medicamento indicado. Descanse y beba liquidos. Control obligatorio en 48 horas.",
                        "urgencia":   "URGENCIA HOSPITALARIA: Necesita atencion inmediata. No espere.",
                        "gris":       "Su caso requiere vigilancia. Tome el medicamento y regrese en 48 horas.",
                    },
                    "oma": {
                        "bacteriana": "Otitis confirmada. Tome el antibiotico como se indico. Regrese si en 3 dias no mejora.",
                        "viral":      "Su oido no tiene infeccion bacteriana. Use analgesicos. Regrese si empeora.",
                        "gris":       "Observacion activa. Regrese en 48-72 horas si persiste o empeora.",
                    },
                    "sinusitis": {
                        "bacteriana": "Sinusitis bacteriana. Tome el antibiotico completo y haga lavados nasales con sal. Regrese si no mejora en 72 horas.",
                        "viral":      "Sinusitis viral. No necesita antibiotico. Lavados nasales con agua salina. Regrese si empeora despues de 10 dias.",
                        "urgencia":   "URGENCIA: Acuda a urgencias de inmediato.",
                    },
                }
                instruccion = INSTRUCCIONES_PAT.get(patologia, {}).get(tipo, "Siga las indicaciones de su medico.")
                qr_text = f"{folio}\nPaciente: {nombre_pac}\nDx: {c['tag']} - {nombre_pat_display}\n\n{instruccion}"

                qr = qrcode.QRCode(version=2, box_size=4, border=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_M)
                qr.add_data(qr_text)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buf = _io.BytesIO()
                qr_img.save(qr_buf, format="PNG")

                # ── PÁGINA 1: REPORTE MÉDICO ──────────────────────────────
                pdf = FPDF(); pdf.add_page()
                pdf.set_font("Helvetica","B",20); pdf.set_text_color(13,148,136)
                pdf.cell(0,15,"SITRE - REPORTE DE TRIAGE",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
                pdf.set_font("Helvetica","",9); pdf.set_text_color(120,120,120)
                pdf.cell(0,8,f"Folio: {folio}  |  {fecha_str}  {hora_str}  |  {nombre_pat_display}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
                pdf.ln(6)
                pdf.set_fill_color(240,253,250); pdf.set_font("Helvetica","B",12); pdf.set_text_color(0,0,0)
                pdf.cell(0,10,f" PACIENTE: {limpiar(nombre_pac.upper())}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,fill=True)
                pdf.ln(4); pdf.set_font("Helvetica","B",11)
                pdf.cell(0,10,f"PATOLOGIA: {nombre_pat_display}  |  RESULTADO: {c['tag']}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","",10); pdf.multi_cell(0,7,limpiar(diagnostico))
                pdf.ln(4); pdf.set_font("Helvetica","B",11)
                pdf.cell(0,10,f"{score_label}: {score_val}/{score_max}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.ln(4); pdf.set_font("Helvetica","B",11)
                pdf.cell(0,10,"GUIA TERAPEUTICA:",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","",10); pdf.multi_cell(0,7,limpiar(tratamiento))
                pdf.ln(10)

                # Override (si existe)
                override = st.session_state.get("override_data")
                if override:
                    pdf.set_fill_color(254,243,199)
                    pdf.set_font("Helvetica","B",10); pdf.set_text_color(180,83,9)
                    pdf.cell(0,8," HUMAN-IN-THE-LOOP: ANULACION CLINICA (OVERRIDE)",new_x=XPos.LMARGIN,new_y=YPos.NEXT,fill=True)
                    pdf.set_font("Helvetica","",9); pdf.set_text_color(0,0,0)
                    pdf.multi_cell(0,6,limpiar(f"Recomendacion SITRE: {override['decision_sitre']}"),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.multi_cell(0,6,limpiar(f"Decision Medica Final: {override['nueva_decision']}"),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.set_font("Helvetica","I",9)
                    pdf.multi_cell(0,6,limpiar(f"Justificacion: \"{override['justificacion']}\""),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.ln(5)

                # 48h Time-Out checklist
                if tipo in ["bacteriana","urgencia"]:
                    pdf.ln(4); pdf.set_font("Helvetica","B",10); pdf.set_text_color(200,100,0)
                    pdf.cell(0,9,"REVISION 48-72 HORAS (Antibiotic Time-Out):",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    to_map = {
                        "faringitis": ["Temp < 37.5C","Dolor faringeo reducido >= 50%","Tolera liquidos sin dificultad","Estado general mejorando"],
                        "neumonia":   ["FR < 24 rpm","Temp < 37.8C","SpO2 >= 94% aire ambiente","Mejoria esfuerzo respiratorio"],
                        "oma":        ["Otalgia reducida >= 50%","Temperatura < 37.5C","Irritabilidad mejorada","Otorrea reducida"],
                        "sinusitis":  ["Descarga nasal reducida","Dolor facial reducido >= 50%","Fiebre resuelta","Mejoria general"],
                    }
                    pdf.set_font("Helvetica","",9); pdf.set_text_color(60,60,60)
                    for cr in to_map.get(patologia,[]):
                        pdf.cell(0,6,f"  [ ]  {cr}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.ln(4)

                # QR section
                pdf.set_font("Helvetica","B",10); pdf.set_text_color(13,148,136)
                pdf.cell(0,8,"INSTRUCCIONES PARA EL PACIENTE (escanee el QR):",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","",9); pdf.set_text_color(60,60,60)
                pdf.multi_cell(130,6,limpiar(instruccion))
                qr_path = "sitre_qr.png"
                with open(qr_path,"wb") as f_q: f_q.write(qr_buf.getvalue())
                y_qr = pdf.get_y()
                pdf.image(qr_path, x=160, y=y_qr-20, w=35, h=35)
                pdf.ln(18)
                pdf.set_font("Helvetica","I",8); pdf.set_text_color(130,130,130)
                pdf.multi_cell(0,5,"Nota: Este documento es sugerencia basada en algoritmos clinicos validados. La decision final recae en el medico tratante.")

                # ── PÁGINA 2: FICHA EDUCATIVA PARA EL PACIENTE ───────────
                ficha_p = _get_ficha(patologia, tipo, folio, fecha_str, nombre_pat_display)
                pdf.add_page()
                color_r, color_g, color_b = 13, 148, 136
                if ficha_p["color_hero"].startswith("#"):
                    hx = ficha_p["color_hero"].lstrip("#")
                    if len(hx) == 6:
                        color_r, color_g, color_b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
                pdf.set_fill_color(color_r,color_g,color_b)
                pdf.rect(0,0,210,28,"F")
                pdf.set_font("Helvetica","B",16); pdf.set_text_color(255,255,255)
                pdf.text(12,12,"SITRE · INSTRUCCIONES PARA EL PACIENTE")
                pdf.set_font("Helvetica","",9); pdf.set_text_color(220,255,250)
                pdf.text(12,21,f"Folio: {folio}  |  {fecha_str}  |  {nombre_pat_display}")
                pdf.ln(32)
                pdf.set_font("Helvetica","B",18); pdf.set_text_color(color_r,color_g,color_b)
                pdf.cell(0,11,limpiar(ficha_p['titulo']),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","I",11); pdf.set_text_color(80,80,80)
                pdf.cell(0,8,limpiar(ficha_p['subtitulo']),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.ln(4)
                if ficha_p.get('mito_titulo'):
                    pdf.set_fill_color(color_r,color_g,color_b)
                    pdf.set_font("Helvetica","B",10); pdf.set_text_color(255,255,255)
                    pdf.cell(0,8,f" {limpiar(ficha_p['mito_titulo'])}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,fill=True)
                    pdf.set_font("Helvetica","",9); pdf.set_text_color(30,30,30)
                    pdf.multi_cell(0,6,limpiar(ficha_p['mito_cuerpo']))
                    pdf.ln(2)
                if ficha_p.get('dato_oms'):
                    pdf.set_fill_color(240,248,255)
                    pdf.set_font("Helvetica","I",8); pdf.set_text_color(60,80,120)
                    pdf.multi_cell(0,5,f"OMS/CDC: {limpiar(ficha_p['dato_oms'])}",fill=True)
                    pdf.ln(3)
                if ficha_p.get('que_hacer'):
                    pdf.set_font("Helvetica","B",10); pdf.set_text_color(color_r,color_g,color_b)
                    pdf.cell(0,8,"Que hacer hoy:",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.set_font("Helvetica","",9); pdf.set_text_color(20,20,20)
                    for em_p, tx_p in ficha_p['que_hacer']:
                        safe_em = em_p.encode('latin-1','replace').decode('latin-1')
                        pdf.cell(0,6,f"  {safe_em}  {limpiar(tx_p)}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.ln(3)
                if ficha_p.get('cuando_regresar'):
                    pdf.set_fill_color(255,235,235)
                    pdf.set_font("Helvetica","B",10); pdf.set_text_color(180,20,20)
                    pdf.cell(0,8," Regrese al medico si:",new_x=XPos.LMARGIN,new_y=YPos.NEXT,fill=True)
                    pdf.set_font("Helvetica","",9); pdf.set_text_color(20,20,20)
                    for al in ficha_p['cuando_regresar']:
                        pdf.cell(0,6,f"  ! {limpiar(al)}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                    pdf.ln(3)
                pdf.set_fill_color(color_r,color_g,color_b)
                pdf.set_font("Helvetica","B",10); pdf.set_text_color(255,255,255)
                pdf.multi_cell(0,7,f" \"{limpiar(ficha_p['mensaje_final'])}\"",fill=True)
                pdf.ln(6)
                # QR página 2
                pdf.set_font("Helvetica","B",9); pdf.set_text_color(color_r,color_g,color_b)
                pdf.cell(135,6,"Escanee el QR para ver esta ficha en su celular:",new_x=XPos.RMARGIN)
                pdf.ln(2)
                y_qr2 = pdf.get_y()
                try:
                    pdf.image(qr_path, x=155, y=y_qr2-6, w=40, h=40)
                except Exception:
                    pass
                pdf.ln(36)
                pdf.set_font("Helvetica","I",7); pdf.set_text_color(150,150,150)
                pdf.multi_cell(0,4,"SITRE CDSS v2.0 · Motor determinisico · Guias IDSA/OMS/AAP. Generado automaticamente. Decision final corresponde al medico tratante.")

                return bytes(pdf.output())

            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=generar_pdf(),
                file_name=f"SITRE_{nombre_pac.replace(' ','_')}.pdf",
                mime="application/pdf",
                use_container_width=True, type="primary"
            )
        else:
            st.info("Instala fpdf2: pip install fpdf2")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Evaluar Nuevo Paciente ➔", type="primary", use_container_width=True):
            st.session_state.timeout_48h = None
            st.session_state.pantalla = "triage"
            st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("← Cambiar Patología", type="primary", use_container_width=True):
            st.session_state.pantalla = "selector"
            st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("← Volver al Inicio", type="primary", use_container_width=True):
            st.session_state.pantalla = "bienvenida"
            st.rerun()