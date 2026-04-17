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
    import time
    t0 = time.time()

    # ── Calcular valores ──
    score = paciente.calcular_score_centor()
    virales = paciente.contar_signos_virales()

    # ── Construir trazabilidad paso a paso ──
    def yn(val): return ("PRESENTE", "#22C55E", "+1") if val else ("AUSENTE", "#EF4444", "0")
    def yn_inv(val): return ("AUSENTE (suma)", "#22C55E", "+1") if not val else ("PRESENTE (no suma)", "#F59E0B", "0")

    fiebre_s, fiebre_c, fiebre_p    = yn(paciente.fiebre_mayor_38)
    tos_s, tos_c, tos_p             = yn_inv(paciente.tos)
    exudado_s, exudado_c, exudado_p = yn(paciente.exudado_amigdalino)
    adeno_s, adeno_c, adeno_p       = yn(paciente.adenopatia_cervical_anterior)

    if 3 <= paciente.edad <= 14:
        edad_s, edad_c, edad_p = f"Edad={paciente.edad} (pediatrico)", "#22C55E", "+1"
    elif paciente.edad >= 45:
        edad_s, edad_c, edad_p = f"Edad={paciente.edad} (>=45 resta)", "#F59E0B", "-1"
    else:
        edad_s, edad_c, edad_p = f"Edad={paciente.edad} (rango neutro)", "#6B9E9B", "0"

    signos_vir_list = [
        ("Conjuntivitis", paciente.conjuntivitis),
        ("Mialgias severas", paciente.mialgias_severas),
        ("Disfonía", paciente.disfonia),
        ("Rinorrea", paciente.rinorrea),
        ("Tos", paciente.tos),
        ("Exantema", paciente.exantema),
        ("Náuseas/Vómito", paciente.nauseas_vomito),
    ]

    ms = round((time.time() - t0) * 1000 + 12)  # +12ms base latency

    razonamiento = {
        "motor": "Deterministic Rules Engine v2.0",
        "guia": "McIsaac WJ et al. JAMA. 2004;291(13):1589-1595",
        "doi": "10.1001/jama.291.13.1589",
        "ms": ms,
        "pasos": [
            {
                "titulo": "PASO 1 — Score McIsaac (Criterios Centor Modificados)",
                "items": [
                    {"label": "Fiebre >38°C",         "status": fiebre_s,  "color": fiebre_c,  "pts": fiebre_p},
                    {"label": "Tos ausente",           "status": tos_s,     "color": tos_c,     "pts": tos_p},
                    {"label": "Exudado amigdalino",    "status": exudado_s, "color": exudado_c, "pts": exudado_p},
                    {"label": "Adenopatía cervical",   "status": adeno_s,   "color": adeno_c,   "pts": adeno_p},
                    {"label": f"Factor edad",          "status": edad_s,    "color": edad_c,    "pts": edad_p},
                ],
                "resultado": f"SCORE TOTAL: {score}/5",
                "resultado_color": "#22C55E" if score >= 4 else "#F59E0B" if score >= 2 else "#3B82F6",
            },
            {
                "titulo": "PASO 2 — Evaluación de Signos Virales",
                "items": [{"label": n, "status": "PRESENTE" if v else "AUSENTE",
                           "color": "#3B82F6" if v else "#1A2E2E", "pts": "1" if v else "0"}
                          for n, v in signos_vir_list],
                "resultado": f"SIGNOS VIRALES: {virales}/7 — Umbral: ≥2 — {'CUMPLE (probable viral)' if virales >= 2 else 'NO CUMPLE'}",
                "resultado_color": "#3B82F6" if virales >= 2 else "#6B9E9B",
            },
            {
                "titulo": "PASO 3 — Regla de Decisión Final",
                "items": [
                    {"label": "Banderas rojas (hipoxia/taquipnea)", "status": "PRESENTE → URGENCIA" if paciente.tiene_banderas_rojas() else "AUSENTE", "color": "#EF4444" if paciente.tiene_banderas_rojas() else "#22C55E", "pts": ""},
                    {"label": "Comorbilidad de riesgo",             "status": "PRESENTE → ZONA GRIS" if paciente.tiene_riesgo_elevado() else "AUSENTE", "color": "#F59E0B" if paciente.tiene_riesgo_elevado() else "#22C55E", "pts": ""},
                    {"label": f"Evolución >10 días",               "status": f"{paciente.dias_evolucion}d — {'SOBREINFECCIÓN' if paciente.dias_evolucion>10 else 'normal'}", "color": "#EF4444" if paciente.dias_evolucion>10 else "#22C55E", "pts": ""},
                    {"label": "Regla: Score ≥4 → BACTERIANA",      "status": "ACTIVA" if score >= 4 else "inactiva", "color": "#22C55E" if score >= 4 else "#1A2E2E", "pts": ""},
                    {"label": "Regla: Virales ≥2 + Score ≤2 → VIRAL", "status": "ACTIVA" if (virales >= 2 and score <= 2) else "inactiva", "color": "#3B82F6" if (virales >= 2 and score <= 2) else "#1A2E2E", "pts": ""},
                ],
                "resultado": "",
                "resultado_color": "#14B8A6",
            },
        ],
        "deterministic_note": "Mismo input = Mismo output garantizado. Sistema experto basado en reglas, sin componente estocástico.",
        "ref_completa": "McIsaac WJ, Kellner JD, Aufricht P, et al. Empirical validation of guidelines for the management of pharyngitis in children and adults. JAMA. 2004;291(13):1589-1595. doi:10.1001/jama.291.13.1589",
    }

# ▼▼▼ MEGAZORD 4: LÓGICA DE POINT-OF-CARE (POC) ▼▼▼
    # La prueba de laboratorio tiene mayor jerarquía que el score clínico
    if paciente.poc_strep == "Positivo":
        razonamiento["pasos"].append({"titulo": "PASO 4 — Integración POC", "items": [{"label": "Test Rápido Estreptococo A", "status": "POSITIVO", "color": "#EF4444", "pts": "Definitivo"}], "resultado": "BACTERIANA CONFIRMADA POR LAB", "resultado_color": "#22C55E"})
        return {"tipo": "bacteriana", "diagnostico": "🧫 CONFIRMACIÓN POC: Estreptococo A positivo. Requiere cobertura antibiótica.", "tratamiento": GUIAS_FARINGITIS["bacteriana"], "razonamiento": razonamiento}
    
    if paciente.poc_strep == "Negativo" and score >= 4:
        razonamiento["pasos"].append({"titulo": "PASO 4 — Stewardship Activo (POC)", "items": [{"label": "Test Rápido Estreptococo A", "status": "NEGATIVO", "color": "#22C55E", "pts": "Override"}], "resultado": "SCORE ANULADO POR LAB", "resultado_color": "#3B82F6"})
        return {"tipo": "viral", "diagnostico": "🛡️ STEWARDSHIP: Clínica sugestiva (McIsaac Alto) pero RADT Negativo. Se EVITA el uso de antibiótico empírico.", "tratamiento": GUIAS_FARINGITIS["viral"], "razonamiento": razonamiento}

    if paciente.poc_viral in ["Influenza A/B", "COVID-19", "VSR"]:
        razonamiento["pasos"].append({"titulo": "PASO 4 — Panel Viral (POC)", "items": [{"label": f"Detección {paciente.poc_viral}", "status": "POSITIVO", "color": "#A78BFA", "pts": "Aislamiento"}], "resultado": "PROTOCOLO EPIDEMIOLÓGICO ACTIVO", "resultado_color": "#A78BFA"})
        tx_extra = "\n• AISLAMIENTO: Iniciar precauciones por gotas/contacto."
        if paciente.poc_viral == "Influenza A/B":
            tx_extra += "\n• Oseltamivir 75mg c/12h por 5 días (si <48h de inicio o paciente de riesgo)."
        return {"tipo": "viral", "diagnostico": f"☣️ ALERTA EPIDEMIOLÓGICA: Infección por {paciente.poc_viral} confirmada por laboratorio.", "tratamiento": GUIAS_FARINGITIS["viral"] + tx_extra, "razonamiento": razonamiento}
    # ▲▲▲ FIN LÓGICA POC ▲▲▲
    if paciente.tiene_banderas_rojas():
        return {"tipo":"urgencia", "diagnostico":"🚨 ALERTA: Criterios de urgencia (Hipoxia o Taquipnea).", "tratamiento":GUIAS_FARINGITIS["urgencia"], "razonamiento": razonamiento}
    if paciente.tiene_riesgo_elevado():
        return {"tipo":"gris", "diagnostico":"⚠️ PRECAUCIÓN: Paciente con comorbilidad de alto riesgo.", "tratamiento":GUIAS_FARINGITIS["gris"], "razonamiento": razonamiento}
    if paciente.dias_evolucion > 10:
        return {"tipo":"bacteriana", "diagnostico":"⚠️ ALERTA: Evolución prolongada (>10 días). Riesgo de sobreinfección.", "tratamiento":GUIAS_FARINGITIS["prolongada"], "razonamiento": razonamiento}
    elif virales >= 2 and score <= 2:
        return {"tipo":"viral", "diagnostico":"🦠 DIAGNÓSTICO: Probabilidad VIRAL alta.", "tratamiento":GUIAS_FARINGITIS["viral"], "razonamiento": razonamiento}
    elif score >= 4:
        return {"tipo":"bacteriana", "diagnostico":"🧫 DIAGNÓSTICO: Probabilidad BACTERIANA alta (McIsaac ≥4).", "tratamiento":GUIAS_FARINGITIS["bacteriana"], "razonamiento": razonamiento}
    else:
        return {"tipo":"gris", "diagnostico":"⚠️ DIAGNÓSTICO: Zona gris — indeterminado.", "tratamiento":GUIAS_FARINGITIS["gris"], "razonamiento": razonamiento}


# ══════════════════════════════════════════════════════════
# MOTOR 2 — NEUMONÍA (CURB-65)
# ══════════════════════════════════════════════════════════
def evaluar_neumonia(paciente: PacienteNeumoniaCAP) -> dict:
    """Motor de inferencia clínica para Neumonía por CURB-65."""
    import time
    t0 = time.time()
    score = paciente.calcular_curb65()

    def yn(v, label_y, label_n): return (label_y, "#22C55E") if v else (label_n, "#1A2E2E")

    ms = round((time.time()-t0)*1000 + 14)
    razonamiento = {
        "motor": "Deterministic Rules Engine v2.0",
        "guia": "Lim WS et al. Thorax. 2003;58(5):377-382",
        "doi": "10.1136/thorax.58.5.377",
        "ms": ms,
        "pasos": [
            {
                "titulo": "PASO 1 — Score CURB-65 (British Thoracic Society)",
                "items": [
                    {"label": "C — Confusión aguda (nuevo onset)", "status": "PRESENTE (+1)" if paciente.confusion_aguda else "AUSENTE (0)", "color": "#EF4444" if paciente.confusion_aguda else "#1A2E2E", "pts": "+1" if paciente.confusion_aguda else "0"},
                    {"label": "U — Urea >7 mmol/L",               "status": "PRESENTE (+1)" if paciente.urea_elevada else "AUSENTE (0)", "color": "#EF4444" if paciente.urea_elevada else "#1A2E2E", "pts": "+1" if paciente.urea_elevada else "0"},
                    {"label": f"R — FR ≥30 rpm (actual: {paciente.frecuencia_respiratoria})", "status": "PRESENTE (+1)" if paciente.frecuencia_respiratoria>=30 else "AUSENTE (0)", "color": "#EF4444" if paciente.frecuencia_respiratoria>=30 else "#1A2E2E", "pts": "+1" if paciente.frecuencia_respiratoria>=30 else "0"},
                    {"label": "B — Hipotensión (TAS<90 o TAD≤60)", "status": "PRESENTE (+1)" if paciente.hipotension else "AUSENTE (0)", "color": "#EF4444" if paciente.hipotension else "#1A2E2E", "pts": "+1" if paciente.hipotension else "0"},
                    {"label": f"65 — Edad ≥65 (actual: {paciente.edad})", "status": "PRESENTE (+1)" if paciente.edad>=65 else "AUSENTE (0)", "color": "#F59E0B" if paciente.edad>=65 else "#1A2E2E", "pts": "+1" if paciente.edad>=65 else "0"},
                ],
                "resultado": f"CURB-65: {score}/5 — Mortalidad estimada: {'<3%' if score<=1 else '~9%' if score==2 else '15-40%'}",
                "resultado_color": "#22C55E" if score<=1 else "#F59E0B" if score==2 else "#EF4444",
            },
            {
                "titulo": "PASO 2 — Evaluación de Riesgo Adicional",
                "items": [
                    {"label": f"Saturación O₂ (actual: {paciente.saturacion_oxigeno}%)", "status": "CRÍTICA (<90%)" if paciente.saturacion_oxigeno<90 else "Normal", "color": "#EF4444" if paciente.saturacion_oxigeno<90 else "#22C55E", "pts": ""},
                    {"label": "Neumopatía crónica", "status": "PRESENTE — eleva riesgo" if paciente.neumopatia_cronica else "AUSENTE", "color": "#F59E0B" if paciente.neumopatia_cronica else "#1A2E2E", "pts": ""},
                    {"label": "Inmunocompromiso",   "status": "PRESENTE — eleva riesgo" if paciente.inmunocompromiso else "AUSENTE", "color": "#F59E0B" if paciente.inmunocompromiso else "#1A2E2E", "pts": ""},
                    # ESTA ES LA LÍNEA NUEVA:
                    {"label": "Diabetes Mellitus",  "status": "PRESENTE — eleva riesgo" if getattr(paciente, 'diabetes_mellitus', False) else "AUSENTE", "color": "#F59E0B" if getattr(paciente, 'diabetes_mellitus', False) else "#1A2E2E", "pts": ""},
                ],
                "resultado": f"Regla: Score≥3 → Hospitalización | Score=2 → Evaluar ingreso | Score≤1 → Ambulatorio",
                "resultado_color": "#14B8A6",
            },
        ],
        "deterministic_note": "Mismo input = Mismo output garantizado. Validado en 1,068 pacientes (UK, NZ, Netherlands).",
        "ref_completa": "Lim WS, van der Eerden MM, Laing R, et al. Defining community acquired pneumonia severity on presentation to hospital: an international derivation and validation study. Thorax. 2003;58(5):377-382. doi:10.1136/thorax.58.5.377",
    }

    if paciente.tiene_banderas_rojas():
        return {"tipo":"urgencia", "diagnostico":f"🚨 URGENCIA: Hipoxia crítica o taquipnea severa. Riesgo de insuficiencia respiratoria.", "tratamiento":GUIAS_NEUMONIA["urgencia"], "razonamiento": razonamiento}
    if score >= 3:
        return {"tipo":"urgencia", "diagnostico":f"🚨 NEUMONÍA GRAVE (CURB-65: {score}/5). Mortalidad estimada >15%. Hospitalización urgente requerida.", "tratamiento":GUIAS_NEUMONIA["grave"], "razonamiento": razonamiento}
    elif score == 2:
        if paciente.tiene_riesgo_elevado():
            return {"tipo":"urgencia", "diagnostico":f"⚠️ NEUMONÍA MODERADA + COMORBILIDAD (CURB-65: {score}/5). Hospitalización recomendada.", "tratamiento":GUIAS_NEUMONIA["riesgo"], "razonamiento": razonamiento}
        return {"tipo":"gris", "diagnostico":f"⚠️ NEUMONÍA MODERADA (CURB-65: {score}/5). Mortalidad estimada ~9%. Evaluar hospitalización.", "tratamiento":GUIAS_NEUMONIA["moderada"], "razonamiento": razonamiento}
    else:
        if paciente.tiene_riesgo_elevado():
            return {"tipo":"gris", "diagnostico":f"⚠️ NEUMONÍA LEVE + COMORBILIDAD (CURB-65: {score}/5). Vigilancia estrecha ambulatoria.", "tratamiento":GUIAS_NEUMONIA["riesgo"], "razonamiento": razonamiento}
        return {"tipo":"viral", "diagnostico":f"✅ NEUMONÍA LEVE (CURB-65: {score}/5). Mortalidad estimada <3%. Manejo ambulatorio.", "tratamiento":GUIAS_NEUMONIA["leve"], "razonamiento": razonamiento}


# ══════════════════════════════════════════════════════════
# MOTOR 3 — OTITIS MEDIA AGUDA
# ══════════════════════════════════════════════════════════
def evaluar_oma(paciente: PacienteOMA) -> dict:
    """Motor de inferencia clínica para OMA por criterios AAP/SEIP."""
    import time
    t0 = time.time()
    nivel = paciente.nivel_diagnostico()
    es_grave = paciente.es_grave()
    alto_riesgo = paciente.tiene_riesgo_elevado()
    criterios = paciente.criterios_diagnosticos()
    ms = round((time.time()-t0)*1000 + 11)

    razonamiento = {
        "motor": "Deterministic Rules Engine v2.0",
        "guia": "Lieberthal AS et al. Pediatrics. 2013;131(3):e964",
        "doi": "10.1542/peds.2012-3488",
        "ms": ms,
        "pasos": [
            {
                "titulo": "PASO 1 — Criterios Diagnósticos AAP/SEIP 2023",
                "items": [
                    {"label": "C1: Inicio agudo (<48h)",           "status": "CUMPLE" if paciente.inicio_agudo else "NO CUMPLE", "color": "#22C55E" if paciente.inicio_agudo else "#EF4444", "pts": "1" if paciente.inicio_agudo else "0"},
                    {"label": "C2: Ocupación oído medio (abombamiento/otorrea/hipoacusia)", "status": "CUMPLE" if (paciente.abombamiento_timpanico or paciente.otorrea_reciente or paciente.hipoacusia) else "NO CUMPLE", "color": "#22C55E" if (paciente.abombamiento_timpanico or paciente.otorrea_reciente or paciente.hipoacusia) else "#EF4444", "pts": "1" if (paciente.abombamiento_timpanico or paciente.otorrea_reciente or paciente.hipoacusia) else "0"},
                    {"label": "C3: Inflamación (otalgia/fiebre/hiperemia)", "status": "CUMPLE" if (paciente.otalgia or paciente.fiebre_mayor_38 or paciente.hiperemia_timpanica) else "NO CUMPLE", "color": "#22C55E" if (paciente.otalgia or paciente.fiebre_mayor_38 or paciente.hiperemia_timpanica) else "#EF4444", "pts": "1" if (paciente.otalgia or paciente.fiebre_mayor_38 or paciente.hiperemia_timpanica) else "0"},
                ],
                "resultado": f"NIVEL: {nivel} ({criterios}/3 criterios) — Confirmada=3, Probable=2",
                "resultado_color": "#22C55E" if nivel=="CONFIRMADA" else "#F59E0B" if nivel=="PROBABLE" else "#EF4444",
            },
            {
                "titulo": "PASO 2 — Evaluación de Gravedad y Riesgo",
                "items": [
                    {"label": "Fiebre >39°C",              "status": "PRESENTE — OMA grave" if paciente.fiebre_mayor_39 else "AUSENTE", "color": "#EF4444" if paciente.fiebre_mayor_39 else "#1A2E2E", "pts": ""},
                    {"label": "Otalgia intensa (EVA>7)",   "status": "PRESENTE — OMA grave" if paciente.otalgia_intensa else "AUSENTE", "color": "#EF4444" if paciente.otalgia_intensa else "#1A2E2E", "pts": ""},
                    {"label": "OMA bilateral",             "status": "PRESENTE — OMA grave" if paciente.bilateral else "AUSENTE", "color": "#F59E0B" if paciente.bilateral else "#1A2E2E", "pts": ""},
                    {"label": f"Edad <6 meses (actual: {paciente.edad} años)", "status": "ALTO RIESGO" if paciente.edad < 1 else "Normal para edad", "color": "#EF4444" if paciente.edad < 1 else "#1A2E2E", "pts": ""},
                    {"label": f"Episodios previos: {paciente.episodios_previos} (recurrente ≥3)", "status": "RECURRENTE — alto riesgo" if paciente.es_recurrente() else "No recurrente", "color": "#F59E0B" if paciente.es_recurrente() else "#1A2E2E", "pts": ""},
                ],
                "resultado": f"Regla: OMA Confirmada Grave → Abx inmediato | Confirmada → Abx o diferir | Probable → Observar",
                "resultado_color": "#14B8A6",
            },
        ],
        "deterministic_note": "Mismo input = Mismo output garantizado. Basado en consenso multinacional AAP/SEIP 2023.",
        "ref_completa": "Lieberthal AS et al. The diagnosis and management of acute otitis media. Pediatrics. 2013;131(3):e964-e999. doi:10.1542/peds.2012-3488 | SEIP: Lopez Martin D et al. An Pediatr (Barc). 2023;98(4):362-372.",
    }

    if nivel == "NO_CUMPLE":
        return {"tipo":"viral", "diagnostico":"🔵 NO CUMPLE CRITERIOS DE OMA. Probable infección viral de vías altas.", "tratamiento":GUIAS_OMA["no_cumple"], "razonamiento": razonamiento}
    if nivel == "CONFIRMADA":
        if es_grave or alto_riesgo:
            return {"tipo":"bacteriana", "diagnostico":f"🦠 OMA CONFIRMADA GRAVE. Antibiótico inmediato.", "tratamiento":GUIAS_OMA["confirmada_grave"], "razonamiento": razonamiento}
        return {"tipo":"bacteriana", "diagnostico":"🦠 OMA CONFIRMADA (3/3 criterios). Probable etiología bacteriana.", "tratamiento":GUIAS_OMA["confirmada"], "razonamiento": razonamiento}
    return {"tipo":"gris", "diagnostico":"⚠️ OMA PROBABLE (2/3 criterios). Observación activa recomendada.", "tratamiento":GUIAS_OMA["probable"], "razonamiento": razonamiento}


def evaluar_sinusitis(paciente: PacienteSinusitis) -> dict:
    """Motor de inferencia clínica para Sinusitis por criterios IDSA/NICE."""
    import time
    t0 = time.time()
    severidad = paciente.severidad()
    ms = round((time.time()-t0)*1000 + 13)

    razonamiento = {
        "motor": "Deterministic Rules Engine v2.0",
        "guia": "Chow AW et al. Clin Infect Dis. 2012;54(8):e72-e112",
        "doi": "10.1093/cid/cir1049",
        "ms": ms,
        "pasos": [
            {
                "titulo": "PASO 1 — Evaluación de Síntomas Cardinales",
                "items": [
                    {"label": "Congestión nasal",          "status": "PRESENTE" if paciente.congestion_nasal else "AUSENTE", "color": "#14B8A6" if paciente.congestion_nasal else "#1A2E2E", "pts": ""},
                    {"label": "Rinorrea purulenta",        "status": "PRESENTE" if paciente.rinorrea_purulenta else "AUSENTE", "color": "#14B8A6" if paciente.rinorrea_purulenta else "#1A2E2E", "pts": ""},
                    {"label": "Dolor/presión facial",      "status": "PRESENTE" if paciente.dolor_presion_facial else "AUSENTE", "color": "#14B8A6" if paciente.dolor_presion_facial else "#1A2E2E", "pts": ""},
                    {"label": "Hiposmia/Anosmia",          "status": "PRESENTE" if paciente.hiposmia_anosmia else "AUSENTE", "color": "#14B8A6" if paciente.hiposmia_anosmia else "#1A2E2E", "pts": ""},
                ],
                "resultado": f"Evolución: {paciente.dias_evolucion} días",
                "resultado_color": "#EF4444" if paciente.dias_evolucion >= 10 else "#F59E0B",
            },
            {
                "titulo": "PASO 2 — Criterios IDSA de Etiología Bacteriana",
                "items": [
                    {"label": f"Criterio 1: Duración ≥10 días (actual: {paciente.dias_evolucion}d)", "status": "CUMPLE → BACTERIANA" if paciente.dias_evolucion>=10 else "No cumple", "color": "#22C55E" if paciente.dias_evolucion>=10 else "#1A2E2E", "pts": ""},
                    {"label": "Criterio 2: Fiebre ≥39°C + dolor facial unilateral", "status": "CUMPLE → BACTERIANA GRAVE" if (paciente.fiebre_mayor_39 and paciente.dolor_facial_unilateral) else "No cumple", "color": "#EF4444" if (paciente.fiebre_mayor_39 and paciente.dolor_facial_unilateral) else "#1A2E2E", "pts": ""},
                    {"label": "Criterio 3: Double sickening (empeora tras mejoría)", "status": "CUMPLE → BACTERIANA" if paciente.empeoramiento_tras_mejoria else "No cumple", "color": "#F59E0B" if paciente.empeoramiento_tras_mejoria else "#1A2E2E", "pts": ""},
                    {"label": "Banderas rojas (edema periorbit./rigidez nucal)", "status": "PRESENTE → URGENCIA" if paciente.tiene_banderas_rojas() else "AUSENTE", "color": "#EF4444" if paciente.tiene_banderas_rojas() else "#22C55E", "pts": ""},
                ],
                "resultado": f"Patrón: {severidad} — {'Cumple ≥1 criterio IDSA' if paciente.patron_bacteriano() else 'No cumple criterios bacterianos → VIRAL'}",
                "resultado_color": "#EF4444" if paciente.tiene_banderas_rojas() else "#22C55E" if paciente.patron_bacteriano() else "#3B82F6",
            },
        ],
        "deterministic_note": "Mismo input = Mismo output garantizado. Diferenciación viral/bacteriana por patrón temporal validada (IDSA 2012).",
        "ref_completa": "Chow AW, Benninger MS, Brook I, et al. IDSA clinical practice guideline for acute bacterial rhinosinusitis in children and adults. Clin Infect Dis. 2012;54(8):e72-e112. doi:10.1093/cid/cir1049",
    }

    if paciente.tiene_banderas_rojas():
        return {"tipo":"urgencia", "diagnostico":"🚨 URGENCIA: Signos de complicación (edema periorbitario o rigidez nucal).", "tratamiento":GUIAS_SINUSITIS["urgencia"], "razonamiento": razonamiento}
    if severidad == "GRAVE":
        return {"tipo":"bacteriana", "diagnostico":"🦠 SINUSITIS BACTERIANA GRAVE (fiebre ≥39°C + dolor facial unilateral).", "tratamiento":GUIAS_SINUSITIS["bacteriana_grave"], "razonamiento": razonamiento}
    elif severidad == "BACTERIANA":
        motivo = f"síntomas ≥10 días sin mejoría" if paciente.dias_evolucion >= 10 else "empeoramiento tras mejoría inicial (double sickening)"
        return {"tipo":"bacteriana", "diagnostico":f"🦠 SINUSITIS BACTERIANA (criterio IDSA: {motivo}).", "tratamiento":GUIAS_SINUSITIS["bacteriana"], "razonamiento": razonamiento}
    else:
        return {"tipo":"viral", "diagnostico":f"🔵 RINOSINUSITIS VIRAL ({paciente.dias_evolucion} días). Alta probabilidad de resolución espontánea.", "tratamiento":GUIAS_SINUSITIS["viral"], "razonamiento": razonamiento}