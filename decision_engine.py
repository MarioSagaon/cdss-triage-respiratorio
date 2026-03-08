# Importamos la clase que creamos en el otro archivo
from clinical_models import PacienteIRA

def evaluar_paciente(paciente: PacienteIRA) -> str:
    """
    Motor de inferencia clínica. Evalúa los datos del paciente 
    y retorna una recomendación de tratamiento.
    """
    # 1. Triage: Descartar Urgencias Médicas (Banderas Rojas)
    if paciente.tiene_banderas_rojas():
        return "🚨 ALERTA: Criterios de urgencia detectados (Hipoxia o Taquipnea). Derivar a segundo nivel. No manejar en consultorio."

    # 2. Pacientes de Alto Riesgo (Comorbilidades)
    if paciente.tiene_riesgo_elevado():
        return "⚠️ PRECAUCIÓN: Paciente con comorbilidad de alto riesgo.\n▶ Alto riesgo de exacerbación. Considerar derivación o antibiótico temprano."
    # Si no hay banderas rojas, calculamos los scores
    score_bacteriano = paciente.calcular_score_centor()
    signos_virales = paciente.contar_signos_virales()

    # 2. Árbol de Decisiones Clínicas
    # Regla A: Temporalidad
    if paciente.dias_evolucion > 10:
        return "⚠️ ALERTA: Evolución prolongada (>10 días). Alto riesgo de sobreinfección bacteriana. Considerar antibiótico."

    # Regla B: Alta probabilidad Viral
    elif signos_virales >= 2 and score_bacteriano <= 2:
        return "🦠 DIAGNÓSTICO: Probabilidad VIRAL alta. \n▶ Manejo sintomático (Paracetamol/Ibuprofeno). \n▶ PROHIBIDO prescribir antibióticos o dexametasona."

    # Regla C: Alta probabilidad Bacteriana (Criterios de McIsaac)
    elif score_bacteriano >= 4:
        return "🧫 DIAGNÓSTICO: Probabilidad BACTERIANA alta (Sospecha Estreptocócica). \n▶ Iniciar esquema antibiótico empírico de primera línea."

    # Regla D: Zona Gris (El paciente no cumple criterios fuertes para ninguno)
    else:
        return "🩺 DIAGNÓSTICO: Zona gris (Indeterminado). \n▶ Manejo sintomático inicial. \n▶ Educar sobre datos de alarma y revaluar en 48-72 horas. No dar antibiótico de inicio."