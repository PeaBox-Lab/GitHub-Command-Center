from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class ReleaseGate:
    name:str;passed:bool;detail:str

def evaluate_release(*,tests_ok:bool,architecture_ok:bool,windows_validation:bool,ui_regression:bool,package_smoke:bool,signed:bool=False):
    gates=[ReleaseGate("Tests",tests_ok,"Automated tests"),ReleaseGate("Architecture",architecture_ok,"Architecture regression gate"),ReleaseGate("Windows validation",windows_validation,"windows-validation workflow"),ReleaseGate("Windows UI regression",ui_regression,"ui-regression matrix"),ReleaseGate("Package smoke",package_smoke,"Windows packaged smoke test"),ReleaseGate("Authenticode",signed,"Optional until signing certificate is configured")]
    required=all(x.passed for x in gates[:5]);return required,gates
