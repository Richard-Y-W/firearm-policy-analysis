from src.data.fetch_cdc_wonder_exports import (
    apply_payload_overrides,
    build_export_specs,
    parse_wonder_form,
)


def test_parse_wonder_form_extracts_action_and_default_payload():
    html = """
    <form method="post" action="/controller/datarequest/D76;jsessionid=ABC123">
      <input type="hidden" name="stage" value="request">
      <input type="hidden" name="dataset_code" value="D76">
      <input type="radio" name="O_location" value="D76.V9" checked>
      <input type="radio" name="O_location" value="D76.V10">
      <select name="B_1">
        <option value="D76.V9-level1">State</option>
        <option value="D76.V1-level1" selected>Year</option>
      </select>
      <select name="V_D76.V5" multiple>
        <option value="*All*" selected>All Ages</option>
        <option value="15-24">15-24 years</option>
      </select>
      <textarea name="I_D76.V2">selected text</textarea>
      <input type="submit" name="action-Send" value="Send">
    </form>
    """

    action, payload = parse_wonder_form(html, "https://wonder.cdc.gov")

    assert action == "https://wonder.cdc.gov/controller/datarequest/D76;jsessionid=ABC123"
    assert ("stage", "request") in payload
    assert ("O_location", "D76.V9") in payload
    assert ("B_1", "D76.V1-level1") in payload
    assert ("V_D76.V5", "*All*") in payload
    assert ("I_D76.V2", "selected text") in payload
    assert not any(key == "action-Send" for key, _ in payload)


def test_apply_payload_overrides_replaces_repeated_keys_and_removes_keys():
    payload = [
        ("B_1", "old"),
        ("B_2", "keep"),
        ("V_D76.V4", "*All*"),
        ("V_D76.V4", "other"),
        ("O_show_totals", "true"),
    ]

    out = apply_payload_overrides(
        payload,
        overrides={"B_1": ["new"], "V_D76.V4": ["GR113-019"]},
        remove={"O_show_totals"},
    )

    assert out == [
        ("B_2", "keep"),
        ("B_1", "new"),
        ("V_D76.V4", "GR113-019"),
    ]


def test_build_export_specs_includes_extra_negative_control_placebos():
    specs = {spec.filename: spec for spec in build_export_specs()}

    falls = specs["negative_control_falls_1999_2020.xls"]
    nontransport = specs[
        "negative_control_non_transport_injury_excluding_falls_poisoning_1999_2020.xls"
    ]
    poisoning = specs["negative_control_accidental_poisoning_1999_2020.xls"]

    assert falls.cause_values == ("GR113-118",)
    assert falls.cause_highlight == "Falls (W00-W19)"
    assert nontransport.cause_values == (
        "GR113-119",
        "GR113-120",
        "GR113-121",
        "GR113-123",
    )
    assert "GR113-118" not in nontransport.cause_values
    assert "GR113-122" not in nontransport.cause_values
    assert nontransport.cause_highlight == "Nontransport accidents excluding falls and accidental poisoning (excludes W00-W19 and X40-X49)"
    assert poisoning.cause_values == ("GR113-122",)
    assert poisoning.cause_highlight == "Accidental poisoning and exposure to noxious substances (X40-X49)"
    assert "negative_control_falls_2018_2024_single_race.xls" in specs
    assert (
        "negative_control_non_transport_injury_excluding_falls_poisoning_2018_2024_single_race.xls"
        in specs
    )
    assert (
        "negative_control_accidental_poisoning_2018_2024_single_race.xls"
        in specs
    )
