import re
from typing import List, Dict, Any

class ControlMapper:
    TAXONOMY_KEYWORDS = {
        "CDD-01": {
            "name": "Customer Due Diligence & AML/CFT",
            "keywords": [r'\b(?:aml|cft|kyc|customer\s+due\s+diligence|beneficial\s+owner|pep|suspicious\s+transaction|str|identity|money\s+laundering)\b'],
            "rationale": "Obligation requires verification of client identity, transaction scrutiny, or AML/CFT prevention controls."
        },
        "REP-01": {
            "name": "Regulatory Reporting & Disclosures",
            "keywords": [r'\b(?:submit|reporting|furnish|disclosure|quarterly\s+return|intimate|notify\s+the\s+authority|filing)\b'],
            "rationale": "Requires formal reporting, submission of statements, or official notification to IFSCA."
        },
        "GOV-01": {
            "name": "Corporate Governance & Oversight",
            "keywords": [r'\b(?:board|directors|compliance\s+officer|principal\s+officer|senior\s+management|governance|supervisory|oversight)\b'],
            "rationale": "Mandates senior management accountability, officer appointments, or board-level oversight."
        },
        "RISK-01": {
            "name": "Risk Management & Internal Controls",
            "keywords": [r'\b(?:risk|internal\s+audit|controls|assessment|framework|mitigat|exposure|limit)\b'],
            "rationale": "Directly impacts entity risk management frameworks, internal audit checks, or exposure limits."
        },
        "REC-01": {
            "name": "Record Keeping & Audit Trails",
            "keywords": [r'\b(?:record|maintain\s+records|retain|preserv|audit\s+trail|log|books\s+of\s+accounts)\b'],
            "rationale": "Obligates retention of compliance logs, customer records, or audit documentation."
        },
        "DATA-01": {
            "name": "Data Protection & Information Security",
            "keywords": [r'\b(?:cyber|information\s+security|data\s+protection|confidential|breach|incident|encryption)\b'],
            "rationale": "Relates to safeguard of electronic client data, incident reporting, and cybersecurity systems."
        },
        "OPS-01": {
            "name": "Operational Compliance & Outsourcing",
            "keywords": [r'\b(?:outsourc|vendor|third-party|operational|business\s+continuity|disaster\s+recovery)\b'],
            "rationale": "Governs service provider outsourcing, operational resiliency, or continuous business operations."
        }
    }

    @classmethod
    def suggest_controls_for_obligation(
        cls,
        obligation_text: str,
        available_categories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Suggests relevant compliance control mappings with transparent rationale.
        """
        suggestions = []
        text_lower = obligation_text.lower()

        cat_lookup = {c["code"]: c for c in available_categories}

        for code, rule in cls.TAXONOMY_KEYWORDS.items():
            if code not in cat_lookup:
                continue

            matched = False
            for pattern in rule["keywords"]:
                if re.search(pattern, text_lower):
                    matched = True
                    break

            if matched:
                suggestions.append({
                    "control_category_id": cat_lookup[code]["id"],
                    "category_code": code,
                    "category_name": cat_lookup[code]["name"],
                    "rationale": f"NLP Suggested: {rule['rationale']}",
                    "mapping_method": "nlp_suggested",
                    "review_status": "suggested"
                })

        # Fallback to general governance if no specific pattern matched
        if not suggestions and "GOV-01" in cat_lookup:
            suggestions.append({
                "control_category_id": cat_lookup["GOV-01"]["id"],
                "category_code": "GOV-01",
                "category_name": cat_lookup["GOV-01"]["name"],
                "rationale": "General compliance governance requirement; default control mapping pending human reviewer refinement.",
                "mapping_method": "nlp_suggested",
                "review_status": "suggested"
            })

        return suggestions
