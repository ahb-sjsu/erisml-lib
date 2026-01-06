# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the AGI-HPC Responsible AI License v1.0.
# You may obtain a copy of the License at the root of this repository,
# or by contacting the author(s).
#
# You may use, modify, and distribute this file for non-commercial
# research and educational purposes, subject to the conditions in
# the License. Commercial use, high-risk deployments, and autonomous
# operation in safety-critical domains require separate written
# permission and must include appropriate safety and governance controls.
#
# Unless required by applicable law or agreed to in writing, this
# software is provided "AS IS", without warranties or conditions
# of any kind. See the License for the specific language governing
# permissions and limitations.

from __future__ import annotations

from erisml.core.model import ErisModel

try:
    import tarski  # type: ignore
    from tarski import fstrips as fs  # type: ignore
except ImportError:  # pragma: no cover
    tarski = None
    fs = None


def erisml_to_tarski(model: ErisModel):
    """Convert an ErisML model to a tarski/FSTRIPS problem (stub).

    This function illustrates where planning integration will live.
    """
    if tarski is None or fs is None:
        raise ImportError("tarski is not installed. Install with `pip install tarski`.")

    lang = fs.language.FStripsLanguage("erisml")

    obj_sorts = {}
    for name, obj_type in model.env.object_types.items():
        sort = lang.sort(name)
        obj_sorts[name] = sort
        for inst in obj_type.instances:
            lang.constant(inst, sort)

    problem = fs.Problem(lang)
    return problem
