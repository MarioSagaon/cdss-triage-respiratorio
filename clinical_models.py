from dataclasses import dataclass, field
from typing import Literal

# ═══════════════════════════════════════════════════════════
# MODELO 1 — FARINGITIS (Score McIsaac) — ya existía
# ═══════════════════════════════════════════════════════════
@dataclass
class PacienteIRA:
    """CDSS — Faringitis / IRA Alta. Score Centor modificado por McIsaac."""
    edad: int
    dias_evolucion: int
    frecuencia_respiratoria: int
    saturacion_oxigeno: float
    fiebre_mayor_38: bool
    exudado_amigdalino: bool
    adenopatia_cervical_anterior: bool
    conjuntivitis: bool
    mialgias_severas: bool
    disfonia: bool
    rinorrea: bool
    tos: bool
    exantema: bool
    nauseas_vomito: bool
    neumopatia_cronica: bool
    inmunocompromiso: bool
    diabetes_mellitus: bool = False  # NUEVO CAMPO
    
    def calcular_score_centor(self) -> int:
        score = 0
        if self.fiebre_mayor_38:            score += 1
        if not self.tos:                    score += 1
        if self.exudado_amigdalino:         score += 1
        if self.adenopatia_cervical_anterior: score += 1
        if 3 <= self.edad <= 14:            score += 1
        elif self.edad >= 45:               score -= 1
        return score

    def tiene_banderas_rojas(self) -> bool:
        return self.saturacion_oxigeno < 90.0 or self.frecuencia_respiratoria > 24

    def tiene_riesgo_elevado(self) -> bool:
        return self.neumopatia_cronica or self.inmunocompromiso or self.diabetes_mellitus

    def contar_signos_virales(self) -> int:
        return sum([
            self.conjuntivitis, self.mialgias_severas, self.disfonia,
            self.rinorrea, self.tos, self.exantema, self.nauseas_vomito
        ])


# ═══════════════════════════════════════════════════════════
# MODELO 2 — NEUMONÍA ADQUIRIDA EN COMUNIDAD (CURB-65)
# Validado: Lim et al. Thorax 2003. British Thoracic Society.
# Score 0-5. Mortalidad: 0-1=<3%, 2=9%, 3+=15-40%
# ═══════════════════════════════════════════════════════════
@dataclass
class PacienteNeumoniaCAP:
    """CDSS — Neumonía Adquirida en la Comunidad. Score CURB-65."""
    edad: int
    # Criterios CURB-65
    confusion_aguda: bool        # C — Confusión mental aguda (nuevo onset)
    urea_elevada: bool           # U — BUN >20 mg/dL o Urea >7 mmol/L
    frecuencia_respiratoria: int # R — FR ≥ 30 rpm
    hipotension: bool            # B — TAS <90 mmHg o TAD ≤60 mmHg
    # Edad ≥65 se calcula automáticamente del campo edad
    # Signos vitales adicionales para banderas rojas
    saturacion_oxigeno: float
    # Comorbilidades
    neumopatia_cronica: bool
    inmunocompromiso: bool
    # Hallazgos clínicos de soporte
    fiebre: bool
    tos_productiva: bool
    dolor_toracico: bool
    escalofrios: bool
    diabetes_mellitus: bool = False
    
    def calcular_curb65(self) -> int:
        """Score CURB-65: 1 punto por cada criterio presente."""
        score = 0
        if self.confusion_aguda:              score += 1  # C
        if self.urea_elevada:                 score += 1  # U
        if self.frecuencia_respiratoria >= 30: score += 1  # R
        if self.hipotension:                  score += 1  # B
        if self.edad >= 65:                   score += 1  # 65
        return score

    def tiene_banderas_rojas(self) -> bool:
        return self.saturacion_oxigeno < 90.0 or self.frecuencia_respiratoria > 30

    def tiene_riesgo_elevado(self) -> bool:
        return self.neumopatia_cronica or self.inmunocompromiso or self.diabetes_mellitus

    def nivel_severidad(self) -> str:
        s = self.calcular_curb65()
        if s <= 1: return "LEVE"
        if s == 2: return "MODERADA"
        return "GRAVE"


# ═══════════════════════════════════════════════════════════
# MODELO 3 — OTITIS MEDIA AGUDA (Criterios AAP/SEIP 2023)
# Confirmada: 3 criterios. Probable: 2 criterios.
# Ref: AAP 2013, Consenso SEIP 2023 (An Pediatr 98:362-72)
# ═══════════════════════════════════════════════════════════
@dataclass
class PacienteOMA:
    """CDSS — Otitis Media Aguda. Criterios diagnósticos AAP/SEIP."""
    edad: int
    dias_evolucion: int
    # Criterio 1: Inicio agudo (< 48h de síntomas)
    inicio_agudo: bool
    # Criterio 2: Signos de ocupación del oído medio
    abombamiento_timpanico: bool  # Principal
    otorrea_reciente: bool        # O perforación con otorrea
    hipoacusia: bool              # Pérdida auditiva
    # Criterio 3: Signos de inflamación
    otalgia: bool                 # Dolor de oído (o equivalente: irritabilidad en niños)
    fiebre_mayor_38: bool
    hiperemia_timpanica: bool     # Enrojecimiento intenso del tímpano
    # Factores de gravedad
    fiebre_mayor_39: bool         # Criterio de OMA grave
    otalgia_intensa: bool         # EVA > 7/10
    bilateral: bool               # OMA bilateral
    # Comorbilidades
    inmunocompromiso: bool
    episodios_previos: int        # Número de episodios en últimos 6 meses
    diabetes_mellitus: bool = False

    def criterios_diagnosticos(self) -> int:
        """
        Cuenta los 3 criterios diagnósticos.
        C1: Inicio agudo
        C2: Signos de ocupación (abombamiento, otorrea o hipoacusia)
        C3: Signos inflamatorios (otalgia, fiebre o hiperemia)
        """
        c1 = 1 if self.inicio_agudo else 0
        c2 = 1 if (self.abombamiento_timpanico or self.otorrea_reciente or self.hipoacusia) else 0
        c3 = 1 if (self.otalgia or self.fiebre_mayor_38 or self.hiperemia_timpanica) else 0
        return c1 + c2 + c3

    def es_grave(self) -> bool:
        """OMA grave: fiebre >39°C, otalgia intensa o afectación bilateral."""
        return self.fiebre_mayor_39 or self.otalgia_intensa or self.bilateral

    def es_recurrente(self) -> bool:
        """OMA recurrente: ≥3 episodios en 6 meses."""
        return self.episodios_previos >= 3
    
    def tiene_riesgo_elevado(self) -> bool:
        return self.inmunocompromiso or self.edad < 6 or self.es_recurrente() or self.diabetes_mellitus

    def nivel_diagnostico(self) -> str:
        c = self.criterios_diagnosticos()
        if c == 3: return "CONFIRMADA"
        if c == 2: return "PROBABLE"
        return "NO_CUMPLE"


# ═══════════════════════════════════════════════════════════
# MODELO 4 — SINUSITIS BACTERIANA AGUDA (IDSA 2012 + NICE)
# Diferenciación viral vs bacteriana por patrón temporal.
# Ref: Chow et al. Clin Infect Dis 2012;54:e72-e112
# ═══════════════════════════════════════════════════════════
@dataclass
class PacienteSinusitis:
    """CDSS — Rinosinusitis Aguda. Criterios IDSA/NICE."""
    edad: int
    dias_evolucion: int  # Clave para diferenciar viral vs bacteriana
    # Síntomas cardinales
    congestion_nasal: bool
    rinorrea_purulenta: bool      # Secreción mucopurulenta o purulenta
    dolor_presion_facial: bool    # Dolor/presión/pesadez facial
    hiposmia_anosmia: bool        # Pérdida parcial/total del olfato
    # Criterios de etiología bacteriana (IDSA)
    empeoramiento_tras_mejoria: bool  # "Double sickening" — empeora tras 5-7 días de mejoría
    fiebre_mayor_38: bool
    dolor_facial_unilateral: bool     # Más sugestivo de bacteriano
    # Signos de severidad
    fiebre_mayor_39: bool
    edema_periorbitario: bool         # Bandera roja — posible extensión orbitaria
    rigidez_nucal: bool               # Bandera roja — posible extensión intracraneal
    cefalea_intensa: bool
    # Comorbilidades
    inmunocompromiso: bool
    asma_rinitis_alergica: bool
    diabetes_mellitus: bool = False

    def tiene_banderas_rojas(self) -> bool:
        """Signos de complicación — derivación urgente."""
        return self.edema_periorbitario or self.rigidez_nucal

    def patron_bacteriano(self) -> bool:
        """
        IDSA: Sinusitis bacteriana si cumple UNO de:
        1. Síntomas ≥10 días sin mejoría
        2. Síntomas severos ≥3-4 días (fiebre ≥39°C + dolor facial unilateral)
        3. "Double sickening": empeora después de mejora inicial 5-7 días
        """
        criterio1 = self.dias_evolucion >= 10
        criterio2 = self.fiebre_mayor_39 and self.dolor_facial_unilateral
        criterio3 = self.empeoramiento_tras_mejoria
        return criterio1 or criterio2 or criterio3

    def severidad(self) -> str:
        if self.tiene_banderas_rojas(): return "COMPLICADA"
        if self.fiebre_mayor_39 or self.cefalea_intensa: return "GRAVE"
        if self.patron_bacteriano(): return "BACTERIANA"
        return "VIRAL"