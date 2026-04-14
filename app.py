import streamlit as st
import base64
from datetime import datetime
import streamlit.components.v1 as components
from clinical_models import PacienteIRA
from decision_engine import evaluar_paciente

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
    "Caso Viral Clásico": {
        "nombre": "Ana Martínez López",
        "edad": 22, "dias": 3, "fr": 17, "sat": 98.5,
        "fiebre": False, "exudado": False, "adenopatia": False,
        "tos": True, "rinorrea": True, "disfonia": True,
        "conjuntivitis": False, "mialgias": True, "exantema": False, "nauseas": False,
        "neumopatia": False, "inmuno": False,
    },
    "Caso Bacteriano (McIsaac Alto)": {
        "nombre": "Carlos Rodríguez Vega",
        "edad": 27, "dias": 4, "fr": 19, "sat": 96.0,
        "fiebre": True, "exudado": True, "adenopatia": True,
        "tos": False, "rinorrea": False, "disfonia": False,
        "conjuntivitis": False, "mialgias": False, "exantema": False, "nauseas": False,
        "neumopatia": False, "inmuno": False,
    },
    "Caso Urgencia (Banderas Rojas)": {
        "nombre": "Roberto Jiménez Torres",
        "edad": 65, "dias": 6, "fr": 28, "sat": 87.0,
        "fiebre": True, "exudado": False, "adenopatia": False,
        "tos": True, "rinorrea": False, "disfonia": False,
        "conjuntivitis": False, "mialgias": True, "exantema": False, "nauseas": True,
        "neumopatia": True, "inmuno": False,
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
    ("resultado_completo", None),
    ("nombre_paciente", ""),
    ("paciente_obj", None),
    ("historial", []),          # ← lista de dicts con cada triage
    ("demo_caso", None),        # ← caso demo seleccionado
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

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
section[data-testid="stSidebar"],
.stApp { background: var(--bg) !important; color: var(--text) !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden !important; }
body { font-family: 'DM Sans', sans-serif !important; }

/* Inputs */
div[data-testid="stNumberInput"] label,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] input {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 1rem !important;
}
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px var(--teal-glow) !important;
    outline: none !important;
}

/* Selectbox */
div[data-testid="stSelectbox"] label { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }
div[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}

/* Toggles */
div[data-testid="stToggle"] label { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }
div[data-testid="stToggle"] span[data-checked="true"] { background-color: var(--teal) !important; }

/* Checkbox */
div[data-testid="stCheckbox"] label { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }

/* Botones */
div.stButton > button[kind="primary"],
div[data-testid="stDownloadButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    background: transparent !important;
    color: var(--teal-light) !important;
    border: 1.5px solid var(--teal) !important;
    border-radius: 100px !important;
    padding: 14px 40px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    transition: all 0.3s cubic-bezier(0.23,1,0.32,1) !important;
    box-shadow: 0 0 24px var(--teal-glow) !important;
    width: 100% !important;
}
div.stButton > button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] > button:hover {
    background: var(--teal) !important;
    color: #fff !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 0 48px var(--teal-glow) !important;
}
div.stButton > button:disabled { opacity: 0.4 !important; cursor: not-allowed !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--teal); border-radius: 99px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# PANTALLA 1 — BIENVENIDA
# ══════════════════════════════════════════
if st.session_state.pantalla == "bienvenida":

    webp_b64 = get_base64("fondo_sitre.webp")
    logo_b64 = get_base64("logo_sitre_transparente.png")

    fondo_css = ""
    if webp_b64:
        fondo_css = f"""
        #fondo-sitre {{
            position: fixed; inset: 0;
            background: url('data:image/webp;base64,{webp_b64}') center/cover no-repeat;
            filter: brightness(0.22) saturate(1.4);
            z-index: -10;
        }}
        """

    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" class="sitre-logo" alt="SITRE Logo">'
        if logo_b64 else '<div class="sitre-logo-fallback">🫁</div>'
    )

    st.markdown(f"""
    <style>
    {fondo_css}
    .welcome-wrap {{
        min-height: 82vh;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 20px 20px 0px; position: relative;
    }}
    .welcome-wrap::before {{
        content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
        width: 1px; height: 60px; background: linear-gradient(to bottom, transparent, var(--teal));
    }}
    .sitre-logo {{
        width: 175px; height: 175px; object-fit: contain;
        filter: drop-shadow(0 0 16px var(--teal)) drop-shadow(0 0 40px rgba(13,148,136,0.4));
        animation: pulse-glow 4s ease-in-out infinite, spin-slow 45s linear infinite;
        margin-bottom: 10px;
    }}
    .sitre-logo-fallback {{ font-size: 100px; margin-bottom: 20px; animation: pulse-glow 4s ease-in-out infinite; }}
    @keyframes pulse-glow {{
        0%,100% {{ filter: drop-shadow(0 0 12px var(--teal)) drop-shadow(0 0 30px rgba(13,148,136,0.3)); }}
        50%      {{ filter: drop-shadow(0 0 22px var(--teal-light)) drop-shadow(0 0 55px rgba(20,184,166,0.55)); }}
    }}
    @keyframes spin-slow {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    .welcome-eyebrow {{
        font-size: 0.65rem; font-weight: 500; letter-spacing: 6px; text-transform: uppercase;
        color: var(--teal-light); margin-bottom: 5px; opacity: 0; animation: fade-up 0.8s 0.2s forwards;
    }}
    .welcome-title {{
        font-family: 'DM Serif Display', serif;
        font-size: clamp(3.5rem, 8vw, 5.5rem); font-weight: 400; color: var(--text);
        line-height: 1; letter-spacing: -3px; text-align: center;
        margin-bottom: 5px; opacity: 0; animation: fade-up 0.8s 0.4s forwards;
    }}
    .welcome-title em {{ font-style: italic; color: var(--teal-light); }}
    .welcome-subtitle {{
        font-size: 0.95rem; font-weight: 300; color: var(--muted); letter-spacing: 2px;
        text-align: center; margin-bottom: 20px; opacity: 0; animation: fade-up 0.8s 0.6s forwards;
    }}
    .welcome-pills {{
        display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;
        margin-bottom: 25px; opacity: 0; animation: fade-up 0.8s 0.8s forwards;
    }}
    .pill {{
        font-size: 0.65rem; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase;
        color: var(--teal-light); border: 1px solid rgba(13,148,136,0.4);
        border-radius: 99px; padding: 5px 14px; background: rgba(13,148,136,0.08);
    }}
    .welcome-wrap::after {{
        content: ''; position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%);
        width: 1px; height: 50px; background: linear-gradient(to top, transparent, var(--teal));
    }}
    @keyframes fade-up {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
    <div id="fondo-sitre"></div>
    <div class="welcome-wrap">
        {logo_html}
        <p class="welcome-eyebrow">Sistema de Triage Respiratorio</p>
        <h1 class="welcome-title">SI<em>TRE</em></h1>
        <p class="welcome-subtitle">Soporte a la Decisión Clínica</p>
        <div class="welcome-pills">
            <span class="pill">Score McIsaac</span>
            <span class="pill">Stewardship Antibiótico</span>
            <span class="pill">Triage en Tiempo Real</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='margin-top:30px;'>", unsafe_allow_html=True)
        if st.button("Iniciar Triage ➔", type="primary", use_container_width=True):
            st.session_state.pantalla = "triage"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Hexágonos animados
    components.html("""
    <canvas id="hx" style="position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:9998;"></canvas>
    <script>
    (function(){
        const cv=document.getElementById('hx'); if(!cv)return;
        const ctx=cv.getContext('2d');
        function resize(){cv.width=window.innerWidth;cv.height=window.innerHeight;} resize();
        const hexes=[],N=24,C='20,184,166';
        function mk(){return{x:Math.random()*cv.width,y:Math.random()*cv.height,s:Math.random()*30+8,vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,r:Math.random()*Math.PI*2,vr:(Math.random()-.5)*.004,a:Math.random()*.11+.03,p:Math.random()*Math.PI*2};}
        for(let i=0;i<N;i++)hexes.push(mk());
        function hex(x,y,s,r,a){ctx.save();ctx.translate(x,y);ctx.rotate(r);ctx.beginPath();for(let i=0;i<6;i++){const ang=Math.PI/3*i;i?ctx.lineTo(s*Math.cos(ang),s*Math.sin(ang)):ctx.moveTo(s*Math.cos(ang),s*Math.sin(ang));}ctx.closePath();ctx.strokeStyle='rgba('+C+','+a+')';ctx.lineWidth=1;ctx.stroke();ctx.restore();}
        function loop(){ctx.clearRect(0,0,cv.width,cv.height);hexes.forEach(h=>{h.x+=h.vx;h.y+=h.vy;h.r+=h.vr;h.p+=.011;const a=h.a*(.55+.45*Math.sin(h.p));if(h.x<-80)h.x=cv.width+80;else if(h.x>cv.width+80)h.x=-80;if(h.y<-80)h.y=cv.height+80;else if(h.y>cv.height+80)h.y=-80;hex(h.x,h.y,h.s,h.r,a);});requestAnimationFrame(loop);}
        loop(); window.addEventListener('resize',resize);
    })();
    </script>
    """, height=0, scrolling=False)


# ══════════════════════════════════════════
# PANTALLA 2 — FORMULARIO TRIAGE
# ══════════════════════════════════════════
elif st.session_state.pantalla == "triage":

    # ── Cargar demo si hay uno seleccionado ──
    demo = st.session_state.get("demo_caso")

    st.markdown("""
    <style>
    .triage-wrap { max-width: 1100px; margin: 0 auto; padding: 40px 32px 20px; }
    .triage-title { font-family: 'DM Serif Display', serif; font-size: 3.5rem; font-weight: 400; color: white; letter-spacing: -1.5px; }
    .triage-badge { font-family: 'DM Sans', sans-serif; font-size: 0.7rem; font-weight: 600; letter-spacing: 3px;
        text-transform: uppercase; color: var(--teal-light); border: 1px solid var(--teal);
        border-radius: 99px; padding: 4px 12px; position: relative; top: -4px; margin-left: 14px; }
    .section-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 4px; text-transform: uppercase;
        color: var(--teal-light); margin-bottom: 14px; margin-top: 22px; display: block; }
    .glass-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px; padding: 24px 22px; margin-bottom: 18px; }
    .safety-box { background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.2);
        border-radius: 12px; padding: 18px 20px; margin-top: 20px; margin-bottom: 10px; }
    .demo-box { background: rgba(13,148,136,0.07); border: 1px solid rgba(13,148,136,0.25);
        border-radius: 12px; padding: 14px 18px; margin-bottom: 18px; display:flex; align-items:center; gap:12px; }
    </style>
    <div class="triage-wrap">
        <div style="display:flex; align-items:baseline; margin-bottom:6px;">
            <span class="triage-title">Expediente</span>
            <span class="triage-badge">CDSS v2.0</span>
        </div>
        <p style="color:var(--muted); letter-spacing:1px; margin-bottom:18px; font-size:0.9rem;">
            Identificación y registro de parámetros clínicos.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── MODO DEMO ──────────────────────────────────────────────
    st.markdown("""
    <div style="max-width:1100px; margin:0 auto; padding:0 32px 0;">
    <div style="background:rgba(13,148,136,0.07); border:1px solid rgba(13,148,136,0.25);
        border-radius:12px; padding:14px 18px; margin-bottom:18px; display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
      <span style="font-size:1rem;">⚡</span>
      <span style="font-size:0.72rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#14B8A6;">Modo Demo</span>
      <span style="font-size:0.82rem; color:rgba(240,253,250,0.5);">Carga un caso clínico real para demostración rápida</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    col_demo1, col_demo2, col_demo3 = st.columns([2, 1, 1])
    with col_demo1:
        caso_sel = st.selectbox(
            "Seleccionar caso demo",
            options=["— Ingresar manualmente —"] + list(CASOS_DEMO.keys()),
            label_visibility="collapsed"
        )
    with col_demo2:
        if st.button("Cargar Caso ➔", type="primary", use_container_width=True):
            if caso_sel != "— Ingresar manualmente —":
                st.session_state.demo_caso = caso_sel
                st.rerun()
    with col_demo3:
        if st.button("Limpiar Campos", type="primary", use_container_width=True):
            st.session_state.demo_caso = None
            st.rerun()

    st.markdown("<hr style='opacity:0.1; margin: 16px 0;'>", unsafe_allow_html=True)

    # ── Valores por defecto (demo o manual) ──
    d = CASOS_DEMO.get(demo, {}) if demo else {}

    # Nombre + Folio
    col_n1, col_n2 = st.columns([2, 1])
    with col_n1:
        nombre_paciente = st.text_input(
            "Nombre completo del Paciente",
            value=d.get("nombre", ""),
            placeholder="Ej. Juan Pérez López"
        )
    with col_n2:
        st.markdown("<p style='margin-bottom:8px; color:var(--muted); font-size:0.75rem; letter-spacing:2px;'>ID DE TRIAGE</p>", unsafe_allow_html=True)
        st.code(datetime.now().strftime("SITRE-%Y%m%d-%H%M"), language=None)

    st.markdown("<hr style='opacity:0.1; margin: 18px 0;'>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">01 · Datos Generales & Signos Vitales</span>', unsafe_allow_html=True)
        edad_input = st.number_input("Edad (años)", 1, 120, d.get("edad", 25))
        dias_input = st.number_input("Días de evolución", 1, 30, d.get("dias", 3))
        fr_input   = st.number_input("Frecuencia Respiratoria (rpm)", 10, 60, d.get("fr", 18))
        sat_input  = st.number_input("Saturación O₂ (%)", 50.0, 100.0, float(d.get("sat", 98.0)), step=0.5)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">02 · Comorbilidades</span>', unsafe_allow_html=True)
        neumopatia = st.toggle("Neumopatía crónica (Asma / EPOC / Fibrosis)", value=d.get("neumopatia", False))
        inmuno     = st.toggle("Inmunocompromiso (Diabetes, VIH, Esteroides)",  value=d.get("inmuno", False))
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">03 · Cuadro Clínico</span>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p style='color:var(--teal-light); font-size:0.8rem; font-weight:600; margin-bottom:8px;'>Criterios bacterianos</p>", unsafe_allow_html=True)
            fiebre     = st.toggle("Fiebre > 38°C",        value=d.get("fiebre", False))
            exudado    = st.toggle("Exudado amigdalino",    value=d.get("exudado", False))
            adenopatia = st.toggle("Adenopatía cervical",   value=d.get("adenopatia", False))
        with c2:
            st.markdown("<p style='color:var(--teal-light); font-size:0.8rem; font-weight:600; margin-bottom:8px;'>Signos virales</p>", unsafe_allow_html=True)
            tos      = st.toggle("Tos",      value=d.get("tos", False))
            rinorrea = st.toggle("Rinorrea", value=d.get("rinorrea", False))
            disfonia = st.toggle("Disfonía", value=d.get("disfonia", False))
        st.markdown("<br>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            conjuntivitis = st.toggle("Conjuntivitis",   value=d.get("conjuntivitis", False))
            mialgias      = st.toggle("Mialgias severas", value=d.get("mialgias", False))
        with c4:
            exantema = st.toggle("Exantema",         value=d.get("exantema", False))
            nauseas  = st.toggle("Náuseas / Vómito", value=d.get("nauseas", False))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="safety-box">', unsafe_allow_html=True)
    st.markdown("<p style='color:#EF4444; font-weight:700; font-size:0.75rem; letter-spacing:2px; margin-bottom:8px;'>⚠️ VALIDACIÓN DE SEGURIDAD</p>", unsafe_allow_html=True)
    safety_check = st.checkbox("Confirmo que el paciente NO presenta estridor, cianosis, tiraje intercostal ni alteración del estado de conciencia.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns([1, 1.5, 1])
    with col_b2:
        label_btn = "Procesar Diagnóstico ➔" if safety_check else "Complete la validación ⚠️"
        if st.button(label_btn, type="primary", use_container_width=True, disabled=not safety_check):
            if not nombre_paciente.strip():
                st.warning("Por favor ingresa el nombre del paciente.")
            else:
                paciente_actual = PacienteIRA(
                    edad=edad_input, dias_evolucion=dias_input,
                    frecuencia_respiratoria=fr_input, saturacion_oxigeno=sat_input,
                    fiebre_mayor_38=fiebre, exudado_amigdalino=exudado,
                    adenopatia_cervical_anterior=adenopatia, conjuntivitis=conjuntivitis,
                    mialgias_severas=mialgias, disfonia=disfonia, rinorrea=rinorrea,
                    tos=tos, exantema=exantema, nauseas_vomito=nauseas,
                    neumopatia_cronica=neumopatia, inmunocompromiso=inmuno
                )
                resultado = evaluar_paciente(paciente_actual)

                # ── Guardar en historial ──
                st.session_state.historial.append({
                    "hora":    datetime.now().strftime("%H:%M"),
                    "nombre":  nombre_paciente.strip(),
                    "edad":    edad_input,
                    "score":   paciente_actual.calcular_score_centor(),
                    "virales": paciente_actual.contar_signos_virales(),
                    "tipo":    resultado.get("tipo", "gris"),
                    "tag":     {"urgencia":"EMERGENCIA","viral":"VIRAL","bacteriana":"BACTERIANA","gris":"INDETERMINADO"}.get(resultado.get("tipo","gris"), "—"),
                })

                st.session_state.resultado_completo = resultado
                st.session_state.nombre_paciente    = nombre_paciente.strip()
                st.session_state.paciente_obj       = paciente_actual
                st.session_state.demo_caso          = None
                st.session_state.pantalla           = "resultados"
                st.rerun()

    # ── HISTORIAL + DASHBOARD (si hay pacientes) ──────────────
    if st.session_state.historial:
        h = st.session_state.historial
        total     = len(h)
        virales   = sum(1 for p in h if p["tipo"] == "viral")
        bacterias = sum(1 for p in h if p["tipo"] == "bacteriana")
        urgencias = sum(1 for p in h if p["tipo"] == "urgencia")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <hr style='opacity:0.08; margin-bottom:28px;'>
        <div style='max-width:1100px; margin:0 auto; padding:0 32px;'>
          <p style='font-size:0.65rem; font-weight:700; letter-spacing:4px; text-transform:uppercase;
              color:#14B8A6; margin-bottom:18px;'>Panel de Turno</p>
        </div>
        """, unsafe_allow_html=True)

        # Dashboard metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        for col, val, label, color in [
            (col_m1, total,     "Pacientes Evaluados", "#14B8A6"),
            (col_m2, virales,   "Casos Virales",        "#3B82F6"),
            (col_m3, bacterias, "Casos Bacterianos",    "#22C55E"),
            (col_m4, urgencias, "Urgencias",            "#EF4444"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
                    border-radius:14px; padding:18px 20px; text-align:center; margin-bottom:12px;
                    border-top: 2px solid {color};">
                  <div style="font-family:'DM Serif Display',serif; font-size:2.6rem; color:{color}; line-height:1;">{val}</div>
                  <div style="font-size:0.62rem; font-weight:600; letter-spacing:2px; text-transform:uppercase;
                      color:rgba(240,253,250,0.4); margin-top:6px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        # Historial table
        st.markdown("""
        <div style='max-width:1100px; margin:0 auto; padding:0 32px;'>
          <p style='font-size:0.65rem; font-weight:700; letter-spacing:4px; text-transform:uppercase;
              color:rgba(240,253,250,0.35); margin-bottom:12px;'>Registro de Triage del Turno</p>
        </div>
        """, unsafe_allow_html=True)

        # Header row
        TIPO_COLORS = {"urgencia":"#EF4444","viral":"#3B82F6","bacteriana":"#22C55E","gris":"#F59E0B"}

        table_rows = ""
        for i, p in enumerate(reversed(h)):
            color = TIPO_COLORS.get(p["tipo"], "#F59E0B")
            bg    = "rgba(255,255,255,0.02)" if i % 2 == 0 else "rgba(255,255,255,0.01)"
            table_rows += f"""
            <tr style="background:{bg};">
              <td style="padding:10px 14px; font-size:0.8rem; color:rgba(240,253,250,0.4);">{p['hora']}</td>
              <td style="padding:10px 14px; font-size:0.88rem; color:#F0FDFA; font-weight:500;">{p['nombre']}</td>
              <td style="padding:10px 14px; font-size:0.8rem; color:rgba(240,253,250,0.5); text-align:center;">{p['edad']} años</td>
              <td style="padding:10px 14px; text-align:center;">
                <span style="font-family:'DM Serif Display',serif; font-size:1.1rem; color:{color}; font-weight:700;">{p['score']}</span>
                <span style="font-size:0.7rem; color:rgba(240,253,250,0.3);">/5</span>
              </td>
              <td style="padding:10px 14px; text-align:center;">
                <span style="font-family:'DM Serif Display',serif; font-size:1.1rem; color:#3B82F6;">{p['virales']}</span>
                <span style="font-size:0.7rem; color:rgba(240,253,250,0.3);">/7</span>
              </td>
              <td style="padding:10px 14px; text-align:center;">
                <span style="display:inline-block; font-size:0.6rem; font-weight:700; letter-spacing:2px;
                    text-transform:uppercase; color:{color}; border:1px solid {color}55;
                    border-radius:99px; padding:3px 10px; background:{color}15;">
                  {p['tag']}
                </span>
              </td>
            </tr>
            """

        # Inyectamos la tabla con components.html para evitar que Streamlit sanitice el HTML complejo
        table_height = 60 + len(h) * 46
        components.html(f"""
        <style>
          body {{ margin:0; padding:0; background:transparent; font-family:'DM Sans',sans-serif; }}
          table {{ width:100%; border-collapse:collapse; }}
          thead tr {{ background:rgba(13,148,136,0.12); border-bottom:1px solid rgba(13,148,136,0.25); }}
          th {{ padding:10px 14px; font-size:0.6rem; font-weight:700; letter-spacing:3px;
               text-transform:uppercase; color:#14B8A6; }}
          th:first-child, td:first-child {{ text-align:left; }}
          th:not(:first-child):not(:nth-child(2)), td:not(:first-child):not(:nth-child(2)) {{ text-align:center; }}
          td {{ padding:10px 14px; }}
          .wrap {{ background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08);
                  border-radius:14px; overflow:hidden; }}
        </style>
        <div class="wrap">
          <table>
            <thead>
              <tr>
                <th>Hora</th>
                <th>Paciente</th>
                <th>Edad</th>
                <th>McIsaac</th>
                <th>Viral</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {table_rows}
            </tbody>
          </table>
        </div>
        """, height=table_height, scrolling=False)


# ══════════════════════════════════════════
# PANTALLA 3 — RESULTADOS
# ══════════════════════════════════════════
elif st.session_state.pantalla == "resultados":

    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
        PDF_DISPONIBLE = True
    except ImportError:
        PDF_DISPONIBLE = False

    resultado  = st.session_state.resultado_completo
    nombre_pac = st.session_state.get("nombre_paciente", "Paciente")
    paciente   = st.session_state.get("paciente_obj", None)
    tipo       = resultado.get("tipo", "gris")
    diagnostico = resultado["diagnostico"]
    tratamiento = resultado["tratamiento"]

    ahora     = datetime.now()
    fecha_str = ahora.strftime("%d %b %Y").upper()
    hora_str  = ahora.strftime("%H:%M")
    folio     = ahora.strftime("SITRE-%Y%m%d-%H%M")

    score_centor = paciente.calcular_score_centor() if paciente else 0
    signos_vir   = paciente.contar_signos_virales()  if paciente else 0
    score_pct    = min(max(score_centor / 5, 0), 1) * 100
    viral_pct    = min(max(signos_vir   / 7, 0), 1) * 100

    CONFIGS = {
        "urgencia":   {"accent":"#EF4444","glow":"rgba(239,68,68,0.3)", "bg":"rgba(239,68,68,0.07)", "tag":"EMERGENCIA",   "label":"Derivación Inmediata a Urgencias",       "emoji":"🚨","pcol":"#EF4444"},
        "viral":      {"accent":"#3B82F6","glow":"rgba(59,130,246,0.3)","bg":"rgba(59,130,246,0.07)","tag":"VIRAL",        "label":"Manejo Conservador · Sin Antibióticos",  "emoji":"🧊","pcol":"#3B82F6"},
        "bacteriana": {"accent":"#22C55E","glow":"rgba(34,197,94,0.3)", "bg":"rgba(34,197,94,0.07)", "tag":"BACTERIANA",   "label":"Indicación Antimicrobiana",              "emoji":"🦠","pcol":"#22C55E"},
        "gris":       {"accent":"#F59E0B","glow":"rgba(245,158,11,0.3)","bg":"rgba(245,158,11,0.07)","tag":"INDETERMINADO","label":"Valoración Clínica Presencial Requerida","emoji":"⚠️","pcol":"#F59E0B"},
    }
    c = CONFIGS.get(tipo, CONFIGS["gris"])

    FUNDAMENTOS = {
        "urgencia":   "Hipoxia (&lt;90%) o taquipnea severa (&gt;24 rpm) indica compromiso de vía aérea inferior o cuadro sistémico grave. El algoritmo detiene la evaluación estándar y exige soporte vital inmediato.",
        "viral":      "El cuadro carece de criterios fuertes para Estreptococo y presenta signos clásicos de etiología viral. Se omiten antimicrobianos para preservar el stewardship antibiótico y reducir resistencias.",
        "bacteriana": "El Score de Centor modificado por McIsaac otorga un VPP alto para <em>Streptococcus pyogenes</em>. La combinación de criterios clínicos justifica el tratamiento antibiótico dirigido.",
        "gris":       "El paciente presenta comorbilidades o zona gris sintomática que invalidan las reglas de predicción estándar. Se requiere juicio clínico presencial y seguimiento estrecho.",
    }

    if score_centor >= 4:   gauge_color = "#22C55E"
    elif score_centor >= 2: gauge_color = "#F59E0B"
    else:                   gauge_color = "#3B82F6"

    diag_html = diagnostico.replace("\n", "<br>")
    trat_html = tratamiento.replace("\n", "<br>")
    fund_html = FUNDAMENTOS.get(tipo, "")
    pcol      = c["pcol"]

    st.markdown(f"""
<style>
.res-page {{ max-width: 980px; margin: 0 auto; padding: 44px 28px 40px; }}
.res-meta-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; animation: fade-up 0.5s 0.1s both; }}
.meta-folio {{ font-size: 0.6rem; font-weight: 700; letter-spacing: 3px; color: var(--teal-light); text-transform: uppercase; }}
.meta-datetime {{ font-family: 'DM Serif Display', serif; font-size: 1.5rem; font-weight: 300; color: var(--text); letter-spacing: -0.5px; margin-top: 2px; }}
.meta-right {{ text-align: right; font-size: 0.75rem; color: var(--muted); line-height: 1.7; }}
.patient-bar {{ display: flex; align-items: center; justify-content: space-between;
    background: rgba(13,148,136,0.08); border: 1px solid rgba(13,148,136,0.2);
    border-radius: 14px; padding: 16px 24px; margin-bottom: 22px; animation: fade-up 0.5s 0.15s both; }}
.patient-label {{ font-size: 0.6rem; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: var(--teal-light); margin-bottom: 4px; }}
.patient-name {{ font-family: 'DM Serif Display', serif; font-size: 1.7rem; color: var(--text); line-height: 1; }}
.patient-folio {{ font-size: 0.72rem; color: var(--muted); letter-spacing: 1px; text-align: right; line-height: 1.6; }}
.res-hero {{ position: relative; border: 1px solid {c["accent"]}44; border-radius: 28px;
    overflow: hidden; margin-bottom: 24px; box-shadow: 0 0 80px {c["glow"]};
    animation: card-in 0.7s cubic-bezier(0.23,1,0.32,1) both; }}
.res-hero-bg {{ position: absolute; inset: 0; z-index: 0;
    background: radial-gradient(ellipse at 20% 50%, {c["accent"]}18 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, {c["accent"]}0c 0%, transparent 60%);
    animation: bg-shift 5s ease-in-out infinite alternate; }}
@keyframes bg-shift {{ from {{ opacity:0.5; }} to {{ opacity:1.0; }} }}
.res-hero-inner {{ position: relative; z-index: 1; display: flex; align-items: center; gap: 32px; padding: 36px 40px; }}
.hero-icon {{ font-size: 5rem; line-height: 1; flex-shrink: 0;
    animation: icon-pop 0.6s 0.4s cubic-bezier(0.34,1.56,0.64,1) both;
    filter: drop-shadow(0 0 16px {c["accent"]}); }}
@keyframes icon-pop {{ from {{ opacity:0; transform: scale(0.2) rotate(-20deg); }} to {{ opacity:1; transform: scale(1) rotate(0deg); }} }}
.hero-tag {{ display: inline-block; font-size: 0.6rem; font-weight: 700; letter-spacing: 4px; text-transform: uppercase;
    color: {c["accent"]}; border: 1px solid {c["accent"]}55; border-radius: 99px; padding: 4px 14px; margin-bottom: 12px; background: {c["bg"]}; }}
.hero-label {{ font-family: 'DM Serif Display', serif; font-size: clamp(1.5rem, 3vw, 2.2rem);
    color: var(--text); font-weight: 400; letter-spacing: -0.5px; line-height: 1.2; margin-bottom: 10px; }}
.hero-diag {{ font-size: 0.92rem; color: var(--muted); line-height: 1.65; }}
.cards-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 22px; animation: fade-up 0.5s 0.3s both; }}
.info-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 24px; }}
.info-card-label {{ font-size: 0.6rem; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }}
.gauge-number {{ font-family: 'DM Serif Display', serif; font-size: 3.2rem; line-height: 1; margin-bottom: 4px; }}
.gauge-sub {{ font-size: 0.72rem; color: var(--muted); margin-bottom: 16px; }}
.gauge-bar-bg {{ width: 100%; height: 8px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; margin-bottom: 8px; }}
.gauge-bar-fill {{ height: 100%; border-radius: 99px;
    background: linear-gradient(to right, {gauge_color}88, {gauge_color});
    animation: fill-bar 1.2s 0.6s cubic-bezier(0.23,1,0.32,1) both; }}
@keyframes fill-bar {{ from {{ width: 0%; }} to {{ width: {score_pct}%; }} }}
.viral-bar-fill {{ height: 100%; border-radius: 99px;
    background: linear-gradient(to right, #3B82F688, #3B82F6);
    animation: fill-viral 1.2s 0.8s cubic-bezier(0.23,1,0.32,1) both; }}
@keyframes fill-viral {{ from {{ width: 0%; }} to {{ width: {viral_pct}%; }} }}
.gauge-ticks {{ display: flex; justify-content: space-between; font-size: 0.58rem; color: var(--muted); margin-top: 4px; }}
.tx-card {{ background: {c["bg"]}; border: 1px solid {c["accent"]}33; border-radius: 18px;
    padding: 26px; margin-bottom: 22px; animation: fade-up 0.5s 0.35s both; }}
.tx-label {{ font-size: 0.6rem; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: {c["accent"]}; margin-bottom: 14px; }}
.tx-body {{ font-size: 0.95rem; color: var(--text); line-height: 1.8; }}
.fund-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 18px;
    padding: 22px 24px; margin-bottom: 22px; animation: fade-up 0.5s 0.4s both; }}
.fund-label {{ font-size: 0.6rem; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }}
.fund-body {{ font-size: 0.88rem; color: var(--muted); line-height: 1.7; }}
#particles-canvas {{ position: fixed; inset: 0; pointer-events: none; z-index: 999; }}
@keyframes card-in {{ from {{ opacity:0; transform: translateY(32px) scale(0.98); }} to {{ opacity:1; transform: translateY(0) scale(1); }} }}
@keyframes fade-up {{ from {{ opacity:0; transform: translateY(20px); }} to {{ opacity:1; transform: translateY(0); }} }}
</style>

<canvas id="particles-canvas"></canvas>
<script>
(function() {{
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth; canvas.height = window.innerHeight;
    const particles = []; const color = '{pcol}';
    function spawn() {{ particles.push({{ x:Math.random()*canvas.width, y:canvas.height+10,
        vx:(Math.random()-0.5)*1.2, vy:-(Math.random()*2.2+0.8),
        r:Math.random()*5+2, life:Math.random()*100+80, age:0 }}); }}
    function draw() {{
        ctx.clearRect(0,0,canvas.width,canvas.height);
        for(let i=particles.length-1;i>=0;i--){{
            const p=particles[i]; p.x+=p.vx; p.y+=p.vy; p.age++;
            if(p.age>=p.life){{particles.splice(i,1);continue;}}
            ctx.save(); ctx.globalAlpha=(1-p.age/p.life)*0.65;
            ctx.fillStyle=color; ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill(); ctx.restore();
        }}
        requestAnimationFrame(draw);
    }}
    setTimeout(()=>{{for(let i=0;i<20;i++)spawn();}},300);
    setInterval(()=>{{if(particles.length<35)spawn();}},350);
    draw();
    window.addEventListener('resize',()=>{{canvas.width=window.innerWidth;canvas.height=window.innerHeight;}});
}})();
</script>

<div class="res-page">
  <div class="res-meta-bar">
    <div>
      <div class="meta-folio">Reporte Clínico · SITRE CDSS v2.0</div>
      <div class="meta-datetime">📅 {fecha_str} &nbsp;·&nbsp; 🕒 {hora_str} hrs</div>
    </div>
    <div class="meta-right">
      <b style="color:var(--teal-light);">{folio}</b><br>
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
      Folio: {folio}
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
  <div class="cards-row">
    <div class="info-card">
      <div class="info-card-label">Score McIsaac · Riesgo Bacteriano</div>
      <div class="gauge-number" style="color:{gauge_color};">{score_centor}<span style="font-size:1.2rem;color:var(--muted);">/5</span></div>
      <div class="gauge-sub">{"Alto riesgo estreptocócico" if score_centor>=4 else "Riesgo moderado" if score_centor>=2 else "Riesgo bajo"}</div>
      <div class="gauge-bar-bg"><div class="gauge-bar-fill"></div></div>
      <div class="gauge-ticks"><span>0</span><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span></div>
    </div>
    <div class="info-card">
      <div class="info-card-label">Carga de Signos Virales</div>
      <div class="gauge-number" style="color:#3B82F6;">{signos_vir}<span style="font-size:1.2rem;color:var(--muted);">/7</span></div>
      <div class="gauge-sub">{"Cuadro fuertemente viral" if signos_vir>=4 else "Signos virales presentes" if signos_vir>=2 else "Pocos signos virales"}</div>
      <div class="gauge-bar-bg"><div class="viral-bar-fill"></div></div>
      <div class="gauge-ticks"><span>0</span><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>7</span></div>
    </div>
  </div>
  <div class="tx-card">
    <div class="tx-label">💊 Guía Terapéutica Sugerida</div>
    <div class="tx-body">{trat_html}</div>
  </div>
  <div class="fund-card">
    <div class="fund-label">📝 Fundamento Clínico</div>
    <div class="fund-body">{fund_html}</div>
  </div>
</div>
""", unsafe_allow_html=True)

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

    # Botones
    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        if PDF_DISPONIBLE:
            def limpiar(t):
                for bad in ["🚨","⚠️","🦠","🧫","🧊","镜","•","💊"]:
                    t = t.replace(bad, "")
                return t.encode("latin-1", "ignore").decode("latin-1").strip()

            def generar_pdf():
                from fpdf import FPDF
                from fpdf.enums import XPos, YPos
                pdf = FPDF(); pdf.add_page()
                pdf.set_font("Helvetica","B",20); pdf.set_text_color(13,148,136)
                pdf.cell(0,15,"SITRE - REPORTE DE TRIAGE",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
                pdf.set_font("Helvetica","",9); pdf.set_text_color(120,120,120)
                pdf.cell(0,8,f"Folio: {folio}  |  {fecha_str}  {hora_str}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
                pdf.ln(6); pdf.set_fill_color(240,253,250)
                pdf.set_font("Helvetica","B",12); pdf.set_text_color(0,0,0)
                pdf.cell(0,10,f" PACIENTE: {limpiar(nombre_pac.upper())}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,fill=True)
                pdf.ln(4); pdf.set_font("Helvetica","B",11)
                pdf.cell(0,10,f"RESULTADO: {c['tag']}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","",10); pdf.multi_cell(0,7,limpiar(diagnostico))
                pdf.ln(4); pdf.set_font("Helvetica","B",11)
                pdf.cell(0,10,f"Score McIsaac: {score_centor}/5  |  Signos virales: {signos_vir}/7",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.ln(4); pdf.set_font("Helvetica","B",11)
                pdf.cell(0,10,"GUIA TERAPEUTICA:",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                pdf.set_font("Helvetica","",10); pdf.multi_cell(0,7,limpiar(tratamiento))
                pdf.ln(14); pdf.set_font("Helvetica","I",8); pdf.set_text_color(130,130,130)
                pdf.multi_cell(0,5,"Nota: Este documento es una sugerencia basada en algoritmos clinicos validados. La decision final recae en el medico tratante.")
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
            st.session_state.pantalla = "triage"
            st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("← Volver al Inicio", type="primary", use_container_width=True):
            st.session_state.pantalla = "bienvenida"
            st.rerun()