# 🏥 Triage Respiratorio Inteligente (CDSS)

Un Sistema de Soporte a las Decisiones Clínicas (CDSS) desarrollado en Python para optimizar el triaje de Infecciones Respiratorias Agudas (IRA) y combatir la resistencia antimicrobiana en el primer nivel de atención.

## 🎯 El Problema
La prescripción innecesaria de antibióticos para infecciones respiratorias de etiología viral es uno de los principales motores de la crisis global de resistencia a los antimicrobianos. Este algoritmo busca estandarizar la evaluación inicial del paciente para reducir prescripciones empíricas injustificadas.

## ⚙️ Lógica Médica del Algoritmo
El motor de inferencia clínica evalúa al paciente en tres fases:
1. **Filtro de Urgencias (Banderas Rojas):** Identificación inmediata de hipoxia (<90%) o taquipnea para derivación a segundo nivel.
2. **Evaluación de Riesgo:** Identificación de comorbilidades (neumopatía crónica, inmunocompromiso) que invalidan el manejo conservador.
3. **Cálculo de Probabilidad Etiológica:**
   - **Sospecha Bacteriana:** Implementación del **Score de Centor modificado por McIsaac** (evaluando fiebre, tos, exudado, adenopatía y edad).
   - **Sospecha Viral:** Cuantificación de signos fuertemente asociados a etiología viral (conjuntivitis, exantema, mialgias severas, disfonía, síntomas gastrointestinales).

## 💻 Arquitectura del Código
El proyecto sigue el principio de separación de responsabilidades:
* `clinical_models.py`: Define las estructuras de datos del paciente y los métodos de cálculo de scores.
* `decision_engine.py`: Contiene el árbol de decisiones y las reglas heurísticas.
* `main.py`: Punto de entrada para la simulación de casos clínicos.

  ---

# 🏥 Intelligent Respiratory Triage (CDSS)

A Clinical Decision Support System (CDSS) developed in Python to optimize the triage of Acute Respiratory Infections (ARI) and combat antimicrobial resistance in primary care.

## 🎯 The Problem
The unnecessary prescription of antibiotics for respiratory infections of viral etiology is one of the main drivers of the global antimicrobial resistance crisis. This algorithm seeks to standardize the initial patient evaluation to reduce unjustified empirical prescriptions.

## ⚙️ Medical Logic of the Algorithm
The clinical inference engine evaluates the patient in three phases:
1. **Emergency Filter (Red Flags):** Immediate identification of hypoxia (<90%) or tachypnea for referral to secondary care.
2. **Risk Assessment:** Identification of comorbidities (chronic pneumopathy, immunocompromise) that invalidate conservative management.
3. **Etiological Probability Calculation:**
   - **Bacterial Suspicion:** Implementation of the **Centor Score modified by McIsaac** (evaluating fever, absence of cough, exudate, adenopathy, and age).
   - **Viral Suspicion:** Quantification of signs strongly associated with viral etiology (conjunctivitis, rash, severe myalgias, dysphonia, gastrointestinal symptoms).

## 💻 Code Architecture
The project follows the separation of concerns principle:
* `clinical_models.py`: Defines patient data structures and score calculation methods.
* `decision_engine.py`: Contains the decision tree and heuristic rules.
* `main.py`: Entry point for clinical case simulation.
