"""
תקנות בריאות העם (איכותם התברואית של מי שתייה), תשע"ג-2013
Drinking water regulation limits – Israel 2013.

Each entry: format.csv test name → (limit_value, unit, note)
limit_value=None means no regulatory limit (aesthetic / monitoring only).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Limit:
    value: Optional[float]   # numeric limit
    unit: str                 # unit matching format.csv
    note: str = ""            # display string, e.g. "≤10 µg/L"

    def exceeded_by(self, measured: float) -> bool:
        return self.value is not None and measured > self.value

    def __str__(self) -> str:
        return self.note if self.note else (
            f"≤{self.value} {self.unit}" if self.value is not None else "—"
        )


LIMITS: dict[str, Limit] = {
    # ── Inorganic – Table A ──────────────────────────────────────────
    "ANTIMONY (Sb)":                 Limit(6,      "µg/L",  "≤6 µg/L"),
    "ARSENIC AS AS":                 Limit(10,     "µg/L",  "≤10 µg/L"),
    "BERYLIUM (Be)":                 Limit(4,      "µg/L",  "≤4 µg/L"),
    "BORON AS B":                    Limit(1.0,    "mg/L",  "≤1 mg/L"),
    "BARIUM AS BA":                  Limit(1000,   "µg/L",  "≤1000 µg/L"),
    "NITRATE AS NO3":                Limit(70,     "mg/L",  "≤70 mg/L"),
    "SILVER (Ag)":                   Limit(100,    "µg/L",  "≤100 µg/L"),
    "MERCURY AS HG":                 Limit(1,      "µg/L",  "≤1 µg/L"),
    "CHROMIUM AS CR":                Limit(50,     "µg/L",  "≤50 µg/L"),
    "CADMIUM AS CD":                 Limit(5,      "µg/L",  "≤5 µg/L"),
    "NICKEL AS NI":                  Limit(20,     "µg/L",  "≤20 µg/L"),
    "SELENIUM AS SE":                Limit(10,     "µg/L",  "≤10 µg/L"),
    "LEAD AS PB":                    Limit(10,     "µg/L",  "≤10 µg/L"),
    "FLUORIDE AS F":                 Limit(1.7,    "mg/L",  "≤1.7 mg/L"),
    "CYANIDE AS CN":                 Limit(50,     "µg/L",  "≤50 µg/L"),

    # ── Organic – Table C ────────────────────────────────────────────
    "BENZENE":                       Limit(5,      "µg/L",  "≤5 µg/L"),
    "ETHYL BENZENE":                 Limit(300,    "µg/L",  "≤300 µg/L"),
    "TOLUENE":                       Limit(700,    "µg/L",  "≤700 µg/L"),
    "XYLENE":                        Limit(500,    "µg/L",  "≤500 µg/L"),
    "VINYL CHLORIDE (VC)":           Limit(0.5,    "µg/L",  "≤0.5 µg/L"),
    "CHLOROFORM":                    Limit(80,     "µg/L",  "≤80 µg/L"),
    "TETRACHLOROETHYLENE (PCE)":     Limit(10,     "µg/L",  "≤10 µg/L"),
    "TRICHLOROETHYLENE (TCE)":       Limit(20,     "µg/L",  "≤20 µg/L"),
    "CARBON TETRACHLORIDE":          Limit(4,      "µg/L",  "≤4 µg/L"),
    "DICHLOROETHANE1,2":             Limit(4,      "µg/L",  "≤4 µg/L"),
    "DICHLOROETHYLENE 1,1 (1,1 DCE)":Limit(10,    "µg/L",  "≤10 µg/L"),
    "CIS 1,2 DICHLOROETHYLENE (C1,2 DCE)": Limit(50, "µg/L","≤50 µg/L"),
    "TRANS-1,2 DICHLOROETHYLENE (T1,2 DCE)":Limit(50,"µg/L","≤50 µg/L"),
    "METHYLENE CHLORIDE (DCM)":      Limit(5,      "µg/L",  "≤5 µg/L"),
    "1,2-DICHLOROPROPANE":           Limit(5,      "µg/L",  "≤5 µg/L"),
    "1,1,2-TRICHLOROETHANE (1,1,2 TCA)": Limit(5, "µg/L",  "≤5 µg/L"),
    "TRICHLORO ETHANE 1,1,1 (1,1,1 TCA)":Limit(200,"µg/L", "≤200 µg/L"),
    "1,2,4-TRICHLOROBENZENE":        Limit(70,     "µg/L",  "≤70 µg/L"),
    "1,2 DICHLOROBENZENE (ODCB)":    Limit(600,    "µg/L",  "≤600 µg/L"),
    "1,4 DICHLOROBENZENE (1,4 DCB)": Limit(75,     "µg/L",  "≤75 µg/L"),
    "MONOCHLOROBENZENE":             Limit(100,    "µg/L",  "≤100 µg/L"),
    "STYRENE":                       Limit(50,     "µg/L",  "≤50 µg/L"),
    "ETHYLENE DIBROMIDE (EDB)":      Limit(0.05,   "µg/L",  "≤0.05 µg/L"),
    "ZINC AS ZN":                    Limit(5000,   "µg/L",  "≤5000 µg/L"),

    # ── No limit ─────────────────────────────────────────────────────
    "CALCIUM AS CA":                 Limit(None, "mg/L"),
    "MAGNESIUM AS MG":               Limit(None, "mg/L"),
    "SODIUM AS NA":                  Limit(None, "mg/L"),
    "POTASSIUM AS K":                Limit(None, "mg/L"),
    "CHLORIDE AS CL":                Limit(400,  "mg/L",  "≤400 mg/L"),
    "SULFATE AS SO4":                Limit(250,  "mg/L",  "≤250 mg/L"),
    "BICARBONATE AS HCO3":           Limit(None, "mg/L"),
    "BROMIDE AS BR":                 Limit(None, "mg/L"),
    "PHOSPHATE AS PO4":              Limit(None, "mg/L"),
    "TOTAL ORGANIC CARBON (TOC)":    Limit(None, "mg/L"),
    "TOTAL NITROGEN AS N":           Limit(None, "mg/L"),
    "ALUMINUM (Al)":                 Limit(200,  "µg/L",  "≤200 µg/L"),
    "COBALT AS CO":                  Limit(None, "µg/L"),
    "COPPER AS CU":                  Limit(None, "µg/L"),
    "FERROUS IRON DISSOLVED AS FE":  Limit(None, "µg/L"),
    "MANGANESE TOTAL AS MN":         Limit(200,  "µg/L",  "≤200 µg/L"),
}


def get_limit(test_name: str) -> Limit:
    """Return the regulation limit for a test name, or a blank Limit."""
    return LIMITS.get(test_name, Limit(None, "—"))


def compliance_status(test_name: str, value) -> str:
    """Return a status string for a measured value against its limit.

    Returns one of: 'תקין', 'חריג!', 'בגבול גילוי', 'לא ניתן לאמת', 'לא נבדק'
    """
    if value is None:
        return "לא נבדק"

    if isinstance(value, str):
        v_lower = value.lower()
        if "not detected" in v_lower or "nd" == v_lower:
            lim = get_limit(test_name)
            if lim.value is not None and lim.unit in ("µg/L",) and lim.value < 1.0:
                return "לא ניתן לאמת"   # LOQ may be above the limit
            return "תקין"
        return "תקין"

    lim = get_limit(test_name)
    if lim.value is None:
        return "תקין"

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "לא נבדק"

    if numeric > lim.value:
        return "חריג!"
    if numeric > lim.value * 0.9:
        return "בגבול גילוי"
    return "תקין"
