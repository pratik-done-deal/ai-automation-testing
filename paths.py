"""Where everything lives.

The suite owns everything in its folder, specs included. It lives both as `automation/` inside
donedeal-web and as the standalone ai-automation-testing repo. The application's source is reached
through APP_ROOT: the donedeal-web checkout around the suite, else a `donedeal-web` checkout next to
it; set DD_APP_ROOT to point anywhere else.
"""
import os
from pathlib import Path

AUTOMATION = Path(__file__).resolve().parent

SPECS = AUTOMATION / "specs"
MODULES_DIR = SPECS / "modules"     # platform modules: module.yml + module.md (the living spec)
FEATURES_DIR = SPECS / "features"   # PRD features: feature.yml, flow.yaml, refs/, impact.md
PRD_DIR = SPECS / "prd"             # PRDs, analyses, test plans

def _default_app_root():
    """Inside donedeal-web (automation/) the app is the folder around the suite; in the standalone
    ai-automation-testing repo it is a donedeal-web checkout next to it."""
    if (AUTOMATION.parent / "src").is_dir():
        return AUTOMATION.parent
    return AUTOMATION.parent / "donedeal-web"


APP_ROOT = Path(os.getenv("DD_APP_ROOT") or _default_app_root()).resolve()


def app_file(*parts):
    """A path inside the application repo, e.g. app_file("src", "config", "endpoint.js")."""
    return APP_ROOT.joinpath(*parts)


def spec_file(relative):
    """A spec path as the registry records it, e.g. "prd/x.analysis.md" -> specs/prd/x.analysis.md."""
    return SPECS / relative
