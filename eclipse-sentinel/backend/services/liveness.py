"""
Eclipse Sentinel — Prototype Liveness Check

PROTOTYPE LIVENESS — placeholder for when camera/multi-frame
input is available.  In the current prototype (single image upload),
we cannot perform real liveness detection, so this module
returns a clearly labelled status.

When multi-frame camera input is available in future versions,
this module should check for blink detection, head movement,
and face presence across frames.
"""


def check_liveness_placeholder() -> dict:
    """
    Prototype liveness check.

    In the current version (image upload only), real liveness
    detection is not possible.  This returns a clearly marked
    prototype status.
    """
    return {
        "status": "NOT AVAILABLE",
        "label": "PROTOTYPE LIVENESS",
        "reason": (
            "Liveness detection requires multi-frame camera input. "
            "This prototype currently supports single-image upload only."
        ),
        "prototype_note": (
            "Future versions will implement blink detection and "
            "head-movement analysis using live camera frames."
        ),
    }
