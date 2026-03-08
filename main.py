from clinical_models import PacienteIRA
from decision_engine import evaluar_paciente

def correr_simulacion():
    print("--- 🏥 INICIANDO SISTEMA DE TRIAJE RESPIRATORIO ---")

    # Paciente 1: Joven con cuadro viral clásico
    print("👨‍⚕️ Evaluando Paciente 1 (Caso Viral Clásico):")
    paciente_1 = PacienteIRA(
        edad=22,
        dias_evolucion=4,
        frecuencia_respiratoria=18,
        saturacion_oxigeno=98.0,
        fiebre_mayor_38=False,
        exudado_amigdalino=False,
        adenopatia_cervical_anterior=False,
        conjuntivitis=False,
        mialgias_severas=True,
        disfonia=True,
        rinorrea=True,
        # --- NUEVAS VARIABLES ---
        tos=True,             # SÍ tiene tos
        exantema=False,
        nauseas_vomito=False,
        # ------------------------
        neumopatia_cronica=False,
        inmunocompromiso=False
    )
    
    diagnostico_1 = evaluar_paciente(paciente_1)
    print(diagnostico_1)

    print("\n👨‍⚕️ Evaluando Paciente 2 (Tu Caso Clínico Estreptocócico):")
    paciente_2 = PacienteIRA(
        edad=27,
        dias_evolucion=4,
        frecuencia_respiratoria=20,
        saturacion_oxigeno=95.0,
        fiebre_mayor_38=True,
        exudado_amigdalino=True,
        adenopatia_cervical_anterior=True,
        conjuntivitis=False,
        mialgias_severas=False,
        disfonia=False,
        rinorrea=False,
        # --- NUEVAS VARIABLES ---
        tos=False,            # NO tiene tos (clásico de bacteria)
        exantema=False,
        nauseas_vomito=False,
        # ------------------------
        neumopatia_cronica=False,
        inmunocompromiso=False
    )
    
    diagnostico_2 = evaluar_paciente(paciente_2)
    print(diagnostico_2)

# Este bloque le dice a Python que este archivo es el principal para ejecutarse
if __name__ == "__main__":
    correr_simulacion()