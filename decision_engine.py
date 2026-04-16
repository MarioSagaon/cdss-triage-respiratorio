from clinical_models import PacienteIRA, PacienteNeumoniaCAP, PacienteOMA, PacienteSinusitis

# ══════════════════════════════════════════════════════════
# GUÍAS TERAPÉUTICAS POR PATOLOGÍA
# Basadas en: IDSA, BTS, SEIP, SSA México, MSF Guidelines
# ══════════════════════════════════════════════════════════

GUIAS_FARINGITIS = {
    "urgencia":   "• Oxigenoterapia (Meta SatO₂ >92%).\n• Posición semifowler.\n• Traslado inmediato a urgencias para manejo de vía aérea.",
    "viral":      "• Paracetamol 500mg c/8h (fiebre/dolor).\n• Hidratación abundante y reposo.\n• Lavados nasales con solución salina.\n• NO usar antibióticos ni esteroides.",
    "bacteriana": "• Amoxicilina 500mg c/8h por 10 días (primera línea).\n• Alternativa: Penicilina V o Cefalosporinas 1ª gen.\n• Paracetamol para control térmico.",
    "prolongada": "• Considerar Amoxicilina/Ácido Clavulánico por riesgo de sobreinfección.\n• Reevaluar foco pulmonar (radiografía de tórax).",
    "gris":       "• Manejo sintomático inicial.\n• Realizar RADT (prueba rápida) o cultivo faríngeo.\n• Vigilancia estrecha de datos de alarma.",
}

GUIAS_NEUMONIA = {
    "urgencia":   "• Traslado INMEDIATO a urgencias / UCI.\n• Oxigenoterapia para mantener SatO₂ >94%.\n• Hemocultivos antes de iniciar antibiótico.\n• Considerar Ventilación Mecánica No Invasiva.",
    "grave":      "• Hospitalización urgente (Score CURB-65 ≥3).\n• Amoxicilina/Ácido Clavulánico IV + Macrólido.\n• Alternativa: Levofloxacino 750mg c/24h IV.\n• Hemocultivos, Ag urinarios (Legionella/Neumococo).\n• Rx tórax o TAC de confirmación.",
    "moderada":   "• Considerar hospitalización para observación (CURB-65 = 2).\n• Amoxicilina 1g c/8h VO o Amoxicilina/Clavulánico.\n• Macrólido si sospecha de bacteria atípica.\n• Control en 48-72h. Criterios de ingreso si no mejora.",
    "leve":       "• Manejo ambulatorio (CURB-65 0-1).\n• Amoxicilina 1g c/8h VO por 5-7 días.\n• Alternativa: Azitromicina 500mg c/24h x 3 días.\n• Control en 48h. Radiografía de control en 4-6 semanas.\n• Reposo, hidratación, antitérmicos según necesidad.",
    "riesgo":     "• Manejo ambulatorio con vigilancia estrecha.\n• Amoxicilina/Ácido Clavulánico por comorbilidad.\n• Control en 24-48h. Umbral bajo para hospitalización.",
}

GUIAS_OMA = {
    "urgencia":   "• Derivación a urgencias si signos de mastoiditis o meningitis.\n• Evaluación por ORL de urgencia.",
    "confirmada_grave": "• Antibiótico INMEDIATO (no diferir).\n• Amoxicilina 80-90mg/kg/día c/8h por 10 días.\n• Si <6 meses o falla terapéutica: Amoxicilina/Clavulánico.\n• Analgesia: Paracetamol o Ibuprofeno.",
    "confirmada": "• Amoxicilina 80mg/kg/día c/8h por 7-10 días (primera línea).\n• En niños >2 años sin riesgo: considerar observación 48-72h.\n• Analgesia adecuada: Ibuprofeno (preferido) o Paracetamol.\n• Control en 48-72h. Si no mejora: iniciar/cambiar antibiótico.",
    "probable":   "• Observación activa 48-72h con analgesia.\n• Prescripción diferida de Amoxicilina (usar si no mejora).\n• Paracetamol o Ibuprofeno para dolor y fiebre.\n• Control en 48h con otoscopia de confirmación.",
    "no_cumple":  "• No cumple criterios de OMA. Probable origen viral.\n• Manejo sintomático: analgesia, descongestionantes.\n• NO iniciar antibiótico.\n• Revaloración en 48-72h si no mejora.",
}

GUIAS_SINUSITIS = {
    "urgencia":   "• Derivación URGENTE a urgencias.\n• Sospecha de complicación orbitaria o intracraneal.\n• Antibiótico IV + TAC de senos paranasales urgente.",
    "bacteriana_grave": "• Antibiótico INMEDIATO.\n• Amoxicilina/Ácido Clavulánico 875/125mg c/12h por 10 días.\n• Lavados nasales con suero salino (irrigación nasal).\n• Corticoide intranasal como coadyuvante.\n• Control en 72h. Derivar a ORL si no responde.",
    "bacteriana": "• Amoxicilina 1g c/8h VO por 7-10 días (IDSA primera línea).\n• Irrigación nasal con suero salino.\n• Corticoide intranasal (Budesonida o Mometasona).\n• Evitar descongestionantes >3 días.\n• Control en 5-7 días.",
    "viral":      "• NO usar antibióticos (curación espontánea >80% en 7-15 días).\n• Irrigación nasal con suero salino (alta evidencia).\n• Corticoide intranasal para alivio sintomático.\n• Paracetamol o Ibuprofeno para dolor y fiebre.\n• Reevaluar en 7-10 días. Si empeora → reconsiderar.",
}


# ══════════════════════════════════════════════════════════
# MOTOR 1 — FARINGITIS (McIsaac)
# ══════════════════════════════════════════════════════════
def evaluar_paciente(paciente: PacienteIRA) -> dict:
    """Motor de inferencia clínica para Faringitis/IRA Alta."""

    if paciente.tiene_banderas_rojas():
        return {"tipo":"urgencia", "diagnostico":"🚨 ALERTA: Criterios de urgencia (Hipoxia o Taquipnea).", "tratamiento":GUIAS_FARINGITIS["urgencia"]}

    if paciente.tiene_riesgo_elevado():
        return {"tipo":"gris", "diagnostico":"⚠️ PRECAUCIÓN: Paciente con comorbilidad de alto riesgo.", "tratamiento":GUIAS_FARINGITIS["gris"]}

    score = paciente.calcular_score_centor()
    virales = paciente.contar_signos_virales()

    if paciente.dias_evolucion > 10:
        return {"tipo":"bacteriana", "diagnostico":"⚠️ ALERTA: Evolución prolongada (>10 días). Riesgo de sobreinfección.", "tratamiento":GUIAS_FARINGITIS["prolongada"]}
    elif virales >= 2 and score <= 2:
        return {"tipo":"viral", "diagnostico":"🦠 DIAGNÓSTICO: Probabilidad VIRAL alta.", "tratamiento":GUIAS_FARINGITIS["viral"]}
    elif score >= 4:
        return {"tipo":"bacteriana", "diagnostico":"🧫 DIAGNÓSTICO: Probabilidad BACTERIANA alta (McIsaac ≥4).", "tratamiento":GUIAS_FARINGITIS["bacteriana"]}
    else:
        return {"tipo":"gris", "diagnostico":"⚠️ DIAGNÓSTICO: Zona gris — indeterminado.", "tratamiento":GUIAS_FARINGITIS["gris"]}


# ══════════════════════════════════════════════════════════
# MOTOR 2 — NEUMONÍA (CURB-65)
# ══════════════════════════════════════════════════════════
def evaluar_neumonia(paciente: PacienteNeumoniaCAP) -> dict:
    """Motor de inferencia clínica para Neumonía por CURB-65."""

    if paciente.tiene_banderas_rojas():
        return {"tipo":"urgencia", "diagnostico":"🚨 URGENCIA: Hipoxia crítica o taquipnea severa. Riesgo de insuficiencia respiratoria.", "tratamiento":GUIAS_NEUMONIA["urgencia"]}

    score = paciente.calcular_curb65()
    severidad = paciente.nivel_severidad()

    if score >= 3:
        return {
            "tipo":"urgencia",
            "diagnostico":f"🚨 NEUMONÍA GRAVE (CURB-65: {score}/5). Mortalidad estimada >15%. Hospitalización urgente requerida.",
            "tratamiento":GUIAS_NEUMONIA["grave"]
        }
    elif score == 2:
        if paciente.tiene_riesgo_elevado():
            return {"tipo":"urgencia", "diagnostico":f"⚠️ NEUMONÍA MODERADA + COMORBILIDAD (CURB-65: {score}/5). Hospitalización recomendada.", "tratamiento":GUIAS_NEUMONIA["riesgo"]}
        return {
            "tipo":"gris",
            "diagnostico":f"⚠️ NEUMONÍA MODERADA (CURB-65: {score}/5). Mortalidad estimada ~9%. Evaluar hospitalización.",
            "tratamiento":GUIAS_NEUMONIA["moderada"]
        }
    else:
        if paciente.tiene_riesgo_elevado():
            return {"tipo":"gris", "diagnostico":f"⚠️ NEUMONÍA LEVE + COMORBILIDAD (CURB-65: {score}/5). Vigilancia estrecha ambulatoria.", "tratamiento":GUIAS_NEUMONIA["riesgo"]}
        return {
            "tipo":"viral",
            "diagnostico":f"✅ NEUMONÍA LEVE (CURB-65: {score}/5). Mortalidad estimada <3%. Manejo ambulatorio.",
            "tratamiento":GUIAS_NEUMONIA["leve"]
        }


# ══════════════════════════════════════════════════════════
# MOTOR 3 — OTITIS MEDIA AGUDA
# ══════════════════════════════════════════════════════════
def evaluar_oma(paciente: PacienteOMA) -> dict:
    """Motor de inferencia clínica para OMA por criterios AAP/SEIP."""

    nivel = paciente.nivel_diagnostico()
    es_grave = paciente.es_grave()
    alto_riesgo = paciente.tiene_riesgo_elevado()

    if nivel == "NO_CUMPLE":
        return {
            "tipo":"viral",
            "diagnostico":"🔵 NO CUMPLE CRITERIOS DE OMA. Probable infección viral de vías altas.",
            "tratamiento":GUIAS_OMA["no_cumple"]
        }

    if nivel == "CONFIRMADA":
        if es_grave or alto_riesgo:
            return {
                "tipo":"bacteriana",
                "diagnostico":f"🦠 OMA CONFIRMADA GRAVE. {'Fiebre >39°C / otalgia intensa / bilateral.' if es_grave else 'Paciente de alto riesgo.'} Antibiótico inmediato.",
                "tratamiento":GUIAS_OMA["confirmada_grave"]
            }
        return {
            "tipo":"bacteriana",
            "diagnostico":"🦠 OMA CONFIRMADA (3/3 criterios). Probable etiología bacteriana. Ver guía terapéutica.",
            "tratamiento":GUIAS_OMA["confirmada"]
        }

    # PROBABLE (2 criterios)
    return {
        "tipo":"gris",
        "diagnostico":"⚠️ OMA PROBABLE (2/3 criterios). Diagnóstico no confirmado. Observación activa recomendada.",
        "tratamiento":GUIAS_OMA["probable"]
    }


# ══════════════════════════════════════════════════════════
# MOTOR 4 — SINUSITIS
# ══════════════════════════════════════════════════════════
def evaluar_sinusitis(paciente: PacienteSinusitis) -> dict:
    """Motor de inferencia clínica para Sinusitis por criterios IDSA/NICE."""

    if paciente.tiene_banderas_rojas():
        return {
            "tipo":"urgencia",
            "diagnostico":"🚨 URGENCIA: Signos de complicación (edema periorbitario o rigidez nucal). Posible extensión orbitaria/intracraneal.",
            "tratamiento":GUIAS_SINUSITIS["urgencia"]
        }

    severidad = paciente.severidad()

    if severidad == "GRAVE":
        return {
            "tipo":"bacteriana",
            "diagnostico":"🦠 SINUSITIS BACTERIANA GRAVE (fiebre ≥39°C + dolor facial unilateral). Antibiótico de amplio espectro requerido.",
            "tratamiento":GUIAS_SINUSITIS["bacteriana_grave"]
        }
    elif severidad == "BACTERIANA":
        motivo = ""
        if paciente.dias_evolucion >= 10:
            motivo = f"síntomas ≥10 días sin mejoría"
        elif paciente.empeoramiento_tras_mejoria:
            motivo = "empeoramiento tras mejoría inicial (double sickening)"
        return {
            "tipo":"bacteriana",
            "diagnostico":f"🦠 SINUSITIS BACTERIANA (criterio IDSA: {motivo}). Antibiótico indicado.",
            "tratamiento":GUIAS_SINUSITIS["bacteriana"]
        }
    else:
        return {
            "tipo":"viral",
            "diagnostico":f"🔵 RINOSINUSITIS VIRAL ({paciente.dias_evolucion} días de evolución). Alta probabilidad de resolución espontánea.",
            "tratamiento":GUIAS_SINUSITIS["viral"]
        }