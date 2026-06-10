from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
import re
import time

try:
    import requests
except ImportError:  # pragma: no cover - surfaced only when running network fetches
    requests = None


ROOT = Path(__file__).resolve().parents[2]
RAW_CDC_DIR = ROOT / "data" / "raw" / "cdc_wonder"
BASE_URL = "https://wonder.cdc.gov"


@dataclass(frozen=True)
class WonderDatabase:
    code: str
    request_url: str
    label: str
    vintage: str


@dataclass(frozen=True)
class WonderExportSpec:
    filename: str
    database_key: str
    group_by: tuple[str, ...]
    cause_mode: str
    cause_values: tuple[str, ...]
    cause_highlight: str


DATABASES = {
    "1999_2020": WonderDatabase(
        code="D76",
        request_url=f"{BASE_URL}/controller/datarequest/D76",
        label="Underlying Cause of Death, 1999-2020",
        vintage="2020",
    ),
    "2018_2024": WonderDatabase(
        code="D158",
        request_url=f"{BASE_URL}/controller/datarequest/D158",
        label="Underlying Cause of Death, 2018-2024, Single Race",
        vintage="2024",
    ),
}


def _by_vars(code: str, *, sex_age: bool = False) -> tuple[str, ...]:
    by_vars = [f"{code}.V9-level1", f"{code}.V1-level1"]
    if sex_age:
        by_vars.extend([f"{code}.V7", f"{code}.V5"])
    return tuple(by_vars)


def _cause_values(code: str, mode: str, values: tuple[str, ...], highlight: str):
    return {
        "cause_mode": mode,
        "cause_values": values,
        "cause_highlight": highlight.format(code=code),
    }


def build_export_specs() -> list[WonderExportSpec]:
    specs = []
    outcome_defs = [
        (
            "negative_control_cancer",
            "cause113",
            ("GR113-019",),
            "Malignant neoplasms (C00-C97)",
        ),
        (
            "negative_control_cardiovascular",
            "icd10",
            ("I00-I99",),
            "I00-I99 (Diseases of the circulatory system)",
        ),
        (
            "negative_control_motor_vehicle",
            "cause113",
            ("GR113-114",),
            "Motor vehicle accidents",
        ),
    ]
    for database_key, year_label in [
        ("1999_2020", "1999_2020"),
        ("2018_2024", "2018_2024_single_race"),
    ]:
        code = DATABASES[database_key].code
        for stem, mode, values, highlight in outcome_defs:
            specs.append(
                WonderExportSpec(
                    filename=f"{stem}_{year_label}.xls",
                    database_key=database_key,
                    group_by=_by_vars(code),
                    **_cause_values(code, mode, values, highlight),
                )
            )
        specs.append(
            WonderExportSpec(
                filename=f"firearm_suicide_by_sex_age_{year_label}.xls",
                database_key=database_key,
                group_by=_by_vars(code, sex_age=True),
                **_cause_values(
                    code,
                    "cause113",
                    ("GR113-125",),
                    "Intentional self-harm (suicide) by discharge of firearms (X72-X74)",
                ),
            )
        )
    return specs


class _WonderFormParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_form = False
        self.action = ""
        self.payload: list[tuple[str, str]] = []
        self._select_name = None
        self._select_multiple = False
        self._select_options: list[tuple[str, bool]] = []
        self._textarea_name = None
        self._textarea_chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.in_form = True
            self.action = attrs.get("action", "")
            return
        if not self.in_form:
            return
        if tag == "input":
            self._handle_input(attrs)
        elif tag == "select":
            self._select_name = attrs.get("name")
            self._select_multiple = "multiple" in attrs
            self._select_options = []
        elif tag == "option" and self._select_name:
            value = attrs.get("value", "")
            self._select_options.append((value, "selected" in attrs))
        elif tag == "textarea":
            self._textarea_name = attrs.get("name")
            self._textarea_chunks = []

    def handle_endtag(self, tag):
        if not self.in_form:
            return
        if tag == "select" and self._select_name:
            selected = [value for value, is_selected in self._select_options if is_selected]
            if not selected and not self._select_multiple and self._select_options:
                selected = [self._select_options[0][0]]
            for value in selected:
                self.payload.append((self._select_name, value))
            self._select_name = None
            self._select_multiple = False
            self._select_options = []
        elif tag == "textarea" and self._textarea_name:
            self.payload.append((self._textarea_name, "".join(self._textarea_chunks)))
            self._textarea_name = None
            self._textarea_chunks = []
        elif tag == "form":
            self.in_form = False

    def handle_data(self, data):
        if self._textarea_name:
            self._textarea_chunks.append(data)

    def _handle_input(self, attrs):
        if "disabled" in attrs:
            return
        input_type = attrs.get("type", "text").lower()
        if input_type in {"submit", "button", "reset", "image"}:
            return
        if input_type in {"checkbox", "radio"} and "checked" not in attrs:
            return
        name = attrs.get("name")
        if not name:
            return
        self.payload.append((name, attrs.get("value", "")))


def parse_wonder_form(html: str, base_url: str = BASE_URL) -> tuple[str, list[tuple[str, str]]]:
    parser = _WonderFormParser()
    parser.feed(html)
    if not parser.action:
        raise ValueError("CDC WONDER form action was not found")
    return urljoin(base_url, parser.action), parser.payload


def apply_payload_overrides(
    payload: Iterable[tuple[str, str]],
    *,
    overrides: dict[str, str | Iterable[str]],
    remove: set[str] | None = None,
) -> list[tuple[str, str]]:
    remove = remove or set()
    replaced = set(overrides)
    out = [(key, value) for key, value in payload if key not in replaced and key not in remove]
    for key, raw_values in overrides.items():
        if isinstance(raw_values, str):
            values = [raw_values]
        else:
            values = list(raw_values)
        out.extend((key, value) for value in values)
    return out


def _group_by_overrides(group_by: tuple[str, ...]) -> dict[str, str]:
    values = list(group_by[:5]) + ["*None*"] * (5 - len(group_by))
    return {f"B_{idx}": value for idx, value in enumerate(values, start=1)}


def build_query_overrides(spec: WonderExportSpec) -> tuple[dict[str, str | Iterable[str]], set[str]]:
    db = DATABASES[spec.database_key]
    code = db.code
    overrides: dict[str, str | Iterable[str]] = {
        "dataset_code": code,
        "dataset_label": db.label,
        "dataset_vintage": db.vintage,
        "stage": "request",
        "action-Send": "Send",
        "O_javascript": "on",
        "O_aar": "aar_none",
        "M_1": f"{code}.M1",
        "M_2": f"{code}.M2",
        "M_3": f"{code}.M3",
        "O_location": f"{code}.V9",
        "O_age": f"{code}.V5",
        f"V_{code}.V5": "*All*",
        f"V_{code}.V7": "*All*",
        f"F_{code}.V1": "*All*",
        f"F_{code}.V9": "*All*",
        f"I_{code}.V1": "*All* (All Dates)",
        f"I_{code}.V9": "*All* (The United States)",
        f"finder-stage-{code}.V1": "codeset",
        f"finder-stage-{code}.V9": "codeset",
        "O_V1_fmode": "freg",
        "O_V9_fmode": "freg",
        "O_rate_per": "100000",
        "O_show_zeros": "true",
        "O_precision": "1",
        "O_timeout": "300",
        "O_change_action-Send-Export Results": "Export Results",
        "O_export-format": "xls",
    }
    overrides.update(_group_by_overrides(spec.group_by))

    if code == "D76":
        overrides[f"V_{code}.V8"] = "*All*"
        overrides[f"V_{code}.V17"] = "*All*"
    else:
        overrides[f"V_{code}.V42"] = "*All*"
        overrides[f"V_{code}.V17"] = "*All*"

    if spec.cause_mode == "icd10":
        overrides["O_ucd"] = f"{code}.V2"
        overrides[f"F_{code}.V2"] = list(spec.cause_values)
        overrides[f"I_{code}.V2"] = spec.cause_highlight
        overrides[f"finder-stage-{code}.V2"] = "codeset"
        overrides["O_V2_fmode"] = "freg"
    elif spec.cause_mode == "cause113":
        overrides["O_ucd"] = f"{code}.V4"
        overrides[f"V_{code}.V4"] = list(spec.cause_values)
    else:
        raise ValueError(f"Unsupported WONDER cause mode: {spec.cause_mode}")

    return overrides, {"O_show_totals"}


def extract_wonder_errors(html: str) -> list[str]:
    if "error-message" not in html and "error-header" not in html:
        return []
    messages = re.findall(r'<div class="error-message">\s*.*?&nbsp;\s*(.*?)</div>', html, re.S)
    return [re.sub(r"<[^>]+>", "", msg).strip() for msg in messages]


def fetch_one_export(session, spec: WonderExportSpec, output_dir: Path = RAW_CDC_DIR) -> Path:
    if requests is None:
        raise RuntimeError("The requests package is required to fetch CDC WONDER exports")

    db = DATABASES[spec.database_key]
    agree = session.post(
        db.request_url,
        data={"stage": "about", "action-I Agree": "I Agree"},
        timeout=60,
    )
    agree.raise_for_status()
    action_url, default_payload = parse_wonder_form(agree.text)
    overrides, remove = build_query_overrides(spec)
    payload = apply_payload_overrides(default_payload, overrides=overrides, remove=remove)

    response = session.post(action_url, data=payload, timeout=360)
    response.raise_for_status()
    text_sample = response.text[:2000]
    if text_sample.lstrip().startswith("<"):
        errors = extract_wonder_errors(response.text)
        joined = "; ".join(errors) if errors else "unexpected HTML response"
        raise RuntimeError(f"CDC WONDER export failed for {spec.filename}: {joined}")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / spec.filename
    out_file.write_bytes(response.content)
    return out_file


def fetch_all_exports(output_dir: Path = RAW_CDC_DIR, *, sleep_seconds: float = 1.0) -> list[Path]:
    if requests is None:
        raise RuntimeError("The requests package is required to fetch CDC WONDER exports")
    written = []
    with requests.Session() as session:
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 permitless-carry-analysis CDC-WONDER fetcher",
                "Referer": BASE_URL,
            }
        )
        for spec in build_export_specs():
            out_file = fetch_one_export(session, spec, output_dir=output_dir)
            written.append(out_file)
            print(f"Wrote: {out_file.relative_to(ROOT)}")
            time.sleep(sleep_seconds)
    return written


def main():
    fetch_all_exports()


if __name__ == "__main__":
    main()
