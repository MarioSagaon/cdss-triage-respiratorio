import streamlit as st
import base64
import json
from datetime import datetime
import streamlit.components.v1 as components
from clinical_models import PacienteIRA, PacienteNeumoniaCAP, PacienteOMA, PacienteSinusitis
from decision_engine import evaluar_paciente, evaluar_neumonia, evaluar_oma, evaluar_sinusitis
from interoperability import generar_decision_id, generar_fhir_r4, generar_json_estructurado

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
    ("abx_evitados_global", 127),   # Contador global persistente (demo seed)
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

    st.markdown("<br>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns([1,1.5,1])
    with col_b2:
        label_btn = "Procesar Diagnóstico ➔" if safety_check else "Complete la validación ⚠️"
        if st.button(label_btn, type="primary", use_container_width=True, disabled=not safety_check):
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
                        neumopatia_cronica=neumopatia, inmunocompromiso=inmuno, diabetes_mellitus=diabetes)
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

                # Tags para historial
                TAG_MAP = {"urgencia":"EMERGENCIA","viral":"VIRAL/LEVE","bacteriana":"BACTERIANA","gris":"INDETERMINADO"}

                # Incrementar contador global de antibióticos evitados
                if resultado.get("tipo") == "viral":
                    st.session_state.abx_evitados_global += 1

                st.session_state.historial.append({
                    "hora":     datetime.now().strftime("%H:%M"),
                    "nombre":   nombre_paciente.strip(),
                    "edad":     edad_input,
                    "patologia": titulo_pat,
                    "score":    score_display,
                    "tipo":     resultado.get("tipo","gris"),
                    "tag":      TAG_MAP.get(resultado.get("tipo","gris"),"—"),
                })
                st.session_state.resultado_completo = resultado
                st.session_state.nombre_paciente    = nombre_paciente.strip()
                st.session_state.paciente_obj       = p
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

        # ── CALCULADORA DE IMPACTO ────────────────────────
        abx_global = st.session_state.abx_evitados_global
        components.html(f"""
        <style>body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif;}}</style>
        <div style="background:rgba(34,197,94,0.05);border:1px solid rgba(34,197,94,0.2);
            border-radius:14px;padding:16px 20px;margin-bottom:16px;
            display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.4rem;">💚</span>
            <div>
              <div style="font-size:0.6rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;
                  color:#22C55E;margin-bottom:3px;">Impacto Stewardship · Este turno</div>
              <div style="font-size:0.82rem;color:#F0FDFA;">
                Evitaste prescribir antibióticos en <b style="color:#22C55E;">{abx_evitados_turno}</b> casos virales
                &nbsp;·&nbsp; <b style="color:#22C55E;">~{gramos_evitados}g</b> de amoxicilina fuera de la cadena resistente
              </div>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.6rem;color:rgba(240,253,250,0.35);margin-bottom:2px;">Odómetro SITRE Global</div>
            <div style="font-family:Georgia,serif;font-size:1.4rem;color:#22C55E;font-weight:700;">
              {abx_global:,} <span style="font-size:0.7rem;color:rgba(240,253,250,0.4);">Abx evitados</span>
            </div>
          </div>
        </div>
        """, height=90, scrolling=False)

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

    # Botón cambiar patología
    st.markdown("<br>", unsafe_allow_html=True)
    col_ch1,col_ch2,col_ch3 = st.columns([1,1.5,1])
    with col_ch2:
        if st.button("← Cambiar Patología", type="primary", use_container_width=True):
            st.session_state.pantalla = "selector"
            st.rerun()


# ══════════════════════════════════════════
# PANTALLA 4 — RESULTADOS
# ══════════════════════════════════════════
elif st.session_state.pantalla == "resultados":

    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
        PDF_DISPONIBLE = True
    except ImportError:
        PDF_DISPONIBLE = False

    resultado   = st.session_state.resultado_completo
    nombre_pac  = st.session_state.get("nombre_paciente","Paciente")
    paciente    = st.session_state.get("paciente_obj", None)
    patologia   = st.session_state.get("patologia","faringitis")
    tipo        = resultado.get("tipo","gris")
    diagnostico = resultado["diagnostico"]
    tratamiento = resultado["tratamiento"]

    ahora         = datetime.now()
    fecha_str     = ahora.strftime("%d %b %Y").upper()
    hora_str      = ahora.strftime("%H:%M")
    decision_info = generar_decision_id(paciente, resultado, ahora)
    folio         = decision_info["decision_id"]

    # Score labels por patología
    if patologia == "faringitis" and paciente:
        score_val = paciente.calcular_score_centor()
        score_label = "Score McIsaac"
        score_max = 5
        viral_val = paciente.contar_signos_virales()
        viral_label = "Signos Virales"
        viral_max = 7
    elif patologia == "neumonia" and paciente:
        score_val = paciente.calcular_curb65()
        score_label = "CURB-65"
        score_max = 5
        viral_val = score_val
        viral_label = "Severidad"
        viral_max = 5
    elif patologia == "oma" and paciente:
        score_val = paciente.criterios_diagnosticos()
        score_label = "Criterios Dx"
        score_max = 3
        viral_val = 1 if paciente.es_grave() else 0
        viral_label = "Gravedad"
        viral_max = 1
    else:
        score_val = 0
        score_label = "Score"
        score_max = 5
        viral_val = 0
        viral_label = "Indicador"
        viral_max = 5

    score_pct  = min(max(score_val/score_max,0),1)*100 if score_max>0 else 0
    viral_pct  = min(max(viral_val/viral_max,0),1)*100 if viral_max>0 else 0
    score_info = {"val": score_val, "max": score_max, "label": score_label}

    CONFIGS = {
        "urgencia":   {"accent":"#EF4444","glow":"rgba(239,68,68,0.3)", "bg":"rgba(239,68,68,0.07)", "tag":"EMERGENCIA",   "label":"Derivación Inmediata a Urgencias",       "emoji":"🚨","pcol":"#EF4444"},
        "viral":      {"accent":"#3B82F6","glow":"rgba(59,130,246,0.3)","bg":"rgba(59,130,246,0.07)","tag":"VIRAL / LEVE", "label":"Manejo Conservador · Sin Antibióticos",  "emoji":"🧊","pcol":"#3B82F6"},
        "bacteriana": {"accent":"#22C55E","glow":"rgba(34,197,94,0.3)", "bg":"rgba(34,197,94,0.07)", "tag":"BACTERIANA",   "label":"Indicación Antimicrobiana",              "emoji":"🦠","pcol":"#22C55E"},
        "gris":       {"accent":"#F59E0B","glow":"rgba(245,158,11,0.3)","bg":"rgba(245,158,11,0.07)","tag":"INDETERMINADO","label":"Valoración Clínica Presencial Requerida","emoji":"⚠️","pcol":"#F59E0B"},
    }
    c = CONFIGS.get(tipo, CONFIGS["gris"])

    if score_val/score_max >= 0.7 if score_max>0 else False: gauge_color="#22C55E"
    elif score_val/score_max >= 0.4 if score_max>0 else False: gauge_color="#F59E0B"
    else: gauge_color="#3B82F6"

    diag_html = diagnostico.replace("\n","<br>")
    trat_html = tratamiento.replace("\n","<br>")
    pcol = c["pcol"]

    # ── LÓGICA DE ALERTA DIABETES ──────────────────────
    banner_diabetes = ""
    if getattr(paciente, "diabetes_mellitus", False):
        if tipo == "viral":
            mensaje_dm = "Vigilancia estrecha: Infecciones virales leves pueden detonar hiperglucemia o cetoacidosis. Recomendar al paciente monitoreo estricto de glucosa en casa y no suspender insulina."
        else:
            mensaje_dm = "Alto riesgo de complicaciones invasivas o daño renal. Considerar ajuste de función renal (TFG) para la dosis del antibiótico indicado."
            
        # SIN ESPACIOS AL INICIO PARA QUE STREAMLIT NO LO HAGA CÓDIGO
        banner_diabetes = f"""
<div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3); border-radius:14px; padding:16px 20px; margin-bottom:24px; display:flex; align-items:flex-start; gap:16px; animation:fade-up 0.5s 0.2s both;">
<span style="font-size:1.6rem; line-height:1;">🔶</span>
<div>
<div style="font-size:0.65rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#F59E0B; margin-bottom:4px;">Alerta Endocrinológica · Riesgo Ajustado</div>
<div style="font-size:0.85rem; color:#F0FDFA; line-height:1.5;">{mensaje_dm}</div>
</div>
</div>
"""

    # Nombre de patología para mostrar
    NOMBRES_PAT = {"faringitis":"Faringitis","neumonia":"Neumonía CAP","oma":"Otitis Media Aguda","sinusitis":"Sinusitis Aguda"}
    nombre_pat_display = NOMBRES_PAT.get(patologia,"IRA")
    metadatos = {
        "patologia": patologia,
        "nombre_paciente": nombre_pac,
        "nombre_pat_display": nombre_pat_display,
        "score_info": score_info,
    }

    st.markdown(f"""
<style>
.res-page {{ max-width:980px; margin:0 auto; padding:44px 28px 40px; }}
.res-meta-bar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:22px; animation:fade-up 0.5s 0.1s both; }}
.meta-folio {{ font-size:0.6rem; font-weight:700; letter-spacing:3px; color:var(--teal-light); text-transform:uppercase; }}
.meta-datetime {{ font-family:'DM Serif Display',serif; font-size:1.5rem; color:var(--text); letter-spacing:-0.5px; margin-top:2px; }}
.meta-right {{ text-align:right; font-size:0.75rem; color:var(--muted); line-height:1.7; }}
.patient-bar {{ display:flex; align-items:center; justify-content:space-between; background:rgba(13,148,136,0.08); border:1px solid rgba(13,148,136,0.2); border-radius:14px; padding:16px 24px; margin-bottom:22px; animation:fade-up 0.5s 0.15s both; }}
.patient-label {{ font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--teal-light); margin-bottom:4px; }}
.patient-name {{ font-family:'DM Serif Display',serif; font-size:1.7rem; color:var(--text); line-height:1; }}
.patient-folio {{ font-size:0.72rem; color:var(--muted); letter-spacing:1px; text-align:right; line-height:1.6; }}
.res-hero {{ position:relative; border:1px solid {c["accent"]}44; border-radius:28px; overflow:hidden; margin-bottom:24px; box-shadow:0 0 80px {c["glow"]}; animation:card-in 0.7s cubic-bezier(0.23,1,0.32,1) both; }}
.res-hero-bg {{ position:absolute; inset:0; z-index:0; background:radial-gradient(ellipse at 20% 50%,{c["accent"]}18 0%,transparent 60%),radial-gradient(ellipse at 80% 50%,{c["accent"]}0c 0%,transparent 60%); animation:bg-shift 5s ease-in-out infinite alternate; }}
@keyframes bg-shift {{ from {{ opacity:0.5; }} to {{ opacity:1.0; }} }}
.res-hero-inner {{ position:relative; z-index:1; display:flex; align-items:center; gap:32px; padding:36px 40px; }}
.hero-icon {{ font-size:5rem; line-height:1; flex-shrink:0; animation:icon-pop 0.6s 0.4s cubic-bezier(0.34,1.56,0.64,1) both; filter:drop-shadow(0 0 16px {c["accent"]}); }}
@keyframes icon-pop {{ from {{ opacity:0; transform:scale(0.2) rotate(-20deg); }} to {{ opacity:1; transform:scale(1) rotate(0deg); }} }}
.hero-tag {{ display:inline-block; font-size:0.6rem; font-weight:700; letter-spacing:4px; text-transform:uppercase; color:{c["accent"]}; border:1px solid {c["accent"]}55; border-radius:99px; padding:4px 14px; margin-bottom:12px; background:{c["bg"]}; }}
.hero-label {{ font-family:'DM Serif Display',serif; font-size:clamp(1.5rem,3vw,2.2rem); color:var(--text); font-weight:400; letter-spacing:-0.5px; line-height:1.2; margin-bottom:10px; }}
.hero-diag {{ font-size:0.92rem; color:var(--muted); line-height:1.65; }}
.cards-row {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:22px; animation:fade-up 0.5s 0.3s both; }}
.info-card {{ background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:24px; }}
.info-card-label {{ font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--muted); margin-bottom:16px; }}
.gauge-number {{ font-family:'DM Serif Display',serif; font-size:3.2rem; line-height:1; margin-bottom:4px; }}
.gauge-sub {{ font-size:0.72rem; color:var(--muted); margin-bottom:16px; }}
.gauge-bar-bg {{ width:100%; height:8px; background:rgba(255,255,255,0.08); border-radius:99px; overflow:hidden; margin-bottom:8px; }}
.gauge-bar-fill {{ height:100%; border-radius:99px; background:linear-gradient(to right,{gauge_color}88,{gauge_color}); animation:fill-bar 1.2s 0.6s cubic-bezier(0.23,1,0.32,1) both; }}
@keyframes fill-bar {{ from {{ width:0%; }} to {{ width:{score_pct}%; }} }}
.viral-bar-fill {{ height:100%; border-radius:99px; background:linear-gradient(to right,#3B82F688,#3B82F6); animation:fill-viral 1.2s 0.8s cubic-bezier(0.23,1,0.32,1) both; }}
@keyframes fill-viral {{ from {{ width:0%; }} to {{ width:{viral_pct}%; }} }}
.gauge-ticks {{ display:flex; justify-content:space-between; font-size:0.58rem; color:var(--muted); margin-top:4px; }}
.tx-card {{ background:{c["bg"]}; border:1px solid {c["accent"]}33; border-radius:18px; padding:26px; margin-bottom:22px; animation:fade-up 0.5s 0.35s both; }}
.tx-label {{ font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:{c["accent"]}; margin-bottom:14px; }}
.tx-body {{ font-size:0.95rem; color:var(--text); line-height:1.8; }}
.fund-card {{ background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:22px 24px; margin-bottom:22px; animation:fade-up 0.5s 0.4s both; }}
.fund-label {{ font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }}
.fund-body {{ font-size:0.88rem; color:var(--muted); line-height:1.7; }}
#particles-canvas {{ position:fixed; inset:0; pointer-events:none; z-index:999; }}
@keyframes card-in {{ from {{ opacity:0; transform:translateY(32px) scale(0.98); }} to {{ opacity:1; transform:translateY(0) scale(1); }} }}
@keyframes fade-up {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
</style>

<canvas id="particles-canvas"></canvas>
<script>
(function() {{
    const canvas=document.getElementById('particles-canvas'); if(!canvas)return;
    const ctx=canvas.getContext('2d');
    canvas.width=window.innerWidth; canvas.height=window.innerHeight;
    const particles=[]; const color='{pcol}';
    const isViral = '{tipo}' === 'viral';

    // Confetti shapes for viral
    const confettiColors = ['#22C55E','#3B82F6','#14B8A6','#A78BFA','#F59E0B','#EC4899'];
    function spawnConfetti(){{
        particles.push({{
            x: Math.random()*canvas.width,
            y: -10,
            vx: (Math.random()-0.5)*3,
            vy: Math.random()*3+1,
            r: Math.random()*6+3,
            color: confettiColors[Math.floor(Math.random()*confettiColors.length)],
            rot: Math.random()*Math.PI*2,
            vrot: (Math.random()-0.5)*0.15,
            shape: Math.random()>0.5?'rect':'circle',
            life: Math.random()*120+100,
            age: 0,
            isConfetti: true
        }});
    }}

    function spawn(){{
        particles.push({{x:Math.random()*canvas.width,y:canvas.height+10,
            vx:(Math.random()-0.5)*1.2,vy:-(Math.random()*2.2+0.8),
            r:Math.random()*5+2,life:Math.random()*100+80,age:0,isConfetti:false}});
    }}

    function draw(){{
        ctx.clearRect(0,0,canvas.width,canvas.height);
        for(let i=particles.length-1;i>=0;i--){{
            const p=particles[i];
            p.x+=p.vx; p.y+=p.vy; p.age++;
            if(p.age>=p.life){{particles.splice(i,1);continue;}}
            const alpha=(1-p.age/p.life)*0.75;
            ctx.save();
            ctx.globalAlpha=alpha;
            if(p.isConfetti){{
                p.rot+=p.vrot;
                p.vy+=0.04; // gravity
                ctx.translate(p.x,p.y); ctx.rotate(p.rot);
                ctx.fillStyle=p.color;
                if(p.shape==='rect'){{ctx.fillRect(-p.r,-p.r/2,p.r*2,p.r);}}
                else{{ctx.beginPath();ctx.arc(0,0,p.r,0,Math.PI*2);ctx.fill();}}
            }}else{{
                ctx.fillStyle=color;
                ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();
            }}
            ctx.restore();
        }}
        requestAnimationFrame(draw);
    }}

    if(isViral){{
        // Confetti burst from top
        setTimeout(()=>{{for(let i=0;i<60;i++) setTimeout(spawnConfetti, i*25);}},200);
        setInterval(()=>{{if(particles.filter(p=>p.isConfetti).length<30) spawnConfetti();}},800);
    }} else {{
        setTimeout(()=>{{for(let i=0;i<20;i++)spawn();}},300);
        setInterval(()=>{{if(particles.length<35)spawn();}},350);
    }}
    draw();
    window.addEventListener('resize',()=>{{canvas.width=window.innerWidth;canvas.height=window.innerHeight;}});
}})();
</script>

<div class="res-page">
  <div class="res-meta-bar">
    <div>
      <div class="meta-folio">Reporte Clínico · SITRE CDSS v2.0 · {nombre_pat_display}</div>
      <div class="meta-datetime">📅 {fecha_str} &nbsp;·&nbsp; 🕒 {hora_str} hrs</div>
    </div>
    <div class="meta-right">
      <b style="color:var(--teal-light); font-family:monospace; font-size:0.85rem;">{folio}</b><br>
      <span style="font-size:0.58rem; color:rgba(240,253,250,0.35); font-family:monospace; letter-spacing:0.5px;">SHA-256·{decision_info["hash_short"]}…</span><br>
      Noreste · Coahuila / NL
    </div>
  </div>
  <div class="patient-bar">
    <div>
      <div class="patient-label">Paciente evaluado</div>
      <div class="patient-name">{nombre_pac}</div>
    </div>
    <div class="patient-folio">
      <span style="color:var(--teal-light);">●</span> Triage activo<br>
      <span style="font-family:monospace;">{folio}</span>
    </div>
  </div>
  <div class="res-hero">
    <div class="res-hero-bg"></div>
    <div class="res-hero-inner">
      <div class="hero-icon">{c["emoji"]}</div>
      <div>
        <span class="hero-tag">{c["tag"]}</span>
        <div class="hero-label">{c["label"]}</div>
        <div class="hero-diag">{diag_html}</div>
      </div>
    </div>
  </div>

  {banner_diabetes}

  <div class="cards-row">
    <div class="info-card">
      <div class="info-card-label">{score_label}</div>
      <div class="gauge-number" style="color:{gauge_color};">{score_val}<span style="font-size:1.2rem;color:var(--muted);">/{score_max}</span></div>
      <div class="gauge-bar-bg"><div class="gauge-bar-fill"></div></div>
      <div class="gauge-ticks">{"".join(f"<span>{i}</span>" for i in range(score_max+1))}</div>
    </div>
    <div class="info-card">
      <div class="info-card-label">{viral_label}</div>
      <div class="gauge-number" style="color:#3B82F6;">{viral_val}<span style="font-size:1.2rem;color:var(--muted);">/{viral_max}</span></div>
      <div class="gauge-bar-bg"><div class="viral-bar-fill"></div></div>
      <div class="gauge-ticks">{"".join(f"<span>{i}</span>" for i in range(viral_max+1))}</div>
    </div>
  </div>
  <div class="tx-card">
    <div class="tx-label">💊 Guía Terapéutica Sugerida</div>
    <div class="tx-body">{trat_html}</div>
  </div>
  <div class="fund-card">
    <div class="fund-label">📚 Referencia Clínica</div>
    <div class="fund-body">{"Score CURB-65 · British Thoracic Society (Lim et al, Thorax 2003). Validado en 1,068 pacientes. Mortalidad: CURB-65 0-1 &lt;3%, 2: 9%, ≥3: 15-40%." if patologia=="neumonia" else "Score McIsaac · Modificación del Score Centor (McIsaac et al, JAMA 2004). Estándar de oro para diagnóstico de faringitis estreptocócica." if patologia=="faringitis" else "Criterios diagnósticos de OMA · AAP/AAFP 2013 + Consenso SEIP 2023 (An Pediatr 98:362-72). Diferenciación confirmada vs probable." if patologia=="oma" else "Criterios IDSA para Rinosinusitis Bacteriana Aguda · Chow et al, Clin Infect Dis 2012;54:e72-112. Patrón temporal como diferenciador viral-bacteriano."}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── PANEL DE EXPLICABILIDAD "CAJA DE CRISTAL" ──────────────────────
    razonamiento = resultado.get("razonamiento", None)
    if razonamiento:
        pasos = razonamiento.get("pasos", [])

        # Construir HTML de pasos SIN espacios duros
        pasos_html = ""
        for paso in pasos:
            items_html = ""
            for item in paso["items"]:
                pts_badge = f'<span style="font-size:0.58rem;font-weight:700;color:{item["color"]};border:1px solid {item["color"]}44;border-radius:4px;padding:1px 6px;background:{item["color"]}11;margin-left:6px;">{item["pts"]}</span>' if item.get("pts","") else ""
                items_html += f'<div style="display:flex;align-items:center;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);"><div style="display:flex;align-items:center;gap:8px;"><div style="width:6px;height:6px;border-radius:50%;background:{item["color"]};flex-shrink:0;"></div><span style="font-size:0.78rem;color:rgba(240,253,250,0.6);">{item["label"]}</span></div><div style="display:flex;align-items:center;gap:4px;"><span style="font-size:0.72rem;font-weight:600;color:{item["color"]};">{item["status"]}</span>{pts_badge}</div></div>'

            resultado_row = f'<div style="margin-top:10px;padding:8px 12px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:3px solid {paso["resultado_color"]};"><span style="font-size:0.72rem;font-weight:700;color:{paso["resultado_color"]};letter-spacing:1px;">{paso["resultado"]}</span></div>' if paso.get("resultado") else ""

            pasos_html += f'<div style="margin-bottom:16px;padding:14px 16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;"><div style="font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#14B8A6;margin-bottom:10px;">{paso["titulo"]}</div>{items_html}{resultado_row}</div>'

        st.markdown(f"""
        <style>
        details.glass-box {{ background:rgba(255,255,255,0.02); border:1px solid rgba(20,184,166,0.2); border-radius:14px; margin-bottom: 20px; }}
        details.glass-box summary {{ display:flex; align-items:center; justify-content:space-between; padding:16px 20px; cursor:pointer; list-style:none; transition:background 0.2s; border-radius:14px; }}
        details.glass-box summary::-webkit-details-marker {{ display:none; }}
        details.glass-box summary:hover {{ background:rgba(20,184,166,0.05); }}
        details.glass-box .chevron {{ transition:transform 0.3s; font-size:0.8rem; color:#14B8A6; }}
        details.glass-box[open] .chevron {{ transform:rotate(180deg); }}
        details.glass-box[open] summary {{ border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .exp-body-content {{ padding: 16px 20px; animation:fadeIn 0.4s ease; }}
        @keyframes fadeIn{{from{{opacity:0;transform:translateY(-4px)}}to{{opacity:1;transform:translateY(0)}}}}
        </style>
        <details class="glass-box">
        <summary>
        <div style="display:flex;align-items:center;gap:14px;"><span style="font-size:1.1rem;">&#128269;</span><div><div style="font-size:0.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#14B8A6;margin-bottom:2px;">Caja de Cristal · Explicabilidad de la Decisión</div><div style="font-size:0.82rem;color:rgba(240,253,250,0.6);">Motor: {razonamiento["motor"]} &nbsp;&#183;&nbsp; Guia: {razonamiento["guia"]} &nbsp;&#183;&nbsp; Respuesta: {razonamiento["ms"]}ms</div></div></div><div style="display:flex;align-items:center;gap:10px;flex-shrink:0;"><span style="font-size:0.58rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#22C55E;border:1px solid #22C55E44;border-radius:99px;padding:3px 10px;background:#22C55E11;">&#10003; Determinista</span><span class="chevron">&#9660;</span></div>
        </summary>
        <div class="exp-body-content">
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;"><div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px 14px;"><div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(240,253,250,0.3);margin-bottom:4px;">Motor</div><div style="font-size:0.78rem;color:#F0FDFA;font-weight:600;">{razonamiento["motor"]}</div></div><div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px 14px;"><div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(240,253,250,0.3);margin-bottom:4px;">DOI</div><div style="font-size:0.75rem;color:#14B8A6;font-weight:600;">{razonamiento["doi"]}</div></div><div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px 14px;"><div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(240,253,250,0.3);margin-bottom:4px;">Tiempo de respuesta</div><div style="font-size:0.78rem;color:#F0FDFA;font-weight:600;">{razonamiento["ms"]} ms</div></div></div>
        {pasos_html}
        <div style="margin-top:4px;padding:10px 14px;background:rgba(34,197,94,0.05);border:1px solid rgba(34,197,94,0.15);border-radius:10px;"><span style="font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#22C55E;margin-right:8px;">&#10003; Sistema Determinista</span><span style="font-size:0.72rem;color:rgba(240,253,250,0.5);">{razonamiento["deterministic_note"]}</span></div><div style="margin-top:10px;padding:10px 14px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;"><div style="font-size:0.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(240,253,250,0.3);margin-bottom:5px;">Referencia Academica Completa (PubMed)</div><div style="font-size:0.75rem;color:rgba(240,253,250,0.5);line-height:1.5;font-style:italic;">{razonamiento["ref_completa"]}</div></div>
        </div>
        </details>
        """, unsafe_allow_html=True)
    # ── LÍNEA DE TIEMPO "SIN TRATAMIENTO" ─────────────────────────────
    TIMELINES = {
        "faringitis": {
            "bacteriana": [
                ("0h",  "#14B8A6", "Consulta actual", "Faringitis estreptocócica identificada. Ventana óptima de tratamiento."),
                ("48h", "#F59E0B", "Sin mejoría",     "Persistencia de fiebre y dolor intenso. Riesgo de absceso periamigdalino."),
                ("5d",  "#EF4444", "Complicación",    "Fiebre reumática aguda: riesgo de carditis en 1-3% sin tratamiento antibiótico."),
                ("3sem","#991B1B", "Secuela",         "Glomerulonefritis post-estreptocócica. Daño renal irreversible potencial."),
            ],
            "viral": [
                ("0h",  "#14B8A6", "Consulta actual", "Cuadro viral confirmado. Antibiótico NO indicado."),
                ("3d",  "#3B82F6", "Pico sintomático","Máxima carga viral. Reposo e hidratación son el tratamiento correcto."),
                ("7d",  "#22C55E", "Resolución",      "Resolución espontánea esperada. Sin secuelas con manejo conservador."),
            ],
            "urgencia": [
                ("0h",  "#EF4444", "Consulta actual", "Hipoxia o taquipnea detectada. Riesgo vital inmediato."),
                ("1h",  "#991B1B", "Crítico",         "Sin soporte de oxígeno: insuficiencia respiratoria progresiva."),
            ],
        },
        "neumonia": {
            "urgencia": [
                ("0h",  "#EF4444", "Evaluación",      "CURB-65 alto. Mortalidad estimada >15% sin hospitalización."),
                ("6h",  "#991B1B", "Deterioro",       "Hipoxemia progresiva. Riesgo de ventilación mecánica sin tratamiento IV."),
                ("24h", "#7F1D1D", "Sepsis",          "Bacteriemia con sepsis. Mortalidad sube a 30-40% sin antibiótico precoz."),
            ],
            "gris": [
                ("0h",  "#F59E0B", "Evaluación",      "Neumonía moderada. Seguimiento estrecho requerido en 48h."),
                ("48h", "#EF4444", "Revisión crítica","Sin mejoría en 48h = hospitalización obligatoria. No diferir."),
                ("7d",  "#22C55E", "Con tratamiento", "Resolución clínica esperada con antibiótico y seguimiento."),
            ],
            "viral": [
                ("0h",  "#14B8A6", "Evaluación",      "Neumonía leve (CURB-65 0-1). Mortalidad <3%. Manejo ambulatorio seguro."),
                ("48h", "#3B82F6", "Revisión",        "Control obligatorio en 48h. Si empeora: hospitalización inmediata."),
                ("6sem","#22C55E", "Resolución",      "Radiografía de control en 4-6 semanas para confirmar resolución completa."),
            ],
        },
        "oma": {
            "bacteriana": [
                ("0h",  "#14B8A6", "Diagnóstico",     "OMA confirmada. Inicio de antibiótico reduce complicaciones en 80%."),
                ("72h", "#F59E0B", "Sin antibiótico",  "Otalgia persistente, riesgo de mastoiditis incipiente."),
                ("7d",  "#EF4444", "Complicación",    "Mastoiditis aguda: extensión al hueso mastoideo. Requiere hospitalización."),
                ("3sem","#991B1B", "Secuela",         "Hipoacusia conductiva de transmisión. Riesgo de daño permanente."),
            ],
            "gris": [
                ("0h",  "#F59E0B", "OMA probable",    "2/3 criterios. Observación activa 48-72h antes de antibiótico."),
                ("48h", "#14B8A6", "Revisión",        "Si mejora: continuar observación. Si empeora: iniciar antibiótico."),
            ],
            "viral": [
                ("0h",  "#3B82F6", "Sin criterios",   "No cumple OMA. Probable viral. Manejo sintomático."),
                ("7d",  "#22C55E", "Resolución",      "Curación espontánea esperada. Sin antibiótico necesario."),
            ],
        },
        "sinusitis": {
            "bacteriana": [
                ("0h",  "#14B8A6", "Diagnóstico",     "Sinusitis bacteriana confirmada. Antibiótico reduce duración 2-3 días."),
                ("5d",  "#F59E0B", "Sin mejoría",     "Persistencia sin antibiótico. Riesgo de extensión a senos adyacentes."),
                ("14d", "#EF4444", "Complicación",    "Celulitis orbitaria o sinusitis frontal: emergencia que requiere TAC urgente."),
                ("30d", "#991B1B", "Secuela",         "Sinusitis crónica. Requiere cirugía endoscópica en >20% de casos."),
            ],
            "viral": [
                ("0h",  "#3B82F6", "Diagnóstico",     "Rinosinusitis viral. 80-85% resuelve espontáneamente sin antibiótico."),
                ("7d",  "#14B8A6", "Mejoría",         "Reducción progresiva de síntomas. Irrigación nasal acelera recuperación."),
                ("10d", "#F59E0B", "Vigilancia",      "Si a día 10 no mejora o empeora: reevaluar etiología bacteriana."),
            ],
            "urgencia": [
                ("0h",  "#EF4444", "Banderas rojas",  "Edema periorbitario o rigidez nucal. Posible extensión orbitaria/intracraneal."),
                ("2h",  "#991B1B", "Urgencia",        "Sin TAC urgente y antibiótico IV: riesgo de absceso cerebral o ceguera."),
            ],
        },
    }

    timeline_pasos = TIMELINES.get(patologia, {}).get(tipo, TIMELINES.get(patologia, {}).get("viral", []))

    if timeline_pasos and tipo != "gris":
        pasos_html = ""
        for i, (tiempo, color, titulo, desc) in enumerate(timeline_pasos):
            es_ultimo = i == len(timeline_pasos) - 1
            linea_color = "#1A2E2E" if es_ultimo else color
            pasos_html += f"""
            <div style="display:flex; gap:0; align-items:flex-start;">
              <div style="display:flex; flex-direction:column; align-items:center; flex-shrink:0; width:44px;">
                <div style="width:12px; height:12px; border-radius:50%; background:{color};
                    box-shadow:0 0 8px {color}88; margin-top:4px; flex-shrink:0;"></div>
                {"" if es_ultimo else f'<div style="width:2px; flex:1; min-height:32px; background:linear-gradient({color},{linea_color}); margin:4px 0;"></div>'}
              </div>
              <div style="padding-bottom:{"0" if es_ultimo else "18px"}; flex:1;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                  <span style="font-size:0.62rem; font-weight:700; letter-spacing:2px; color:{color};
                      border:1px solid {color}55; border-radius:99px; padding:2px 8px; background:{color}15;">{tiempo}</span>
                  <span style="font-size:0.85rem; font-weight:600; color:#F0FDFA;">{titulo}</span>
                </div>
                <div style="font-size:0.8rem; color:rgba(240,253,250,0.5); line-height:1.5;">{desc}</div>
              </div>
            </div>"""

        tl_height = 80 + len(timeline_pasos) * 72
        components.html(f"""
        <style>
          body {{ margin:0; padding:0; background:transparent; font-family:'DM Sans',sans-serif; }}
        </style>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
            border-radius:18px; padding:22px 24px;">
          <div style="font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase;
              color:rgba(240,253,250,0.35); margin-bottom:18px;">
            &#9201; Progresión clínica sin tratamiento adecuado
          </div>
          {pasos_html}
        </div>
        """, height=tl_height, scrolling=False)

    # ── SEMÁFORO DE RESISTENCIA ANTIMICROBIANA ─────────────────────────
    # Datos basados en: Red PUCRA 2024 (UNAM), Hospital Universitario Monterrey NL,
    # SIREVA II OPS/OMS, y guías IDSA/SSA.
    # Arquitectura lista para conectar a SINAVE/InDRE vía API REST.
    AMR_DATA = {
        "faringitis": {
            "titulo": "Resistencia AMR · Patógenos IRA Alta · Noreste MX",
            "fuente": "Red PUCRA 2024 · SIREVA II OPS · Hospital Universitario Monterrey",
            "patogenos": [
                {"nombre": "S. pyogenes (Estreptococo A)",  "abx": "Amoxicilina",   "resistencia": 2,  "nivel": "BAJA",   "color": "#22C55E", "nota": "Primera línea segura. Sin resistencia clínica significativa reportada."},
                {"nombre": "S. pyogenes (Estreptococo A)",  "abx": "Macrólidos",    "resistencia": 18, "nivel": "MEDIA",  "color": "#F59E0B", "nota": "Resistencia a eritromicina/azitromicina en aumento. Usar solo en alérgicos a penicilina."},
                {"nombre": "S. pneumoniae",                  "abx": "Penicilina",    "resistencia": 22, "nivel": "MEDIA",  "color": "#F59E0B", "nota": "Resistencia intermedia 15-30% según SIREVA II México 2024."},
            ]
        },
        "neumonia": {
            "titulo": "Resistencia AMR · Neumonía Comunitaria · Noreste MX",
            "fuente": "Red PUCRA 2024 · Hospital Universitario Monterrey NL · INRE",
            "patogenos": [
                {"nombre": "S. pneumoniae",   "abx": "Amoxicilina",      "resistencia": 12, "nivel": "BAJA",   "color": "#22C55E", "nota": "Primera línea aún efectiva para CAP ambulatoria en la región."},
                {"nombre": "S. pneumoniae",   "abx": "Macrólidos",       "resistencia": 31, "nivel": "ALTA",   "color": "#EF4444", "nota": "Alta resistencia. Evitar monoterapia con azitromicina en NAC."},
                {"nombre": "H. influenzae",   "abx": "Ampicilina",       "resistencia": 24, "nivel": "MEDIA",  "color": "#F59E0B", "nota": "Productores de beta-lactamasas en aumento. Preferir Amox/Clav."},
                {"nombre": "K. pneumoniae",   "abx": "Cefalosporinas 3G", "resistencia": 38, "nivel": "ALTA",   "color": "#EF4444", "nota": "BLEE en 36% según PUCRA 2024. Hospitalización con carbapenem si sospecha."},
            ]
        },
        "oma": {
            "titulo": "Resistencia AMR · Otitis Media Aguda · Noreste MX",
            "fuente": "Consenso SEIP 2023 · SIREVA II · Datos regionales NL/Coahuila",
            "patogenos": [
                {"nombre": "S. pneumoniae",  "abx": "Amoxicilina",       "resistencia": 15, "nivel": "BAJA",   "color": "#22C55E", "nota": "Amoxicilina sigue siendo primera línea efectiva a dosis altas."},
                {"nombre": "H. influenzae",  "abx": "Amoxicilina",       "resistencia": 22, "nivel": "MEDIA",  "color": "#F59E0B", "nota": "Productores de beta-lactamasas ~16%. Si falla: Amox/Clav."},
                {"nombre": "M. catarrhalis", "abx": "Amoxicilina",       "resistencia": 75, "nivel": "ALTA",   "color": "#EF4444", "nota": "Alta resistencia intrínseca. Sensible a Amox/Clav y TMP-SMX."},
            ]
        },
        "sinusitis": {
            "titulo": "Resistencia AMR · Rinosinusitis Bacteriana · Noreste MX",
            "fuente": "Guías IDSA 2012 · PRAN México · Datos PUCRA Tamaulipas/NL",
            "patogenos": [
                {"nombre": "S. pneumoniae",  "abx": "Amoxicilina",       "resistencia": 18, "nivel": "BAJA",   "color": "#22C55E", "nota": "Primera línea IDSA. Efectiva en 80% de sinusitis bacteriana."},
                {"nombre": "S. pneumoniae",  "abx": "Macrólidos",        "resistencia": 35, "nivel": "ALTA",   "color": "#EF4444", "nota": "Alta resistencia en México. NO usar como monoterapia."},
                {"nombre": "H. influenzae",  "abx": "Ampicilina",        "resistencia": 24, "nivel": "MEDIA",  "color": "#F59E0B", "nota": "Si falla amoxicilina en 72h: cambiar a Amox/Clav o fluoroquinolona."},
            ]
        },
    }

    amr = AMR_DATA.get(patologia, AMR_DATA["faringitis"])

    barras_html = ""
    for pat in amr["patogenos"]:
        r = pat["resistencia"]
        col_r = pat["color"]
        barras_html += f"""
        <div style="margin-bottom:18px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div>
              <span style="font-size:0.8rem; font-weight:600; color:#F0FDFA;">{pat['nombre']}</span>
              <span style="font-size:0.72rem; color:rgba(240,253,250,0.4); margin-left:8px;">vs {pat['abx']}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:0.62rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
                  color:{col_r}; border:1px solid {col_r}55; border-radius:99px; padding:2px 8px; background:{col_r}15;">{pat['nivel']}</span>
              <span style="font-family:'DM Serif Display',serif; font-size:1.1rem; color:{col_r}; font-weight:700;">{r}%</span>
            </div>
          </div>
          <div style="width:100%; height:6px; background:rgba(255,255,255,0.07); border-radius:99px; overflow:hidden; margin-bottom:5px;">
            <div style="width:{r}%; height:100%; background:linear-gradient(to right,{col_r}88,{col_r}); border-radius:99px;
                transition:width 1s ease;"></div>
          </div>
          <div style="font-size:0.73rem; color:rgba(240,253,250,0.38); line-height:1.4;">{pat['nota']}</div>
        </div>"""

    amr_height = 120 + len(amr["patogenos"]) * 88
    components.html(f"""
    <style>
      body {{ margin:0; padding:0; background:transparent; font-family:'DM Sans',sans-serif; }}
    </style>
    <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
        border-radius:18px; padding:22px 24px;">

      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:18px; flex-wrap:wrap; gap:10px;">
        <div>
          <div style="font-size:0.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase;
              color:rgba(240,253,250,0.35); margin-bottom:5px;">&#129440; Semaforo de Resistencia Antimicrobiana</div>
          <div style="font-size:1rem; color:#F0FDFA; font-weight:600;">{amr["titulo"]}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.58rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
              color:#14B8A6; border:1px solid rgba(13,148,136,0.35); border-radius:99px;
              padding:3px 10px; background:rgba(13,148,136,0.08); display:inline-block; margin-bottom:5px;">
            Demo · SINAVE-Ready
          </div>
          <div style="font-size:0.62rem; color:rgba(240,253,250,0.3); line-height:1.4;">{amr["fuente"]}</div>
        </div>
      </div>

      <div style="display:flex; gap:8px; margin-bottom:18px; flex-wrap:wrap;">
        <span style="font-size:0.6rem; font-weight:700; padding:3px 10px; border-radius:99px;
            background:rgba(34,197,94,0.12); color:#22C55E; border:1px solid rgba(34,197,94,0.35);">&#9679; BAJA &lt;20%</span>
        <span style="font-size:0.6rem; font-weight:700; padding:3px 10px; border-radius:99px;
            background:rgba(245,158,11,0.12); color:#F59E0B; border:1px solid rgba(245,158,11,0.35);">&#9679; MEDIA 20-34%</span>
        <span style="font-size:0.6rem; font-weight:700; padding:3px 10px; border-radius:99px;
            background:rgba(239,68,68,0.12); color:#EF4444; border:1px solid rgba(239,68,68,0.35);">&#9679; ALTA &ge;35%</span>
      </div>

      {barras_html}

      <div style="margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.06);
          font-size:0.65rem; color:rgba(240,253,250,0.22); line-height:1.5;">
        Datos basados en evidencia para demo. Arquitectura lista para integracion con API REST de SINAVE/InDRE.
        Actualizacion automatica proyectada en Fase 3 del roadmap SITRE.
      </div>
    </div>
    """, height=amr_height, scrolling=False)

    # Banner epidemiológico
    st.markdown("""
    <div style="max-width:980px; margin:-10px auto 22px; display:flex; gap:12px; flex-wrap:wrap;">
      <div style="flex:1; min-width:260px; display:flex; align-items:center; gap:12px;
          background:rgba(13,148,136,0.07); border:1px solid rgba(13,148,136,0.22);
          border-radius:12px; padding:12px 18px;">
        <span style="font-size:1.3rem; flex-shrink:0;">📍</span>
        <div>
          <div style="font-size:0.58rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#14B8A6; margin-bottom:3px;">Vigilancia Epidemiológica · Noreste MX</div>
          <div style="font-size:0.83rem; color:#F0FDFA; line-height:1.5;">Alta circulación de <b>Influenza A</b>, <b>VSR</b> y <b>Rinovirus</b> en Coahuila y Nuevo León.</div>
        </div>
      </div>
      <div style="display:flex; flex-direction:column; justify-content:center; align-items:center;
          background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
          border-radius:12px; padding:12px 22px; min-width:160px; text-align:center;">
        <div style="font-size:1.5rem; margin-bottom:4px;">🌎</div>
        <div style="font-size:0.58rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:rgba(240,253,250,0.45); margin-bottom:2px;">Región detectada</div>
        <div style="font-family:'DM Serif Display',serif; font-size:1rem; color:#F0FDFA;">Coahuila / NL</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── INTEROPERABILIDAD & AUDIT TRAIL ───────────────────────────────────────
    fhir_data       = generar_fhir_r4(paciente, resultado, decision_info, metadatos)
    research_data   = generar_json_estructurado(paciente, resultado, decision_info, metadatos)
    fhir_bytes      = json.dumps(fhir_data,     indent=2, ensure_ascii=False).encode("utf-8")
    research_bytes  = json.dumps(research_data, indent=2, ensure_ascii=False).encode("utf-8")
    abx_tag = "ABX_AVOIDED" if tipo == "viral" else ("ABX_PRESCRIBED" if tipo == "bacteriana" else "ESCALATION")

    st.markdown(f"""
<div style="max-width:980px; margin:0 auto 24px; background:rgba(13,148,136,0.05);
    border:1px solid rgba(13,148,136,0.25); border-radius:20px; padding:24px 28px;
    animation:fade-up 0.5s 0.55s both;">

  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:18px;">
    <div style="display:flex; align-items:center; gap:12px;">
      <span style="font-size:1.4rem;">🔗</span>
      <div>
        <div style="font-size:0.58rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#14B8A6;">
          Interoperabilidad &amp; Audit Trail
        </div>
        <div style="font-size:0.8rem; color:rgba(240,253,250,0.55); margin-top:2px;">
          HL7 FHIR R4 · Structured JSON · SHA-256 Integrity
        </div>
      </div>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
      <span style="font-size:0.58rem; font-weight:700; padding:4px 12px; border-radius:99px;
          background:rgba(34,197,94,0.12); color:#22C55E; border:1px solid rgba(34,197,94,0.3);">
        ● DETERMINISTIC ENGINE
      </span>
      <span style="font-size:0.58rem; font-weight:700; padding:4px 12px; border-radius:99px;
          background:rgba(59,130,246,0.12); color:#3B82F6; border:1px solid rgba(59,130,246,0.3);">
        ● {abx_tag}
      </span>
    </div>
  </div>

  <div style="background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.07);
      border-radius:12px; padding:14px 18px; margin-bottom:16px; font-family:monospace;">
    <div style="font-size:0.58rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
        color:rgba(240,253,250,0.4); margin-bottom:8px;">Decision ID · Audit Hash</div>
    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
      <span style="font-size:1rem; font-weight:700; color:#14B8A6; letter-spacing:1.5px;">{folio}</span>
      <span style="font-size:0.68rem; color:rgba(240,253,250,0.45);">
        SHA-256 · {decision_info["hash_full"][:32]}…
      </span>
    </div>
    <div style="margin-top:8px; font-size:0.62rem; color:rgba(240,253,250,0.3); line-height:1.5;">
      Hash: SHA-256(timestamp_utc + decision_type + clinical_snapshot) · Algoritmo: determinístico · Reproducible
    </div>
  </div>

  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:0px;">
    <div style="background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.2);
        border-radius:12px; padding:14px 16px;">
      <div style="font-size:0.58rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
          color:#3B82F6; margin-bottom:6px;">⬡ FHIR R4 Bundle</div>
      <div style="font-size:0.75rem; color:rgba(240,253,250,0.55); line-height:1.5;">
        Observation + AuditEvent · HL7 R4 · SNOMED/LOINC<br>
        <span style="color:rgba(240,253,250,0.3);">Compatible con HIS/EHR hospitalarios</span>
      </div>
    </div>
    <div style="background:rgba(34,197,94,0.06); border:1px solid rgba(34,197,94,0.2);
        border-radius:12px; padding:14px 16px;">
      <div style="font-size:0.58rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
          color:#22C55E; margin-bottom:6px;">{"{ }"} Research JSON</div>
      <div style="font-size:0.75rem; color:rgba(240,253,250,0.55); line-height:1.5;">
        Features listas para ML · Stewardship · DOIs<br>
        <span style="color:rgba(240,253,250,0.3);">Listo para análisis epidemiológico / Python / R</span>
      </div>
    </div>
  </div>

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
            help="HL7 FHIR R4 — Observation + AuditEvent. Compatible con sistemas HIS/EHR hospitalarios.",
        )
    with col_i2:
        st.download_button(
            label="{ }  Exportar Research JSON",
            data=research_bytes,
            file_name=f"SITRE_{folio}_research.json",
            mime="application/json",
            use_container_width=True,
            help="JSON estructurado con features para ML, stewardship antimicrobiano y análisis epidemiológico.",
        )

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Botones
    col_a, col_b, col_c = st.columns([1,1.2,1])
    with col_b:
        if PDF_DISPONIBLE:
            def limpiar(t):
                for bad in ["🚨","⚠️","🦠","🧫","🧊","镜","•","💊","🔵","✅"]:
                    t = t.replace(bad,"")
                return t.encode("latin-1","ignore").decode("latin-1").strip()

            def generar_pdf():
                from fpdf import FPDF
                from fpdf.enums import XPos, YPos
                import qrcode
                import io as _io

                # Generar QR con instrucciones para el paciente
                INSTRUCCIONES_PAT = {
                    "faringitis": {
                        "viral":      "Su diagnostico es viral. NO necesita antibioticos. Tome paracetamol para la fiebre, descanse y tome mucho liquido. Regrese si empeora despues de 7 dias.",
                        "bacteriana": "Su medico indico tratamiento antibiotico. Tomelo completo aunque se sienta mejor. No lo interrumpa. Regrese si hay fiebre mayor 3 dias de tratamiento.",
                        "urgencia":   "URGENCIA: Dirijase inmediatamente a urgencias del hospital mas cercano.",
                    },
                    "neumonia": {
                        "viral":      "Su neumonia es leve. Tome el antibiotico recetado por su medico. Descanse, tome liquidos. Regrese en 48 horas o antes si tiene dificultad para respirar.",
                        "urgencia":   "URGENCIA HOSPITALARIA: Necesita atencion hospitalaria inmediata. No espere.",
                        "gris":       "Su caso requiere vigilancia. Tome el medicamento indicado y regrese en 48 horas. Si tiene dificultad para respirar, vaya a urgencias.",
                    },
                    "oma": {
                        "bacteriana": "Otitis media detectada. Tome el antibiotico exactamente como se indico. Use analgesicos para el dolor. Regrese si en 3 dias no hay mejoria.",
                        "viral":      "Su oido no tiene infeccion bacteriana. Use analgesicos para el dolor. Regrese si empeora o aparece fiebre alta.",
                        "gris":       "Observacion activa. Si el dolor de oido persiste o empeora en 48-72 horas, regrese con su medico.",
                    },
                    "sinusitis": {
                        "bacteriana": "Sinusitis bacteriana. Tome el antibiotico completo. Lave su nariz con solucion salina. Regrese si en 72 horas no mejora.",
                        "viral":      "Su sinusitis es viral. No necesita antibiotico. Lave su nariz con agua salina, use descongestionante. Regrese si empeora despues de 10 dias.",
                        "urgencia":   "URGENCIA: Tiene signos de complicacion. Acuda a urgencias de inmediato.",
                    },
                }
                instruccion = INSTRUCCIONES_PAT.get(patologia, {}).get(tipo, "Siga las indicaciones de su medico y regrese si sus sintomas empeoran.")
                qr_text = f"{folio}\nPaciente: {nombre_pac}\nDx: {c['tag']} - {nombre_pat_display}\n\n{instruccion}"

                qr = qrcode.QRCode(version=2, box_size=4, border=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_M)
                qr.add_data(qr_text)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buf = _io.BytesIO()
                qr_img.save(qr_buf, format="PNG")
                qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()

                pdf = FPDF(); pdf.add_page()
                # Header
                pdf.set_font("Helvetica","B",20); pdf.set_text_color(13,148,136)
                pdf.cell(0,15,"SITRE - REPORTE DE TRIAGE",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
                pdf.set_font("Helvetica","",9); pdf.set_text_color(120,120,120)
                pdf.cell(0,8,f"Folio: {folio}  |  {fecha_str}  {hora_str}  |  {nombre_pat_display}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
                pdf.ln(6); pdf.set_fill_color(240,253,250)
                pdf.set_font("Helvetica","B",12); pdf.set_text_color(0,0,0)
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

                # QR section
                pdf.set_font("Helvetica","B",10); pdf.set_text_color(13,148,136)
                pdf.cell(0,8,"INSTRUCCIONES PARA EL PACIENTE (escanee el QR):",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","",9); pdf.set_text_color(60,60,60)
                pdf.multi_cell(130,6,limpiar(instruccion))
                # Save QR image and embed
                qr_path = "sitre_qr.png"
                with open(qr_path, "wb") as f:
                    f.write(qr_buf.getvalue())
                y_before = pdf.get_y()
                pdf.image(qr_path, x=160, y=y_before-24, w=35, h=35)
                pdf.ln(14); pdf.set_font("Helvetica","I",8); pdf.set_text_color(130,130,130)
                pdf.multi_cell(0,5,"Nota: Este documento es una sugerencia basada en algoritmos clinicos validados. La decision final recae en el medico tratante.")
                return bytes(pdf.output())

            st.download_button(label="📥 Descargar Reporte PDF", data=generar_pdf(),
                file_name=f"SITRE_{nombre_pac.replace(' ','_')}.pdf",
                mime="application/pdf", use_container_width=True, type="primary")
        else:
            st.info("Instala fpdf2: pip install fpdf2")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Evaluar Nuevo Paciente ➔", type="primary", use_container_width=True):
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