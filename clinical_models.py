from dataclasses import dataclass

@dataclass
class PacienteIRA:
    """
    Estructura de datos central para el CDSS de Infecciones Respiratorias.
    Versión 2.0: Incluye banderas rojas y triage viral.
    """
    # 1. Demográficos y Evolución
    edad: int
    dias_evolucion: int
    
    # 2. Signos Vitales (Banderas Rojas)
    frecuencia_respiratoria: int
    saturacion_oxigeno: float  # Usamos float para permitir decimales, ej. 92.5
    
    # 3. Criterios de Centor/McIsaac (Sospecha Bacteriana)
    fiebre_mayor_38: bool
    exudado_amigdalino: bool
    adenopatia_cervical_anterior: bool
    
    # 4. Signos Fuertemente Virales
    conjuntivitis: bool
    mialgias_severas: bool
    disfonia: bool
    rinorrea: bool
    tos: bool 
    exantema: bool
    nauseas_vomito: bool

    # 5. Antecedentes de Riesgo
    neumopatia_cronica: bool  # Ej. Asma, EPOC, Fibrosis
    inmunocompromiso: bool    # Ej. Diabetes descontrolada, VIH, esteroides crónicos



    def calcular_score_centor(self) -> int:
        """Calcula el Score de Centor modificado por McIsaac."""
        score = 0
        if self.fiebre_mayor_38: score += 1
        if not self.tos: score += 1
        if self.exudado_amigdalino: score += 1
        if self.adenopatia_cervical_anterior: score += 1
            
        if 3 <= self.edad <= 14:
            score += 1
        elif self.edad >= 45:
            score -= 1
            
        return score

    def tiene_banderas_rojas(self) -> bool:
        """
        Evalúa si el paciente requiere derivación a urgencias.
        Retorna True si hay taquipnea o hipoxia.
        """
        return self.saturacion_oxigeno < 90.0 or self.frecuencia_respiratoria > 24

    def tiene_riesgo_elevado(self) -> bool:
        """
        Evalúa si el paciente tiene comorbilidades que invalidan 
        el manejo conservador estándar de una IRA.
        """
        return self.neumopatia_cronica or self.inmunocompromiso



    def contar_signos_virales(self) -> int:
        """
        Cuantifica el peso de la etiología viral en el cuadro clínico.
        """
        # En Python, True vale 1 y False vale 0. 
        # Podemos sumarlos directamente dentro de una lista [ ]
        signos = [
            self.conjuntivitis, 
            self.mialgias_severas, 
            self.disfonia, 
            self.rinorrea, 
            self.tos, # La simple presencia de tos es fuertemente sugestiva de virus
            self.exantema,
            self.nauseas_vomito
        ]
        return sum(signos)