import streamlit as st
from clinical_models import PacienteIRA
from decision_engine import evaluar_paciente

# 1. Configuración de la página
st.set_page_config(page_title="CDSS Triage Respiratorio", page_icon="🏥", layout="wide")

st.title("🏥 Sistema Inteligente de Triage Respiratorio")
st.markdown("---")

# 2. Panel Lateral
st.sidebar.header("📋 Ingreso de Datos Clínicos")

st.sidebar.subheader("1. Demográficos y Signos Vitales")
edad_input = st.sidebar.number_input("Edad", min_value=1, max_value=120, value=25)
dias_input = st.sidebar.number_input("Días de evolución", min_value=1, max_value=30, value=3)
fr_input = st.sidebar.number_input("Frecuencia Respiratoria (rpm)", min_value=10, max_value=60, value=18)
sat_input = st.sidebar.number_input("Saturación de Oxígeno (%)", min_value=50.0, max_value=100.0, value=98.0, step=0.1)

# CAMBIO 1: Simplificamos el título a "Síntomas" (Tu idea de UX)
st.sidebar.subheader("2. Síntomas")
col1, col2 = st.sidebar.columns(2)

# Repartimos todos los síntomas en dos columnas solo para que se vea ordenado
with col1:
    fiebre = st.checkbox("Fiebre > 38°C")
    exudado = st.checkbox("Exudado Amigdalino")
    adenopatia = st.checkbox("Adenopatía Cervical")
    tos = st.checkbox("Tos")
    rinorrea = st.checkbox("Rinorrea")

with col2:
    disfonia = st.checkbox("Disfonía")
    conjuntivitis = st.checkbox("Conjuntivitis")
    mialgias = st.checkbox("Mialgias Severas")
    exantema = st.checkbox("Exantema")
    nauseas = st.checkbox("Náuseas/Vómito")

st.sidebar.subheader("3. Comorbilidades")
neumopatia = st.sidebar.checkbox("Neumopatía Crónica (Asma/EPOC)")
inmuno = st.sidebar.checkbox("Inmunocompromiso")

# 3. Botón de Acción y Lógica de Colores/Textos
st.markdown("### 🤖 Análisis Clínico")

if st.button("Evaluar Paciente", type="primary"):
    # Creamos el paciente
    paciente_actual = PacienteIRA(
        edad=edad_input, dias_evolucion=dias_input, frecuencia_respiratoria=fr_input,
        saturacion_oxigeno=sat_input, fiebre_mayor_38=fiebre, exudado_amigdalino=exudado,
        adenopatia_cervical_anterior=adenopatia, conjuntivitis=conjuntivitis,
        mialgias_severas=mialgias, disfonia=disfonia, rinorrea=rinorrea, tos=tos,
        exantema=exantema, nauseas_vomito=nauseas, neumopatia_cronica=neumopatia,
        inmunocompromiso=inmuno
    )
    
    # Obtenemos el resultado de tu "cerebro"
    diagnostico = evaluar_paciente(paciente_actual)
    
    # CAMBIO 2 y 3: Colores (Rojo, Verde, Azul) y Justificaciones Médicas
    # Evaluamos las condiciones sin explicar los colores
    if "DERIVACIÓN" in diagnostico or "ALERTA" in diagnostico and "Evolución" not in diagnostico:
        st.error("🚨 **ALERTA DE EMERGENCIA**\n\n" + diagnostico)
        st.error("**📝 Justificación Clínica:** La presencia de hipoxia (<90%) o taquipnea sugiere un compromiso severo de la vía aérea inferior (como neumonía) o un cuadro sistémico grave. El algoritmo detiene la evaluación de faringitis y exige atención de urgencia inmediata.")
        
    elif "VIRAL" in diagnostico:
        st.info("🧊 **PROBABILIDAD VIRAL ALTA**\n\n" + diagnostico)
        st.info("**📝 Justificación Clínica:** El cuadro carece de criterios fuertes para Estreptococo y presenta signos clásicos de infección viral (ej. tos, disfonía, rinorrea, mialgias). Estas infecciones (rinovirus, adenovirus, etc.) son autolimitadas. Los antibióticos no modificarán el curso clínico y solo contribuyen a la resistencia antimicrobiana mundial.")
        
    elif "BACTERIANA" in diagnostico or "Evolución prolongada" in diagnostico:
        st.success("🦠 **SOSPECHA BACTERIANA ALTA**\n\n" + diagnostico)
        if "Evolución" in diagnostico:
            st.success("**📝 Justificación Clínica:** La duración prolongada de los síntomas (>10 días) sugiere que el epitelio respiratorio ha sido dañado por un virus inicial, permitiendo la colonización oportunista de bacterias (ej. *S. pneumoniae*, *H. influenzae*). Se justifica el esquema antibiótico empírico por sospecha de sobreinfección.")
        else:
            st.success("**📝 Justificación Clínica:** El diagnóstico se basa en el **Score de Centor modificado por McIsaac**. La suma de síntomas como exudado, fiebre, adenopatía, ausencia de tos y la edad del paciente, otorgan un Valor Predictivo Positivo alto para *Streptococcus pyogenes* (EBHGA), justificando el antibiótico para prevenir secuelas como la fiebre reumática.")
            
    else:
        st.warning("⚠️ **ATENCIÓN ESPECIAL REQUERIDA**\n\n" + diagnostico)
        st.warning("**📝 Justificación Clínica:** El paciente tiene factores de riesgo de base (neumopatía o inmunocompromiso) que invalidan las reglas de predicción clínica estándar. Requiere valoración individualizada.")