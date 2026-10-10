"""Public endpoints: content, filters and data-availability behaviour."""

API = "/api/v1"


def test_health(client):
    r = client.get(f"{API}/health")
    assert r.status_code == 200
    body = r.json()
    assert body["database"] == "ok" and body["has_content"] is True


def test_conflicts_listed_in_order(client):
    r = client.get(f"{API}/conflicts")
    slugs = [c["slug"] for c in r.json()]
    assert slugs == ["primeira-guerra-mundial", "segunda-guerra-mundial"]


def test_conflict_structure_contains_registered_theaters(client):
    c = client.get(f"{API}/conflicts/primeira-guerra-mundial").json()
    names = {t["slug"] for t in c["theaters"]}
    assert {"frente-ocidental-1gm", "frente-oriental-1gm", "galipoli", "oriente-medio-1gm", "balcas-1gm", "guerra-naval-1gm"} <= names
    western = next(t for t in c["theaters"] if t["slug"] == "frente-ocidental-1gm")
    assert any(b["slug"] == "batalha-do-somme" for b in western["battles"])


def test_unknown_entity_returns_structured_404(client):
    r = client.get(f"{API}/battles/batalha-inexistente")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_battle_sheet_has_sources_and_divergent_figures(client):
    b = client.get(f"{API}/battles/batalha-do-somme").json()
    assert b["citations"], "battle must expose its sources"
    german = [f for f in b["figures"] if f["metric"] == "casualties" and f["side"] == "b"]
    assert len(german) >= 3, "divergent German casualty figures must all be kept"
    assert all(f["source"] for f in german)
    assert {p["slug"] for p in [x["polity"] for x in b["participants"]]} >= {"reino-unido-1801", "imperio-alemao"}
    assert len(b["phases"]) >= 5


def test_bidirectional_navigation_battle_person(client):
    b = client.get(f"{API}/battles/batalha-do-somme").json()
    assert any(c["person"]["slug"] == "douglas-haig" for c in b["commanders"])
    p = client.get(f"{API}/persons/douglas-haig").json()
    assert any(x["battle"]["slug"] == "batalha-do-somme" for x in p["battles"])
    assert any(pos["unit"] and pos["unit"]["slug"] == "bef-1914" for pos in p["positions"])


def test_equipment_unit_links_are_explicit_only(client):
    e = client.get(f"{API}/equipment/m4-sherman").json()
    unit_slugs = {u["unit"]["slug"] for u in e["units"]}
    # national service (USA) must NOT imply every US unit used it
    assert unit_slugs == {"2-division-blindee", "1-divisao-blindada-polonesa"}
    assert {u["polity"]["slug"] for u in e["users"]} >= {"estados-unidos", "reino-unido"}


def test_equipment_filters(client):
    tanks = client.get(f"{API}/equipment", params={"category": "tank"}).json()
    assert tanks and all(t["category"] == "tank" for t in tanks)
    ww1 = {e["slug"] for e in client.get(f"{API}/equipment", params={"conflict": "primeira-guerra-mundial"}).json()}
    assert "tanque-mark-i" in ww1 and "m4-sherman" not in ww1


def test_search_grouped_and_filtered(client):
    r = client.get(f"{API}/search", params={"q": "sherman"}).json()
    assert r["groups"][0]["type"] == "equipment"
    r = client.get(f"{API}/search", params={"q": "divisão", "types": "unit", "conflict": "segunda-guerra-mundial"}).json()
    slugs = {i["slug"] for g in r["groups"] for i in g["items"]}
    assert "1-divisao-infantaria-eua" in slugs and "29-divisao-britanica" not in slugs
    # a WWI unit with open-ended existence must not be inferred into WWII
    assert "1-divisao-australiana" not in slugs


def test_equipment_conflict_filter_uses_documented_use_only(client):
    ww2 = {e["slug"] for e in client.get(f"{API}/equipment", params={"conflict": "segunda-guerra-mundial"}).json()}
    assert "tanque-mark-i" not in ww2 and "m4-sherman" in ww2
    r = client.get(f"{API}/search", params={"q": "mark i", "types": "equipment", "conflict": "segunda-guerra-mundial"}).json()
    assert r["total"] == 0


def test_search_is_accent_insensitive(client):
    r = client.get(f"{API}/search", params={"q": "pozieres"}).json()
    assert any(i["slug"] == "batalha-de-pozieres" for g in r["groups"] for i in g["items"])


def test_search_returns_nothing_artificial(client):
    r = client.get(f"{API}/search", params={"q": "zzzqqq"}).json()
    assert r["total"] == 0 and r["groups"] == []


def test_research_evidence_reports_absence_honestly(client):
    r = client.get(f"{API}/research/evidence", params={"q": "batalha de stalingrado"}).json()
    assert r["items"] == [] and "Ausência" in r["note"]
