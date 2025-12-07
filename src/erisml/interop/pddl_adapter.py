from __future__ import annotations

from erisml.core.model import ErisModel

try:
    import tarski
    from tarski import fstrips as fs
except ImportError:  # pragma: no cover - optional dependency
    tarski = None
    fs = None


def erisml_to_tarski(model: ErisModel):
    '''Convert an ErisModel to a tarski/FSTRIPS problem (stub).

    This function illustrates where planning integration will live.
    '''
    if tarski is None or fs is None:
        raise ImportError(
            "tarski is not installed. Install with `pip install tarski`."
        )

    lang = fs.language.FStripsLanguage("erisml")

    obj_sorts = {}
    for name, obj_type in model.env.object_types.items():
        obj_sorts[name] = lang.sort(name)
        for inst in obj_type.instances:
            lang.constant(inst, obj_sorts[name])

    problem = fs.Problem(lang)
    return problem
