import re
from typing import List, Dict, Any, Optional

class ObligationExtractor:
    # Normative modals indicating binding regulatory requirements
    MODAL_PATTERNS = [
        (r'\bshall\s+(?:not\s+)?([a-zA-Z0-9\s\(\)\/\,\'\"\-%]+?)(?=[.;]|\bprovided\b|\bsubject to\b|\bwithin\b|\bsave as\b|$)', 0.95),
        (r'\bmust\s+(?:not\s+)?([a-zA-Z0-9\s\(\)\/\,\'\"\-%]+?)(?=[.;]|\bprovided\b|\bsubject to\b|\bwithin\b|\bsave as\b|$)', 0.95),
        (r'\bis\s+required\s+to\s+([a-zA-Z0-9\s\(\)\/\,\'\"\-%]+?)(?=[.;]|\bprovided\b|\bsubject to\b|\bwithin\b|\bsave as\b|$)', 0.90),
        (r'\bare\s+required\s+to\s+([a-zA-Z0-9\s\(\)\/\,\'\"\-%]+?)(?=[.;]|\bprovided\b|\bsubject to\b|\bwithin\b|\bsave as\b|$)', 0.90),
        (r'\bprohibited\s+from\s+([a-zA-Z0-9\s\(\)\/\,\'\"\-%]+?)(?=[.;]|\bprovided\b|\bsubject to\b|\bunless\b|$)', 0.90),
        (r'\bis\s+mandated\s+to\s+([a-zA-Z0-9\s\(\)\/\,\'\"\-%]+?)(?=[.;]|\bprovided\b|\bsubject to\b|\bwithin\b|$)', 0.90)
    ]

    # IFSCA and Regulated Entities
    ENTITY_PATTERNS = [
        r'\b(?:IFSC\s+Banking\s+Units?|IBUs?)\b',
        r'\b(?:Finance\s+Companies?|FCs?)\b',
        r'\b(?:Fund\s+Management\s+Entities?|FMEs?)\b',
        r'\b(?:Authorised\s+Persons?)\b',
        r'\b(?:Registered\s+Intermediar(?:y|ies))\b',
        r'\b(?:Broker\s+Dealers?)\b',
        r'\b(?:Recognised\s+Stock\s+Exchanges?)\b',
        r'\b(?:Recognised\s+Clearing\s+Corporations?)\b',
        r'\b(?:Depositories?|Depository\s+Participants?)\b',
        r'\b(?:Regulated\s+Entities?|REs?)\b',
        r'\b(?:Capital\s+Market\s+Intermediar(?:y|ies))\b',
        r'\b(?:Board\s+of\s+Directors?)\b',
        r'\b(?:Compliance\s+Officer)\b',
        r'\b(?:Principal\s+Officer)\b',
        r'\b(?:Internal\s+Auditor)\b',
        r'\b(?:Management)\b',
        r'\b(?:Custodian(?:s)?)\b'
    ]

    # Deadlines and temporal compliance milestones
    DEADLINE_PATTERNS = [
        r'\b(?:within\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|thirty|forty-five|sixty|ninety)\s+(?:business\s+|working\s+)?(?:days?|weeks?|months?|hours?)(?:\s+of\s+[a-zA-Z0-9\s]+)?)\b',
        r'\b(?:on\s+or\s+before\s+[0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+(?:\s+[0-9]{4})?)\b',
        r'\b(?:by\s+[0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+(?:\s+[0-9]{4})?)\b',
        r'\b(?:not\s+later\s+than\s+[0-9]{1,2}\s+(?:days?|hours?|months?))\b',
        r'\b(?:quarterly\s+within\s+\d+\s+days\s+of\s+(?:the\s+)?end\s+of\s+(?:each\s+)?quarter)\b',
        r'\b(?:minimum\s+period\s+of\s+\d+\s+years?)\b',
        r'\b(?:prior\s+to\s+commencement\s+of\s+operations?)\b',
        r'\b(?:immediately|forthwith|promptly)\b'
    ]

    # Conditions & Exceptions
    CONDITION_PREFIXES = [
        r'provided\s+that',
        r'subject\s+to',
        r'in\s+the\s+event\s+that',
        r'where\s+the',
        r'if\s+the'
    ]

    EXCEPTION_PREFIXES = [
        r'except\s+where',
        r'unless\s+otherwise\s+approved',
        r'unless\s+specifically\s+permitted',
        r'save\s+as\s+provided',
        r'without\s+prejudice\s+to'
    ]

    @classmethod
    def segment_into_candidate_sentences(cls, raw_text: str) -> List[Dict[str, Any]]:
        """
        Cleans text and segments into discrete clauses/sentences with precise char offsets.
        """
        normalized_chars = []
        source_offsets = []
        previous_was_whitespace = False
        for source_offset, character in enumerate(raw_text):
            if character.isspace():
                if normalized_chars and not previous_was_whitespace:
                    normalized_chars.append(" ")
                    source_offsets.append(source_offset)
                previous_was_whitespace = True
                continue
            normalized_chars.append(character)
            source_offsets.append(source_offset)
            previous_was_whitespace = False

        normalized_text = "".join(normalized_chars)
        candidates = []
        for match in re.finditer(r"\S.*?(?:[.!?](?=\s|$)|$)", normalized_text):
            start, end = match.span()
            while end > start and normalized_text[end - 1].isspace():
                end -= 1

            sentence = normalized_text[start:end]
            if len(sentence) < 25:
                continue

            candidates.append({
                "text": sentence,
                "char_start": source_offsets[start],
                "char_end": source_offsets[end - 1] + 1
            })

        return candidates

    @classmethod
    def extract_from_pages(cls, pages: List[Dict[str, Any]], circular_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts structured candidate obligations across document pages.
        """
        obligations = []
        obl_counter = 1

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            word_boxes = page.get("bounding_boxes", [])

            sentences = cls.segment_into_candidate_sentences(page_text)

            for item in sentences:
                sentence = item["text"]
                char_start = item["char_start"]
                char_end = item["char_end"]

                # Check for normative modals
                is_mandatory = False
                matched_action = ""
                modal_confidence = 0.0

                for pattern, conf in cls.MODAL_PATTERNS:
                    m = re.search(pattern, sentence, re.IGNORECASE)
                    if m:
                        is_mandatory = True
                        modal_confidence = conf
                        # Extract the required action
                        action_chunk = sentence[m.start():].split(".")[0].strip()
                        matched_action = action_chunk
                        break

                if not is_mandatory:
                    continue

                # Extract Responsible Entity
                responsible_entity = None
                for ep in cls.ENTITY_PATTERNS:
                    em = re.search(ep, sentence, re.IGNORECASE)
                    if em:
                        responsible_entity = em.group(0).strip()
                        break

                # Extract Deadline
                deadline = None
                for dp in cls.DEADLINE_PATTERNS:
                    dm = re.search(dp, sentence, re.IGNORECASE)
                    if dm:
                        deadline = dm.group(0).strip()
                        break

                # Extract Conditions
                conditions = []
                for cp in cls.CONDITION_PREFIXES:
                    for cm in re.finditer(r'(?:' + cp + r')\s+([^,;.]+)', sentence, re.IGNORECASE):
                        cond_text = cm.group(0).strip()
                        if cond_text not in conditions:
                            conditions.append(cond_text)

                # Extract Exceptions
                exceptions = []
                for exp_p in cls.EXCEPTION_PREFIXES:
                    for exm in re.finditer(r'(?:' + exp_p + r')\s+([^,;.]+)', sentence, re.IGNORECASE):
                        ex_text = exm.group(0).strip()
                        if ex_text not in exceptions:
                            exceptions.append(ex_text)

                sentence_words = re.findall(r"[a-z0-9]+", sentence.lower())
                page_words = [
                    re.findall(r"[a-z0-9]+", box["text"].lower())
                    for box in word_boxes
                ]
                flattened_page_words = [
                    (word, box)
                    for words, box in zip(page_words, word_boxes)
                    for word in words
                ]
                matching_boxes = []
                for start in range(len(flattened_page_words) - len(sentence_words) + 1):
                    window = flattened_page_words[start:start + len(sentence_words)]
                    if [word for word, _ in window] == sentence_words:
                        matching_boxes = [box for _, box in window]
                        break

                bounding_box = {}
                if matching_boxes:
                    bounding_box = {
                        "x0": min(b["x0"] for b in matching_boxes),
                        "top": min(b["top"] for b in matching_boxes),
                        "x1": max(b["x1"] for b in matching_boxes),
                        "bottom": max(b["bottom"] for b in matching_boxes),
                        "page": page_num
                    }

                # Confidence calculation
                confidence = modal_confidence
                if responsible_entity:
                    confidence = min(0.98, confidence + 0.05)
                else:
                    confidence = max(0.65, confidence - 0.15)

                if deadline:
                    confidence = min(0.99, confidence + 0.04)

                year_tag = "2024"
                if circular_number and re.search(r'202[4-6]', circular_number):
                    m_yr = re.search(r'202[4-6]', circular_number)
                    if m_yr:
                        year_tag = m_yr.group(0)

                obl_code = f"OBL-{year_tag}-{obl_counter:03d}"
                obl_counter += 1

                review_status = "approved" if confidence >= 0.88 else "pending"

                obligations.append({
                    "obligation_code": obl_code,
                    "source_page": page_num,
                    "obligation_text": sentence,
                    "source_text": page_text[char_start:char_end],
                    "char_start": char_start,
                    "char_end": char_end,
                    "responsible_entity": responsible_entity,
                    "required_action": matched_action or sentence,
                    "deadline": deadline,
                    "conditions": conditions,
                    "exceptions": exceptions,
                    "confidence_score": round(confidence, 2),
                    "evidence_status": (
                        "anchored"
                        if page_text[char_start:char_end].strip()
                        else "mismatched"
                    ),
                    "review_status": review_status,
                    "extraction_method": "normative_modal_nlp_baseline",
                    "bounding_box": bounding_box
                })

        return obligations
