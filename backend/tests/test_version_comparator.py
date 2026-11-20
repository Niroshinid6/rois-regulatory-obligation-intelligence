from app.services.version_comparator import VersionComparator


def _obligation(obligation_id: int, **overrides):
    obligation = {
        "id": obligation_id,
        "obligation_text": "The regulated entity shall submit a report within 30 days.",
        "required_action": "submit a report",
        "responsible_entity": "regulated entity",
        "deadline": "within 30 days",
        "conditions": [],
        "exceptions": [],
        "source_page": 1,
    }
    obligation.update(overrides)
    return obligation


def test_identical_obligation_is_not_marked_human_verified():
    changes = VersionComparator.compare_documents(
        [_obligation(1)],
        [_obligation(2)],
    )

    assert changes[0]["change_type"] == "unchanged"
    assert changes[0]["human_verified"] is False


def test_attribute_change_is_classified_as_modified():
    changes = VersionComparator.compare_documents(
        [_obligation(1)],
        [_obligation(2, deadline="within 15 days")],
    )

    assert changes[0]["change_type"] == "modified"
    assert changes[0]["diff_details"]["changed_attributes"]["deadline"] == {
        "previous": "within 30 days",
        "current": "within 15 days",
    }


def test_ambiguous_text_match_requires_review():
    changes = VersionComparator.compare_documents(
        [_obligation(1)],
        [_obligation(
            2,
            obligation_text="The regulated entity shall submit a return within 30 days.",
        )],
    )

    assert changes[0]["change_type"] == "requires_review"
    assert changes[0]["human_verified"] is False


def test_each_prior_obligation_is_matched_at_most_once():
    changes = VersionComparator.compare_documents(
        [_obligation(1)],
        [_obligation(2), _obligation(3)],
    )

    matched_prior_ids = [
        change["previous_obligation_id"]
        for change in changes
        if change["previous_obligation_id"] is not None
    ]
    assert matched_prior_ids == [1]
    assert [change["change_type"] for change in changes] == [
        "unchanged",
        "new",
    ]
