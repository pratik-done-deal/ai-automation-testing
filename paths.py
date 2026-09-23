"""Where everything lives.

The suite owns everything under `automation/`, its specs included, so this folder can be moved to a
repo of its own. The application it tests is reached through APP_ROOT, which defaults to the checkout
this folder sits in; set DD_APP_ROOT when the suite lives somewhere else.
"""
import os
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parent

SPECS = AUTOMATION / "specs"
MODULES_DIR = SPECS / "modules"     # platform modules: module.yml + module.md (the living spec)
FEATURES_DIR = SPECS / "features"   # PRD features: feature.yml, flow.yaml, refs/, impact.md
PRD_DIR = SPECS / "prd"             # PRDs, analyses, test plans

APP_ROOT = Path(os.getenv("DD_APP_ROOT", AUTOMATION.parent)).resolve()


def app_file(*parts):
    """A path inside the application repo, e.g. app_file("src", "config", "endpoint.js")."""
    return APP_ROOT.joinpath(*parts)


def spec_file(relative):
    """A spec path as the registry records it, e.g. "prd/x.analysis.md" -> automation/specs/prd/x.analysis.md."""
    return SPECS / relative
