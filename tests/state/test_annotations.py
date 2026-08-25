"""AnnotationsIndex: machine-local realization facts, secret-aware on display.

A secret-marked entry ({value: …, secret: true}, wire.cddl) is access
material — the runner may hand it to effectful plugins, but freckles never
prints it (design.md §9).
"""

from freckles.documents import cid_for_blob
from freckles.state import AnnotationsIndex, StateDb


def test_redacted_view_hides_secret_marked_values(tmp_path):
    index = AnnotationsIndex(StateDb(tmp_path / "state.sqlite"))
    claim = cid_for_blob(b"claim-stand-in")
    index.set(
        claim,
        {
            "deployed_at": "2026-08-24T12:00:00Z",
            "admin_token": {"value": "s3ns1tive-material", "secret": True},
        },
    )

    redacted = index.redacted(claim)

    assert redacted["deployed_at"] == "2026-08-24T12:00:00Z"
    assert redacted["admin_token"] == "<secret — not shown>"
    assert "s3ns1tive-material" not in str(redacted)

    # the full view is untouched — effectful runs still receive the material
    assert index.get(claim)["admin_token"]["value"] == "s3ns1tive-material"


def test_distrust_marks_are_set_read_and_cleared(tmp_path):
    index = AnnotationsIndex(StateDb(tmp_path / "state.sqlite"))
    claim = cid_for_blob(b"deployed-site-claim")

    assert index.distrusted(claim) is None  # trusted until contradicted

    index.distrust(claim, "health endpoint unreachable")
    assert index.distrusted(claim) == "health endpoint unreachable"

    index.clear_distrust(claim)
    assert index.distrusted(claim) is None


def test_distrust_marks_stay_out_of_the_annotations(tmp_path):
    """Trust state never leaks into what effectful runs and prior: receive."""
    index = AnnotationsIndex(StateDb(tmp_path / "state.sqlite"))
    claim = cid_for_blob(b"deployed-site-claim")
    index.set(claim, {"deployed_at": "2026-08-25T12:00:00Z"})

    index.distrust(claim, "drifted")

    assert index.get(claim) == {"deployed_at": "2026-08-25T12:00:00Z"}
    assert index.redacted(claim) == {"deployed_at": "2026-08-25T12:00:00Z"}
