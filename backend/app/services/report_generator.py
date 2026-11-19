import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class ImpactReportGenerator:
    @classmethod
    def generate_document_impact_report(
        cls,
        document: Dict[str, Any],
        obligations: List[Dict[str, Any]],
        control_mappings: List[Dict[str, Any]],
        generated_by_user: Optional[str] = "ROIS System"
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive regulatory intelligence impact report from actual database records.
        """
        total_obligations = len(obligations)
        approved_count = sum(1 for o in obligations if o.get("review_status") == "approved")
        pending_count = sum(1 for o in obligations if o.get("review_status") == "pending")
        corrected_count = sum(1 for o in obligations if o.get("review_status") == "corrected")
        rejected_count = sum(1 for o in obligations if o.get("review_status") == "rejected")

        # Group by affected control category
        controls_summary = {}
        for cm in control_mappings:
            cat_name = cm.get("category_name", "Uncategorized")
            controls_summary[cat_name] = controls_summary.get(cat_name, 0) + 1

        # Group only entities explicitly extracted or verified on the obligation.
        entities_summary = {}
        for o in obligations:
            entity = o.get("responsible_entity")
            if entity:
                entities_summary[entity] = entities_summary.get(entity, 0) + 1

        # Include only actions supported by stored obligation records.
        action_items = []
        for o in obligations:
            if o.get("required_action"):
                action_items.append({
                    "obligation_code": o.get("obligation_code"),
                    "responsible_entity": o.get("responsible_entity"),
                    "action": o.get("required_action"),
                    "deadline": o.get("deadline"),
                    "page": o.get("source_page"),
                    "review_status": o.get("review_status")
                })

        report_title = f"Regulatory Impact Assessment: {document.get('title', '')}".strip()
        if document.get("circular_number"):
            report_title += f" ({document.get('circular_number')})"

        executive_summary = (
            f"This Regulatory Impact Assessment synthesizes {total_obligations} extracted compliance obligations "
            f"associated with {document.get('regulator') or 'the recorded authority'}. Of these, {approved_count} have been validated by compliance "
            f"reviewers, while {pending_count} remain in the active human verification queue. Primary impacted control "
            f"domains include {', '.join(list(controls_summary.keys())[:3]) if controls_summary else 'none recorded'}."
        )

        metrics = {
            "total_obligations": total_obligations,
            "approved_obligations": approved_count,
            "pending_reviews": pending_count,
            "corrected_obligations": corrected_count,
            "rejected_candidates": rejected_count,
            "impacted_control_count": len(controls_summary),
            "identified_entities_count": len(entities_summary)
        }

        report_data = {
            "title": report_title,
            "document_id": document.get("id"),
            "circular_number": document.get("circular_number"),
            "regulator": document.get("regulator"),
            "publication_date": document.get("publication_date"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": generated_by_user,
            "executive_summary": executive_summary,
            "metrics": metrics,
            "control_distribution": controls_summary,
            "entity_distribution": entities_summary,
            "high_priority_action_items": action_items[:10],
            "all_obligations": obligations,
            "legal_limitations_notice": (
                "Notice of Limitation: ROIS provides automated regulatory extraction and traceability assistance. "
                "AI-extracted obligations and suggested control mappings do not constitute formal legal counsel. "
                "Final compliance sign-off requires human verification by designated Compliance Officers."
            )
        }

        return report_data
