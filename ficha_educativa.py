"""
SITRE — Módulo de Desescalada Narrativa (MEGAZORD 4)
=====================================================
Genera la Ficha Educativa para el Paciente.
Diseñada para:
  - Abrirse desde el QR del PDF en el celular del paciente
  - Reducir la presión de prescripción ("doctor shopping")
  - Empoderar al paciente con información empática y sin tecnicismos
  - Cumplir con lineamientos CDC/OMS sobre comunicación de RAM

Ref: CDC Be Antibiotics Aware | OMS AMR Communication Toolkit
"""

# ─── Contenido narrativo por patología y tipo ────────────────────────────────

FICHA_CONTENT = {
    "faringitis": {
        "viral": {
            "emoji_hero":   "🧊",
            "titulo":       "Su infección es viral",
            "subtitulo":    "NO necesita antibióticos — y eso es una buena noticia",
            "color_hero":   "#0EA5E9",
            "color_accent": "#38BDF8",
            "mito_titulo":  "¿Por qué no me dan antibiótico si me duele tanto?",
            "mito_cuerpo":  (
                "Porque su dolor de garganta lo está causando un virus — "
                "igual que el del resfriado común. "
                "Los antibióticos matan bacterias, no virus. "
                "Darlos hoy no reduciría su dolor ni un día, "
                "pero sí dañaría las bacterias buenas de su cuerpo "
                "y volvería más difícil tratarlo si algún día tiene "
                "una infección grave de verdad."
            ),
            "dato_oms":     "El 80% de los dolores de garganta son causados por virus. La OMS advierte que el mal uso de antibióticos es una de las mayores amenazas para la salud mundial.",
            "que_hacer":    [
                ("💊", "Paracetamol o Ibuprofeno cada 6-8 horas para el dolor y la fiebre"),
                ("💧", "Tome mucho líquido: agua, caldos, jugos naturales — al menos 2 litros al día"),
                ("😴", "Descanse. Su sistema inmune trabaja mejor cuando duerme"),
                ("🧂", "Haga gárgaras con agua tibia con sal 3-4 veces al día — alivia el dolor"),
                ("🚫", "NO tome antibióticos guardados de tratamientos anteriores"),
            ],
            "cuando_regresar": [
                "Fiebre que no baja después del tercer día",
                "Dificultad para respirar o para tragar saliva",
                "Cuello muy tieso o dolor de oído intenso",
                "Manchas blancas nuevas en la garganta después del día 3",
                "Se siente mucho peor después de haber mejorado",
            ],
            "mensaje_final": "Su médico tomó la decisión correcta al no recetarle antibiótico. Confíe en el proceso — la mayoría de los casos virales mejoran solos en 5-7 días.",
        },
        "bacteriana": {
            "emoji_hero":   "🦠",
            "titulo":       "Su infección necesita antibiótico",
            "subtitulo":    "Siga el tratamiento completo — es muy importante",
            "color_hero":   "#22C55E",
            "color_accent": "#4ADE80",
            "mito_titulo":  "¿Puedo parar el antibiótico si ya me siento mejor?",
            "mito_cuerpo":  (
                "No. Aunque se sienta mejor en 2-3 días, las bacterias "
                "no están completamente eliminadas. Si para el antibiótico antes, "
                "las bacterias que sobrevivieron pueden hacerse resistentes "
                "y regresar más fuertes. Completar el ciclo protege "
                "a su familia y a toda la comunidad."
            ),
            "dato_oms":     "Completar el ciclo antibiótico es fundamental. Interrumpirlo es una de las causas principales de resistencia bacteriana.",
            "que_hacer":    [
                ("💊", "Tome el antibiótico exactamente como se indicó — misma hora todos los días"),
                ("⏰", "No se salte dosis aunque se sienta bien"),
                ("🍽️", "Tómelo con alimentos si le cae pesado al estómago"),
                ("💧", "Mantenga buena hidratación"),
                ("🚫", "No comparta su antibiótico con nadie"),
            ],
            "cuando_regresar": [
                "Fiebre que no baja después de 2 días de antibiótico",
                "Alergia: ronchas, cara hinchada, dificultad para respirar",
                "Diarrea intensa o con sangre",
                "Se siente igual o peor después de 48 horas de tratamiento",
            ],
            "mensaje_final": "Tome el antibiótico completo aunque se sienta mejor. Es el acto más responsable que puede hacer por su salud y la de su familia.",
        },
        "urgencia": {
            "emoji_hero":   "🚨",
            "titulo":       "Necesita atención urgente",
            "subtitulo":    "Diríjase a urgencias del hospital más cercano ahora",
            "color_hero":   "#EF4444",
            "color_accent": "#F87171",
            "mito_titulo":  "¿Por qué necesito ir al hospital?",
            "mito_cuerpo":  "Su médico detectó señales que requieren evaluación especializada inmediata. No espere a que empeore. En urgencias pueden darle el cuidado que necesita.",
            "dato_oms":     "Actuar rápido en infecciones graves puede salvar vidas. No postergue la atención.",
            "que_hacer":    [
                ("🏥", "Vaya AHORA al hospital o urgencias más cercano"),
                ("📋", "Lleve este reporte y todos sus medicamentos actuales"),
                ("📞", "Si no puede moverse, llame al 911"),
            ],
            "cuando_regresar": [],
            "mensaje_final": "Su salud es lo primero. No espere.",
        },
    },
    "neumonia": {
        "viral": {
            "emoji_hero":   "🫁",
            "titulo":       "Su neumonía es leve",
            "subtitulo":    "Puede manejarse en casa con cuidado y vigilancia",
            "color_hero":   "#6366F1",
            "color_accent": "#818CF8",
            "mito_titulo":  "¿Tengo neumonía y no me internan?",
            "mito_cuerpo":  (
                "Las neumonías leves sin factores de riesgo graves se tratan "
                "perfectamente en casa. Su médico calculó que su caso puede "
                "manejarse ambulatoriamente — eso es una buena noticia. "
                "Lo importante es que tome el tratamiento y regrese en 48 horas "
                "o antes si siente que empeora."
            ),
            "dato_oms":     "La mayoría de las neumonías comunitarias leves se curan con tratamiento oral en casa. El reposo y la hidratación son tan importantes como el medicamento.",
            "que_hacer":    [
                ("💊", "Tome el medicamento que le recetaron exactamente como se indicó"),
                ("💧", "Hidratación intensa: mínimo 2-3 litros de agua al día"),
                ("😴", "Reposo en cama o sofá. Su cuerpo necesita toda su energía para combatir la infección"),
                ("🌡️", "Mida su temperatura dos veces al día"),
                ("📱", "Regrese a revisión en exactamente 48 horas, aunque se sienta mejor"),
            ],
            "cuando_regresar": [
                "Dificultad para respirar que aumenta",
                "Labios o uñas con color azulado",
                "Confusión o somnolencia inusual",
                "Fiebre mayor a 39°C que no baja con medicamento",
                "No puede tomar líquidos ni medicamentos",
            ],
            "mensaje_final": "La neumonía leve se cura bien en casa. Pero el control a 48h es OBLIGATORIO — no lo cancele aunque se sienta mejor.",
        },
        "urgencia": {
            "emoji_hero":   "🚨",
            "titulo":       "Necesita hospitalización urgente",
            "subtitulo":    "Vaya al hospital ahora mismo",
            "color_hero":   "#EF4444",
            "color_accent": "#F87171",
            "mito_titulo":  "¿Por qué necesito internarme?",
            "mito_cuerpo":  "Su nivel de gravedad requiere medicamentos intravenosos y vigilancia continua que no es posible en casa. Es la decisión más segura para usted.",
            "dato_oms":     "La neumonía grave no tratada puede ser mortal. La atención hospitalaria a tiempo salva vidas.",
            "que_hacer":    [
                ("🏥", "Vaya al hospital de inmediato"),
                ("📋", "Lleve este reporte y lista de medicamentos actuales"),
                ("👨‍👩‍👧", "Acompáñese de un familiar si es posible"),
            ],
            "cuando_regresar": [],
            "mensaje_final": "No postergue la atención. Cada hora importa.",
        },
        "gris": {
            "emoji_hero":   "⚠️",
            "titulo":       "Su caso requiere vigilancia",
            "subtitulo":    "Siga el tratamiento y regrese exactamente en 48 horas",
            "color_hero":   "#F59E0B",
            "color_accent": "#FCD34D",
            "mito_titulo":  "¿Por qué tengo que regresar si me siento igual?",
            "mito_cuerpo":  "Su médico necesita ver cómo evoluciona en 48 horas para tomar la mejor decisión. Una neumonía moderada puede mejorar o empeorar — el seguimiento es parte del tratamiento.",
            "dato_oms":     "El seguimiento a 48h en neumonías moderadas es un estándar de oro en medicina basada en evidencia.",
            "que_hacer":    [
                ("💊", "Tome el tratamiento indicado sin falta"),
                ("💧", "Hidratación: mínimo 2 litros al día"),
                ("😴", "Reposo. No haga actividad física"),
                ("📅", "Regrese en 48 horas aunque se sienta mejor"),
            ],
            "cuando_regresar": [
                "Dificultad para respirar que aumenta",
                "Fiebre mayor a 39°C",
                "Se siente peor en cualquier momento",
                "No puede tomar medicamentos o líquidos",
            ],
            "mensaje_final": "El control a 48h no es opcional — es parte de su tratamiento.",
        },
    },
    "oma": {
        "bacteriana": {
            "emoji_hero":   "👂",
            "titulo":       "Infección en el oído — necesita antibiótico",
            "subtitulo":    "Siga el tratamiento y el dolor mejorará pronto",
            "color_hero":   "#F59E0B",
            "color_accent": "#FCD34D",
            "mito_titulo":  "¿Cuánto tarda en quitarse el dolor de oído?",
            "mito_cuerpo":  (
                "Con el antibiótico correcto, el dolor de oído suele mejorar "
                "en 24-72 horas. Mientras tanto, el paracetamol o ibuprofeno "
                "son sus mejores aliados para el dolor. "
                "No interrumpa el antibiótico aunque ya no duela — "
                "la infección puede no estar completamente eliminada."
            ),
            "dato_oms":     "La otitis media bacteriana sin tratamiento puede complicarse con mastoiditis o pérdida auditiva. El antibiótico completo es esencial.",
            "que_hacer":    [
                ("💊", "Antibiótico exactamente como se indicó — no omita dosis"),
                ("🤕", "Paracetamol o Ibuprofeno para el dolor cada 6-8 horas"),
                ("🛌", "Duerma con la cabeza un poco elevada — alivia la presión"),
                ("🚫", "No meta agua al oído mientras dure la infección"),
                ("🌡️", "Mida la temperatura si hay fiebre"),
            ],
            "cuando_regresar": [
                "Dolor que NO mejora después de 2-3 días de antibiótico",
                "Fiebre que persiste o aumenta",
                "Salida de líquido por el oído",
                "Dolor detrás de la oreja (hueso mastoideo)",
                "Pérdida notable de la audición",
            ],
            "mensaje_final": "La otitis bien tratada se cura completamente. Complete el ciclo y proteja la audición.",
        },
        "viral": {
            "emoji_hero":   "🔵",
            "titulo":       "Su oído no tiene infección bacteriana",
            "subtitulo":    "No necesita antibiótico — el dolor mejorará solo",
            "color_hero":   "#3B82F6",
            "color_accent": "#60A5FA",
            "mito_titulo":  "¿Por qué me duele el oído si no tengo infección?",
            "mito_cuerpo":  (
                "El dolor de oído puede tener varias causas — no todas son infección bacteriana. "
                "Su médico evaluó que no hay signos de infección bacteriana confirmada. "
                "El antibiótico no ayudaría y sí podría hacerle daño. "
                "Los analgésicos son el tratamiento correcto por ahora."
            ),
            "dato_oms":     "Hasta el 80% de las otitis medias en niños mayores y adultos mejoran sin antibiótico. El uso innecesario genera resistencia.",
            "que_hacer":    [
                ("💊", "Paracetamol o Ibuprofeno para el dolor cada 6-8 horas"),
                ("🌡️", "Monitoree si aparece fiebre"),
                ("🚫", "No use gotas óticas sin indicación médica"),
                ("📅", "Regrese en 48-72 horas si no mejora o empeora"),
            ],
            "cuando_regresar": [
                "Dolor que aumenta o no mejora en 48-72 horas",
                "Aparece fiebre mayor de 38°C",
                "Salida de líquido por el oído",
                "Pérdida de audición notable",
            ],
            "mensaje_final": "Si en 48-72 horas no hay mejoría, regrese. Su médico puede reevaluar y ajustar el plan.",
        },
        "gris": {
            "emoji_hero":   "⚠️",
            "titulo":       "Observación activa de su oído",
            "subtitulo":    "Vigilancia 48-72 horas antes de decidir tratamiento",
            "color_hero":   "#F59E0B",
            "color_accent": "#FCD34D",
            "mito_titulo":  "¿Por qué no me dieron antibiótico de una vez?",
            "mito_cuerpo":  "Su caso está en el límite — los criterios no son suficientes para confirmar infección bacteriana todavía. Darle antibiótico sin necesidad le haría más mal que bien. Su médico le da 48-72 horas para observar cómo evoluciona.",
            "dato_oms":     "La prescripción diferida reduce el uso de antibióticos hasta un 40% sin empeorar los resultados clínicos (OMS/NICE 2023).",
            "que_hacer":    [
                ("💊", "Paracetamol o Ibuprofeno para el dolor"),
                ("📅", "Regrese en 48-72 horas — obligatorio"),
                ("📝", "Lleve nota de cómo evolucionó el dolor y si apareció fiebre"),
                ("🚫", "No compre antibiótico por su cuenta"),
            ],
            "cuando_regresar": [
                "El dolor empeora significativamente",
                "Aparece fiebre mayor de 38°C",
                "Salida de líquido por el oído",
                "El niño llora inconsolablemente",
            ],
            "mensaje_final": "Si en 48-72h mejora: bien. Si empeora: regrese — su médico tiene un plan.",
        },
    },
    "sinusitis": {
        "viral": {
            "emoji_hero":   "👃",
            "titulo":       "Su sinusitis es viral",
            "subtitulo":    "NO necesita antibiótico — mejorará en días",
            "color_hero":   "#8B5CF6",
            "color_accent": "#A78BFA",
            "mito_titulo":  "¿Por qué me duele tanto la cara si no me dan antibiótico?",
            "mito_cuerpo":  (
                "Su dolor facial y congestión son causados por un virus — "
                "el mismo tipo que causa un resfriado fuerte. "
                "Los senos paranasales se llenan de moco y eso presiona. "
                "Los antibióticos no eliminan virus, no reducirían su dolor, "
                "pero sí alterarían su flora intestinal y contribuirían "
                "a crear superbacterias en su comunidad."
            ),
            "dato_oms":     "El 98% de las sinusitis agudas son de origen viral y se curan sin antibiótico. La OMS reporta que la sinusitis es una de las causas más comunes de prescripción antibiótica innecesaria.",
            "que_hacer":    [
                ("🧂", "Lavados nasales con solución salina — 3-4 veces al día. Esto es lo más efectivo"),
                ("💊", "Paracetamol o Ibuprofeno para el dolor facial y la fiebre"),
                ("💧", "Hidratación abundante para fluidificar el moco"),
                ("🛁", "Vapores o baños calientes alivian la presión"),
                ("😴", "Reposo. Su cuerpo necesita energía para combatir el virus"),
            ],
            "cuando_regresar": [
                "Síntomas que no mejoran después de 10 días",
                "Fiebre alta (más de 39°C) con dolor facial intenso",
                "Empeoramiento después de haber mejorado",
                "Hinchazón alrededor del ojo",
                "Dolor de cabeza muy intenso o rigidez de cuello",
            ],
            "mensaje_final": "Los lavados nasales con agua salina tienen más evidencia científica que los antibióticos para su sinusitis. Úselos generosamente.",
        },
        "bacteriana": {
            "emoji_hero":   "🦠",
            "titulo":       "Su sinusitis necesita antibiótico",
            "subtitulo":    "Complete el tratamiento y no lo interrumpa",
            "color_hero":   "#22C55E",
            "color_accent": "#4ADE80",
            "mito_titulo":  "¿Cuánto tarda en quitarse?",
            "mito_cuerpo":  (
                "Con antibiótico correcto, suele mejorar en 5-7 días. "
                "Los lavados nasales TAMBIÉN son parte esencial del tratamiento "
                "para limpiar el moco y ayudar al antibiótico a llegar donde necesita."
            ),
            "dato_oms":     "La sinusitis bacteriana responde bien al tratamiento cuando se completa el ciclo. Complementar con lavados nasales duplica la efectividad.",
            "que_hacer":    [
                ("💊", "Antibiótico exactamente como se indicó — todos los días"),
                ("🧂", "Lavados nasales con solución salina — obligatorios, 3-4 veces al día"),
                ("💧", "Hidratación abundante"),
                ("🌿", "Spray nasal de corticoide si se recetó — úselo aunque no tenga síntomas"),
                ("🚫", "Evite descongestionantes en aerosol más de 3 días — generan rebote"),
            ],
            "cuando_regresar": [
                "Sin mejoría después de 3 días de antibiótico",
                "Hinchazón o enrojecimiento alrededor del ojo",
                "Visión doble o dificultad para mover los ojos",
                "Dolor de cabeza intenso o rigidez de cuello",
                "Fiebre que aumenta con el tratamiento",
            ],
            "mensaje_final": "Los lavados nasales son tan importantes como el antibiótico. No los omita.",
        },
        "urgencia": {
            "emoji_hero":   "🚨",
            "titulo":       "Necesita atención urgente",
            "subtitulo":    "Vaya al hospital de inmediato",
            "color_hero":   "#EF4444",
            "color_accent": "#F87171",
            "mito_titulo":  "¿Es tan grave una sinusitis?",
            "mito_cuerpo":  "En la mayoría de los casos no. Pero los síntomas que su médico detectó sugieren que la infección podría estar extendiéndose. La atención rápida previene complicaciones graves.",
            "dato_oms":     "Las complicaciones orbitarias o intracraneales de sinusitis no tratada pueden ser graves. La atención inmediata es esencial.",
            "que_hacer":    [
                ("🏥", "Vaya AHORA al servicio de urgencias"),
                ("📋", "Lleve este reporte"),
                ("👁️", "Si tiene visión doble o el ojo hinchado, es emergencia"),
            ],
            "cuando_regresar": [],
            "mensaje_final": "No espere. Vaya ahora.",
        },
    },
}


def get_ficha(patologia: str, tipo: str, folio: str, fecha_str: str, nombre_pat: str) -> dict:
    """Devuelve el contenido estructurado de la ficha para una patología y tipo dados."""
    data = FICHA_CONTENT.get(patologia, FICHA_CONTENT["faringitis"])
    content = data.get(tipo, data.get("viral", list(data.values())[0]))
    return {**content, "folio": folio, "fecha": fecha_str, "patologia_display": nombre_pat}


def generar_html_ficha(patologia: str, tipo: str, folio: str, fecha_str: str, nombre_pat: str) -> str:
    """
    Genera una página HTML completa y autocontenida para la ficha educativa.
    Diseñada para verse en móvil. No requiere internet para renderizarse.
    """
    f = get_ficha(patologia, tipo, folio, fecha_str, nombre_pat)
    color = f["color_hero"]
    accent = f["color_accent"]
    es_urgencia = tipo == "urgencia"

    que_hacer_html = "".join(f"""
    <div class="step">
      <span class="step-icon">{emoji}</span>
      <span class="step-text">{texto}</span>
    </div>""" for emoji, texto in f.get("que_hacer", []))

    alarmas_html = "".join(f"""
    <div class="alarm-item">
      <span class="alarm-dot">⚠</span>
      <span>{alarma}</span>
    </div>""" for alarma in f.get("cuando_regresar", []))

    alarmas_section = f"""
    <div class="section alarmas">
      <div class="section-title" style="color:#EF4444;">🚨 Regrese al médico si:</div>
      {alarmas_html}
    </div>""" if f.get("cuando_regresar") else ""

    mito_section = "" if es_urgencia else f"""
    <div class="section mito-box" style="border-color:{color}44; background:{color}0D;">
      <div class="mito-title" style="color:{accent};">💬 {f['mito_titulo']}</div>
      <div class="mito-body">{f['mito_cuerpo']}</div>
      <div class="oms-badge">
        <span class="oms-icon">🌍</span>
        <span class="oms-text">{f['dato_oms']}</span>
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>SITRE · Instrucciones para {nombre_pat}</title>
  <style>
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #050F0F;
      color: #F0FDFA;
      min-height: 100vh;
      padding-bottom: 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, {color}22, {color}08);
      border-bottom: 1px solid {color}44;
      padding: 32px 20px 24px;
      text-align: center;
      position: relative;
    }}
    .hero-emoji {{
      font-size: 4rem;
      display: block;
      margin-bottom: 12px;
      filter: drop-shadow(0 0 20px {color});
    }}
    .hero-eyebrow {{
      font-size: 0.6rem;
      font-weight: 700;
      letter-spacing: 4px;
      text-transform: uppercase;
      color: {accent};
      margin-bottom: 8px;
    }}
    .hero-title {{
      font-size: 1.6rem;
      font-weight: 700;
      color: #fff;
      line-height: 1.2;
      margin-bottom: 8px;
    }}
    .hero-sub {{
      font-size: 0.85rem;
      color: rgba(240,253,250,0.6);
      line-height: 1.4;
    }}
    .folio-bar {{
      background: rgba(255,255,255,0.04);
      border-bottom: 1px solid rgba(255,255,255,0.06);
      padding: 10px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.65rem;
      color: rgba(240,253,250,0.35);
      letter-spacing: 1px;
    }}
    .folio-id {{ color: {accent}; font-weight: 700; }}
    .container {{ padding: 0 16px; max-width: 480px; margin: 0 auto; }}
    .section {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 16px;
      padding: 18px;
      margin-top: 14px;
    }}
    .section-title {{
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: {accent};
      margin-bottom: 14px;
    }}
    .step {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255,255,255,0.04);
    }}
    .step:last-child {{ border-bottom: none; }}
    .step-icon {{ font-size: 1.2rem; flex-shrink: 0; margin-top: 1px; }}
    .step-text {{ font-size: 0.88rem; color: rgba(240,253,250,0.85); line-height: 1.45; }}
    .mito-box {{ border-width: 1px; border-style: solid; }}
    .mito-title {{
      font-size: 0.88rem;
      font-weight: 700;
      margin-bottom: 10px;
      line-height: 1.3;
    }}
    .mito-body {{
      font-size: 0.85rem;
      color: rgba(240,253,250,0.7);
      line-height: 1.6;
      margin-bottom: 12px;
    }}
    .oms-badge {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
      background: rgba(255,255,255,0.04);
      border-radius: 8px;
      padding: 8px 12px;
    }}
    .oms-icon {{ font-size: 1rem; flex-shrink: 0; }}
    .oms-text {{ font-size: 0.72rem; color: rgba(240,253,250,0.45); line-height: 1.45; }}
    .alarmas {{ border-color: rgba(239,68,68,0.2); }}
    .alarm-item {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 7px 0;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      font-size: 0.85rem;
      color: rgba(240,253,250,0.8);
      line-height: 1.4;
    }}
    .alarm-item:last-child {{ border-bottom: none; }}
    .alarm-dot {{ color: #F59E0B; font-size: 0.8rem; flex-shrink: 0; margin-top: 1px; }}
    .final-card {{
      background: linear-gradient(135deg, {color}1A, {color}08);
      border: 1px solid {color}44;
      border-radius: 16px;
      padding: 18px;
      margin-top: 14px;
      text-align: center;
    }}
    .final-text {{
      font-size: 0.9rem;
      color: rgba(240,253,250,0.8);
      line-height: 1.55;
      font-style: italic;
    }}
    .sitre-footer {{
      text-align: center;
      margin-top: 24px;
      padding: 0 20px;
    }}
    .sitre-brand {{
      font-size: 0.6rem;
      font-weight: 700;
      letter-spacing: 4px;
      text-transform: uppercase;
      color: rgba(240,253,250,0.2);
    }}
    .sitre-desc {{
      font-size: 0.6rem;
      color: rgba(240,253,250,0.15);
      margin-top: 4px;
      line-height: 1.4;
    }}
    @media (prefers-color-scheme: light) {{
      body {{ background: #F8FFFE; color: #0F2A28; }}
      .folio-bar {{ background: #E0F7F5; }}
      .section {{ background: #fff; border-color: #D1FAF5; }}
      .step-text {{ color: #1A4A45; }}
      .mito-body {{ color: #2D6660; }}
      .alarm-item {{ color: #1A4A45; }}
      .oms-text {{ color: #5A8A85; }}
      .sitre-brand, .sitre-desc {{ color: rgba(0,0,0,0.25); }}
    }}
  </style>
</head>
<body>
  <!-- HERO -->
  <div class="hero">
    <span class="hero-emoji">{f['emoji_hero']}</span>
    <div class="hero-eyebrow">SITRE · Instrucciones Personalizadas</div>
    <div class="hero-title">{f['titulo']}</div>
    <div class="hero-sub">{f['subtitulo']}</div>
  </div>

  <!-- FOLIO BAR -->
  <div class="folio-bar">
    <span>Folio: <span class="folio-id">{f['folio']}</span></span>
    <span>{f['fecha']} · {nombre_pat}</span>
  </div>

  <div class="container">

    <!-- MITO/EXPLICACIÓN -->
    {mito_section}

    <!-- QUÉ HACER -->
    {"" if es_urgencia else f'''
    <div class="section">
      <div class="section-title">💊 Qué hacer hoy</div>
      {que_hacer_html}
    </div>''' if f.get("que_hacer") else ""}

    <!-- URGENCIA: que_hacer siempre -->
    {f'''
    <div class="section" style="border-color:{color}44; background:{color}0D;">
      <div class="section-title" style="color:{accent};">Pasos inmediatos</div>
      {que_hacer_html}
    </div>''' if es_urgencia and f.get("que_hacer") else ""}

    <!-- CUÁNDO REGRESAR -->
    {alarmas_section}

    <!-- MENSAJE FINAL -->
    <div class="final-card">
      <div class="final-text">"{f['mensaje_final']}"</div>
    </div>

    <!-- FOOTER -->
    <div class="sitre-footer">
      <div class="sitre-brand">SITRE · Sistema de Triage Respiratorio</div>
      <div class="sitre-desc">
        Generado por motor determinístico basado en guías IDSA/OMS/AAP.<br>
        La decisión final corresponde al médico tratante.
      </div>
    </div>

  </div>
</body>
</html>"""
