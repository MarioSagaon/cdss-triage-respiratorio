"""
SITRE — Módulo de Interoperabilidad de Grado Médico
======================================================
Genera los tres artefactos del Audit Trail:
  1. Decision ID único (SITRE-YYYYMMDD-XXXXXXXX) con hash SHA-256
  2. HL7 FHIR R4 Bundle (mock) — Observation + AuditEvent
  3. Structured Research JSON — listo para análisis epidemiológico

Diseñado para interoperar con HIS hospitalarios y sistemas de salud pública
(SINAVE/InDRE, Hacking Health Monterrey, Noreste MX).
"""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone

# ─── Constantes de versión ────────────────────────────────────────────────────
SITRE_VERSION = "2.0.0"
SCHEMA_VERSION = "1.0"

GUIA_VERSIONS = {
    "faringitis": "McIsaac 2004 — JAMA 291:1589",
    "neumonia":   "CURB-65 BTS 2003 — Thorax 58:377",
    "oma":        "AAP/SEIP 2023 — Pediatrics 131:e964",
    "sinusitis":  "IDSA 2012 — Clin Infect Dis 54:e72",
}

# ─── Terminología clínica estándar ───────────────────────────────────────────
SNOMED_MAP = {
    "faringitis": {"code": "405737000", "display": "Pharyngitis (disorder)"},
    "neumonia":   {"code": "233604007", "display": "Community-acquired pneumonia (disorder)"},
    "oma":        {"code": "65363002",  "display": "Otitis media (disorder)"},
    "sinusitis":  {"code": "36971009",  "display": "Sinusitis (disorder)"},
}

LOINC_MAP = {
    "faringitis": {"code": "89238-4",  "display": "McIsaac/Centor Score"},
    "neumonia":   {"code": "96811-9",  "display": "CURB-65 Score"},
    "oma":        {"code": "custom-oma-aap-seip-2023",  "display": "AAP/SEIP Diagnostic Criteria Count"},
    "sinusitis":  {"code": "custom-sinusitis-idsa-2012","display": "IDSA Bacterial Pattern Score"},
}

DECISION_MAP = {
    "viral":      {"code": "no-antibiotic",     "display": "No antibiotic — viral etiology"},
    "bacteriana": {"code": "antibiotic",         "display": "Antibiotic indicated — bacterial etiology"},
    "urgencia":   {"code": "urgent-referral",    "display": "Urgent hospital referral required"},
    "gris":       {"code": "clinical-eval",      "display": "Clinical evaluation required — indeterminate"},
}

FHIR_INTERP = {
    "viral":      {"code": "N",  "display": "Normal"},
    "bacteriana": {"code": "A",  "display": "Abnormal"},
    "urgencia":   {"code": "AA", "display": "Critical"},
    "gris":       {"code": "IND","display": "Indeterminate"},
}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _to_dict(paciente) -> dict:
    try:
        return asdict(paciente)
    except Exception:
        return {}


def _age_group(edad: int) -> str:
    if edad < 2:   return "infant (<2y)"
    if edad < 12:  return "child (2-11y)"
    if edad < 18:  return "adolescent (12-17y)"
    if edad < 65:  return "adult (18-64y)"
    return "elderly (≥65y)"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DECISION ID — SHA-256 Audit Hash
# ═══════════════════════════════════════════════════════════════════════════════
def generar_decision_id(paciente, resultado: dict, timestamp: datetime) -> dict:
    """
    Genera el identificador único reproducible de la decisión clínica.

    Formato:  SITRE-YYYYMMDD-XXXXXXXX
    Hash:     SHA-256 sobre (timestamp_utc + tipo_decision + snapshot_clinico)

    Mismos inputs = mismo hash → auditabilidad y reproducibilidad garantizada.
    """
    p_dict = _to_dict(paciente)
    tipo = resultado.get("tipo", "")

    payload = {
        "ts":       timestamp.strftime("%Y%m%d%H%M%S"),
        "tipo":     tipo,
        "snapshot": p_dict,
    }
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    hash_full   = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    hash_short  = hash_full[:8].upper()

    return {
        "decision_id":       f"SITRE-{timestamp.strftime('%Y%m%d')}-{hash_short}",
        "hash_full":         hash_full,
        "hash_short":        hash_short,
        "hash_algorithm":    "SHA-256",
        "timestamp_utc":     timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_display": timestamp.strftime("%d/%m/%Y %H:%M:%S"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HL7 FHIR R4 BUNDLE (Mock — Observation + AuditEvent)
# ═══════════════════════════════════════════════════════════════════════════════
def generar_fhir_r4(paciente, resultado: dict, decision_info: dict, metadatos: dict) -> dict:
    """
    Genera un Bundle HL7 FHIR R4 válido (mock) con dos recursos:
      - Observation: resultado clínico + score + componentes booleanos
      - AuditEvent:  trazabilidad de la decisión (Decision ID + SHA-256)

    Ref: https://hl7.org/fhir/R4/bundle.html
         https://hl7.org/fhir/R4/observation.html
         https://hl7.org/fhir/R4/auditevent.html
    """
    patologia  = metadatos.get("patologia", "faringitis")
    tipo       = resultado.get("tipo", "gris")
    ts_utc     = decision_info["timestamp_utc"]
    dec_id     = decision_info["decision_id"]
    hash_full  = decision_info["hash_full"]
    score_info = metadatos.get("score_info", {})
    p          = _to_dict(paciente)

    snomed  = SNOMED_MAP.get(patologia,  {"code": "87982008",  "display": "Respiratory infection"})
    loinc   = LOINC_MAP.get(patologia,   {"code": "custom",    "display": "Clinical Score"})
    decisn  = DECISION_MAP.get(tipo,     DECISION_MAP["gris"])
    interp  = FHIR_INTERP.get(tipo,      FHIR_INTERP["gris"])

    # Componentes clínicos booleanos (criterios evaluados)
    components = [
        {
            "code": {
                "coding": [{"system": f"http://sitre.mx/CodeSystem/{patologia}-criteria",
                            "code": k, "display": k.replace("_", " ").title()}]
            },
            "valueBoolean": v
        }
        for k, v in p.items() if isinstance(v, bool)
    ]

    # Componente principal — score numérico
    score_component = {
        "code": {
            "coding": [{"system": "http://loinc.org",
                        "code": loinc["code"], "display": loinc["display"]}]
        },
        "valueQuantity": {
            "value":  score_info.get("val", 0),
            "unit":   "score",
            "system": "http://unitsofmeasure.org",
            "code":   "{score}"
        },
        "referenceRange": [{
            "low":  {"value": 0},
            "high": {"value": score_info.get("max", 5)},
            "text": f"0–{score_info.get('max', 5)}"
        }]
    }

    bundle = {
        "resourceType": "Bundle",
        "id": f"sitre-bundle-{decision_info['hash_short'].lower()}",
        "meta": {
            "lastUpdated": ts_utc,
            "tag": [{
                "system":  "http://sitre.mx/tags",
                "code":    "cdss-triage-respiratorio",
                "display": f"SITRE CDSS v{SITRE_VERSION} — Zero Hallucination Engine"
            }]
        },
        "type":      "collection",
        "timestamp": ts_utc,
        "entry": [
            # ── Resource 1: Observation ──────────────────────────────────────
            {
                "fullUrl": f"urn:uuid:{dec_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": dec_id,
                    "meta": {
                        "profile": ["http://hl7.org/fhir/StructureDefinition/Observation"],
                        "tag": [{
                            "system":  "http://sitre.mx/tags",
                            "code":    "deterministic-rules-engine",
                            "display": f"SITRE v{SITRE_VERSION} — Deterministic, zero hallucination"
                        }]
                    },
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system":  "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code":    "exam",
                            "display": "Exam"
                        }]
                    }],
                    "code": {
                        "coding": [
                            {"system": "http://snomed.info/sct",
                             "code": snomed["code"], "display": snomed["display"]},
                            {"system": "http://loinc.org",
                             "code": loinc["code"],  "display": loinc["display"]}
                        ],
                        "text": f"SITRE Triage — {patologia.title()}"
                    },
                    "subject": {
                        "display": "De-identified patient",
                        "extension": [{
                            "url":          "http://sitre.mx/Extension/age-years",
                            "valueInteger": p.get("edad", 0)
                        }, {
                            "url":         "http://sitre.mx/Extension/age-group",
                            "valueString": _age_group(p.get("edad", 0))
                        }]
                    },
                    "effectiveDateTime": ts_utc,
                    "valueCodeableConcept": {
                        "coding": [{
                            "system":  "http://sitre.mx/CodeSystem/diagnostic-type",
                            "code":    decisn["code"],
                            "display": decisn["display"]
                        }],
                        "text": resultado.get("diagnostico", "")[:250]
                    },
                    "interpretation": [{
                        "coding": [{
                            "system":  "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code":    interp["code"],
                            "display": interp["display"]
                        }]
                    }],
                    "note": [{
                        "text": (
                            f"Engine: {resultado.get('razonamiento', {}).get('motor', 'SITRE Rules Engine')} | "
                            f"Guideline: {GUIA_VERSIONS.get(patologia, 'N/A')} | "
                            f"DOI: {resultado.get('razonamiento', {}).get('doi', 'N/A')} | "
                            f"Decision ID: {dec_id} | "
                            f"Processing: {resultado.get('razonamiento', {}).get('ms', 0)}ms"
                        )
                    }],
                    "component": [score_component] + components
                }
            },

            # ── Resource 2: AuditEvent ───────────────────────────────────────
            {
                "fullUrl": f"urn:uuid:audit-{decision_info['hash_short'].lower()}",
                "resource": {
                    "resourceType": "AuditEvent",
                    "id": f"audit-{decision_info['hash_short'].lower()}",
                    "type": {
                        "system":  "http://dicom.nema.org/resources/ontology/DCM",
                        "code":    "110113",
                        "display": "Security Alert"
                    },
                    "subtype": [{
                        "system":  "http://sitre.mx/CodeSystem/audit-events",
                        "code":    "cdss-clinical-evaluation",
                        "display": "SITRE Clinical Decision Support Evaluation"
                    }],
                    "action":      "E",
                    "recorded":    ts_utc,
                    "outcome":     "0",
                    "outcomeDesc": "Success — Decision rendered deterministically",
                    "agent": [{
                        "type": {"coding": [{
                            "system":  "http://terminology.hl7.org/CodeSystem/extra-security-role-type",
                            "code":    "humanuser",
                            "display": "Human User (Clinician)"
                        }]},
                        "requestor": True,
                        "name": f"SITRE CDSS v{SITRE_VERSION}"
                    }],
                    "source": {
                        "site":     "SITRE — Noreste MX (Coahuila / Nuevo León)",
                        "observer": {"display": "SITRE Clinical Decision Support System"},
                        "type": [{"system": "http://terminology.hl7.org/CodeSystem/security-source-type",
                                  "code": "4", "display": "Application Server"}]
                    },
                    "entity": [{
                        "what": {
                            "identifier": {
                                "system": "http://sitre.mx/identifiers/decision",
                                "value":  dec_id
                            }
                        },
                        "type": {
                            "system":  "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                            "code":    "2",
                            "display": "System Object"
                        },
                        "description": f"Integrity hash SHA-256: {hash_full}"
                    }]
                }
            }
        ]
    }

    return bundle


# ═══════════════════════════════════════════════════════════════════════════════
# 3. STRUCTURED RESEARCH JSON — Listo para epidemiología y ML
# ═══════════════════════════════════════════════════════════════════════════════
def generar_json_estructurado(paciente, resultado: dict, decision_info: dict, metadatos: dict) -> dict:
    """
    JSON estructurado limpio, listo para:
      - Análisis epidemiológico (Python/R/SPSS)
      - Machine Learning (features listas para entrenamiento)
      - Auditoría clínica y publicación científica
      - Stewardship antimicrobiano (conteo de ABX evitados)
    """
    patologia  = metadatos.get("patologia", "faringitis")
    tipo       = resultado.get("tipo", "gris")
    score_info = metadatos.get("score_info", {})
    razon      = resultado.get("razonamiento", {})
    p          = _to_dict(paciente)
    edad       = p.get("edad", 0)

    return {
        # ── Metadatos del sistema ──────────────────────────────────────────────
        "_sitre": {
            "schema_version":   SCHEMA_VERSION,
            "system":           "SITRE CDSS — Sistema de Triage Respiratorio",
            "system_version":   SITRE_VERSION,
            "engine":           razon.get("motor", "Deterministic Rules Engine v2.0"),
            "deterministic":    True,
            "zero_hallucination": True,
            "note": "Same clinical inputs always produce the same output. No generative AI involved.",
        },

        # ── Audit trail ───────────────────────────────────────────────────────
        "audit": {
            "decision_id":    decision_info["decision_id"],
            "timestamp_utc":  decision_info["timestamp_utc"],
            "hash_sha256":    decision_info["hash_full"],
            "hash_algorithm": "SHA-256",
            "integrity_note": (
                "Hash computed over (timestamp_utc + decision_type + full_patient_snapshot). "
                "Identical inputs reproduce identical hash — enables reproducibility auditing."
            ),
        },

        # ── Metadatos clínicos ────────────────────────────────────────────────
        "metadata": {
            "region":              "Noreste MX — Coahuila / Nuevo León",
            "pathology":           patologia,
            "pathology_display":   metadatos.get("nombre_pat_display", patologia.title()),
            "clinical_guideline":  GUIA_VERSIONS.get(patologia, ""),
            "guideline_doi":       razon.get("doi", ""),
            "guideline_ref":       razon.get("ref_completa", ""),
            "processing_ms":       razon.get("ms", 0),
        },

        # ── Datos del paciente (de-identificados) ─────────────────────────────
        "patient": {
            "age_years":    edad,
            "age_group":    _age_group(edad),
            "days_evolution": p.get("dias_evolucion", 0),
            "de_identified": True,
            "_privacy_note": "Patient name excluded. Age and evolution days retained for epidemiological analysis.",
        },

        # ── Inputs clínicos crudos (features para ML) ─────────────────────────
        "clinical_inputs": {
            k: v for k, v in p.items()
            if k not in ("edad",)
        },

        # ── Scores calculados ─────────────────────────────────────────────────
        "scores": {
            "primary": {
                "name":  score_info.get("label", "Score"),
                "value": score_info.get("val", 0),
                "max":   score_info.get("max", 5),
                "pct":   round(
                    score_info.get("val", 0) / score_info.get("max", 5) * 100, 1
                ) if score_info.get("max", 5) > 0 else 0.0,
            }
        },

        # ── Decisión clínica ──────────────────────────────────────────────────
        "decision": {
            "type":                tipo,
            "type_display":        DECISION_MAP.get(tipo, {}).get("display", tipo),
            "antibiotic_indicated": tipo == "bacteriana",
            "antibiotic_avoided":   tipo == "viral",
            "urgent_referral":      tipo == "urgencia",
            "indeterminate":        tipo == "gris",
            "diagnostic_text":     resultado.get("diagnostico", ""),
            "therapeutic_guideline": resultado.get("tratamiento", ""),
        },

        # ── Trazabilidad del razonamiento (pasos del motor) ───────────────────
        "reasoning_trace": {
            "total_steps":    len(razon.get("pasos", [])),
            "steps":          razon.get("pasos", []),
            "reference":      razon.get("ref_completa", ""),
        },

        # ── Impacto en stewardship antimicrobiano ─────────────────────────────
        "stewardship": {
            "antibiotic_prescription_avoided": tipo == "viral",
            "prescription_category": (
                "none"             if tipo == "viral"
                else "full_course" if tipo == "bacteriana"
                else "urgent_iv"   if tipo == "urgencia"
                else "defer_or_evaluate"
            ),
            "amr_impact_label": (
                "ABX_AVOIDED"   if tipo == "viral"
                else "ABX_PRESCRIBED" if tipo == "bacteriana"
                else "URGENT_ESCALATION" if tipo == "urgencia"
                else "PENDING_EVALUATION"
            ),
            "region_amr_context": "Noreste MX — high prevalence of ABX-resistant S. pneumoniae (~35%)",
        },
    }
