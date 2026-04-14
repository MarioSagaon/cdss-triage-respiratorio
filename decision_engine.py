# Importamos la clase que creamos en el otro archivo
from clinical_models import PacienteIRA

def evaluar_paciente(paciente: PacienteIRA) -> dict:
    """
    Motor de inferencia clínica. 
    Retorna un diccionario con el 'diagnostico' y el 'tratamiento'.
    """
    
    # --- BASE DE DATOS DE TRATAMIENTOS SUGERIDOS ---
    guias = {
        "urgencia": "• Oxigenoterapia suplementaria (Meta >92%).\n• Posición semifowler.\n• Traslado inmediato a segundo nivel para manejo de vía aérea.",
        "viral": "• Paracetamol: 500mg c/8h (Fiebre/Dolor).\n• Hidratación abundante y reposo.\n• Lavados nasales con solución salina.\n• NO usar antibióticos ni esteroides.",
        "bacteriana": "• Amoxicilina: 500mg c/8h por 10 días (Primera línea).\n• Alternativa: Penicilina V o Cefalosporinas de 1ª gen.\n• Paracetamol para control térmico.",
        "prolongada": "• Considerar Amoxicilina/Ácido Clavulánico por riesgo de sobreinfección.\n• Reevaluar foco pulmonar (Radiografía de tórax).",
        "gris": "• Manejo sintomático inicial.\n• Realizar RADT (Prueba rápida) o Cultivo faríngeo.\n• Vigilancia estrecha de datos de alarma."
    }

    # 1. Triage: Banderas Rojas
    if paciente.tiene_banderas_rojas():
        return {
            "tipo": "urgencia",
            "diagnostico": "🚨 ALERTA: Criterios de urgencia detectados (Hipoxia o Taquipnea).",
            "tratamiento": guias["urgencia"]
        }

    # 2. Pacientes de Alto Riesgo
    if paciente.tiene_riesgo_elevado():
        return {
            "tipo": "gris",
            "diagnostico": "⚠️ PRECAUCIÓN: Paciente con comorbilidad de alto riesgo.",
            "tratamiento": guias["gris"]
        }

    score_bacteriano = paciente.calcular_score_centor()
    signos_virales = paciente.contar_signos_virales()

    # 3. Árbol de Decisiones
    if paciente.dias_evolucion > 10:
        return {
            "tipo": "bacteriana",
            "diagnostico": "⚠️ ALERTA: Evolución prolongada (>10 días). Riesgo de sobreinfección.",
            "tratamiento": guias["prolongada"]
        }

    elif signos_virales >= 2 and score_bacteriano <= 2:
        return {
            "tipo": "viral",
            "diagnostico": "🦠 DIAGNÓSTICO: Probabilidad VIRAL alta.",
            "tratamiento": guias["viral"]
        }

    elif score_bacteriano >= 4:
        return {
            "tipo": "bacteriana",
            "diagnostico": "🧫 DIAGNÓSTICO: Probabilidad BACTERIANA alta (Criterios McIsaac).",
            "tratamiento": guias["bacteriana"]
        }

    else:
        return {
            "tipo": "gris",
            "diagnostico": "镜 DIAGNÓSTICO: Zona gris (Indeterminado).",
            "tratamiento": guias["gris"]
        }