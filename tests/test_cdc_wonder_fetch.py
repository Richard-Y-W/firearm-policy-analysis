from src.data.fetch_cdc_wonder_exports import (
    apply_payload_overrides,
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
