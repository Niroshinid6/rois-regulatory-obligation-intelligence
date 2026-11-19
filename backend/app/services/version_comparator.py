import difflib
import json
from typing import Any, Dict, List


class VersionComparator:
    MATCH_REVIEW_THRESHOLD = 0.35
    ATTRIBUTE_MATCH_THRESHOLD = 0.55

    @staticmethod
    def _normalize_text(value: Any) -> str:
        return " ".join(str(value or "").lower().split())

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str) -> float:
        return difflib.SequenceMatcher(
            None,
            cls._normalize_text(text1),
            cls._normalize_text(text2),
        ).ratio()

    @classmethod
    def _normalize_attribute(cls, value: Any) -> str:
        if isinstance(value, (list, dict)):
            value = json.dumps(value, sort_keys=True, ensure_ascii=False)
        return cls._normalize_text(value)

    @classmethod
    def compare_documents(
        cls,
        base_obligations: List[Dict[str, Any]],
        target_obligations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        changes = []
        matched_base_ids = set()
        compared_attributes = (
            "required_action",
            "responsible_entity",
            "deadline",
            "conditions",
            "exceptions",
        )

        for target_obligation in target_obligations:
            available_base = [
                base_obligation
                for base_obligation in base_obligations
                if base_obligation["id"] not in matched_base_ids
            ]
            best_match = None
            best_similarity = 0.0

            for base_obligation in available_base:
                similarity = cls.calculate_similarity(
                    base_obligation["obligation_text"],
                    target_obligation["obligation_text"],
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = base_obligation

            if best_match is None or best_similarity < cls.MATCH_REVIEW_THRESHOLD:
                changes.append({
                    "change_type": "new",
                    "previous_obligation_id": None,
                    "current_obligation_id": target_obligation["id"],
                    "change_explanation": "No sufficiently supported match was found in the prior version.",
                    "diff_details": {
                        "current_text": target_obligation["obligation_text"],
                        "target_page": target_obligation["source_page"],
                    },
                    "human_verified": False,
                })
                continue

            matched_base_ids.add(best_match["id"])
            changed_attributes = {
                attribute: {
                    "previous": best_match.get(attribute),
                    "current": target_obligation.get(attribute),
                }
                for attribute in compared_attributes
                if cls._normalize_attribute(best_match.get(attribute))
                != cls._normalize_attribute(target_obligation.get(attribute))
            }
            exact_wording = (
                cls._normalize_text(best_match["obligation_text"])
                == cls._normalize_text(target_obligation["obligation_text"])
            )

            if exact_wording and not changed_attributes:
                change_type = "unchanged"
                explanation = (
                    "Normalized wording and extracted attributes match; "
                    "human verification is still required."
                )
            elif best_similarity >= cls.ATTRIBUTE_MATCH_THRESHOLD and changed_attributes:
                change_type = "modified"
                explanation = (
                    "A candidate match has changed wording or extracted attributes; "
                    "review the linked source evidence."
                )
            else:
                change_type = "requires_review"
                explanation = (
                    "A possible textual match was found, but equivalence or change "
                    "cannot be determined automatically."
                )

            changes.append({
                "change_type": change_type,
                "previous_obligation_id": best_match["id"],
                "current_obligation_id": target_obligation["id"],
                "change_explanation": explanation,
                "diff_details": {
                    "similarity": round(best_similarity, 2),
                    "previous_text": best_match["obligation_text"],
                    "current_text": target_obligation["obligation_text"],
                    "changed_attributes": changed_attributes,
                    "previous_page": best_match.get("source_page"),
                    "current_page": target_obligation.get("source_page"),
                },
                "human_verified": False,
            })

        for base_obligation in base_obligations:
            if base_obligation["id"] not in matched_base_ids:
                changes.append({
                    "change_type": "retired",
                    "previous_obligation_id": base_obligation["id"],
                    "current_obligation_id": None,
                    "change_explanation": (
                        "No supported match was found in the newer version; "
                        "human review is required before treating it as retired."
                    ),
                    "diff_details": {
                        "previous_text": base_obligation["obligation_text"],
                        "base_page": base_obligation.get("source_page"),
                    },
                    "human_verified": False,
                })

        return changes
