"""Temporal integrity: relations are only shown inside their documented intervals."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import models as m

API = "/api/v1"


def _tree_names(nodes):
    out = set()
    for n in nodes:
        out.add(n["slug"])
        out |= _tree_names(n["children"])
    return out


def test_hierarchy_changes_with_date(client):
    jul1 = client.get(f"{API}/forces/exercito-imperial-alemao", params={"date": "1916-07-01"}).json()
    assert {"2-armee-1914", "xiv-reservekorps", "26-reserve-division"} <= _tree_names(jul1["tree"])
    assert "hgr-kronprinz-rupprecht" not in _tree_names(jul1["tree"])
    sep1 = client.get(f"{API}/forces/exercito-imperial-alemao", params={"date": "1916-09-01"}).json()
    top = [n["slug"] for n in sep1["tree"]]
    assert top == ["hgr-kronprinz-rupprecht"]
    assert {c["slug"] for c in sep1["tree"][0]["children"]} == {"1-armee-1914", "2-armee-1914"}


def test_attested_bounds_are_not_extended(client):
    """A subordination attested only on 1 Jul 1916 must not appear on 2 Jul 1916."""
    jul2 = client.get(f"{API}/forces/exercito-imperial-alemao", params={"date": "1916-07-02"}).json()
    assert "xiv-reservekorps" not in _tree_names(jul2["tree"])
    assert any(u["slug"] == "xiv-reservekorps" for u in jul2["unplaced_units"]), "unit is listed as 'no documented subordination'"


def test_unit_not_shown_before_formation(client):
    jul1 = client.get(f"{API}/forces/exercito-imperial-alemao", params={"date": "1916-07-01"}).json()
    assert all(u["slug"] != "1-armee-1914" for u in jul1["unplaced_units"])
    unit = client.get(f"{API}/units/1-armee-1914", params={"date": "1916-07-01"}).json()
    assert unit["existence_at_date"] == "not_yet_formed"


def test_commander_changes_with_date(client):
    jul = client.get(f"{API}/units/1-exercito-eua", params={"date": "1944-07-15"}).json()["at_date"]
    aug = client.get(f"{API}/units/1-exercito-eua", params={"date": "1944-08-15"}).json()["at_date"]
    assert [c["person"]["slug"] for c in jul["commanders"]] == ["omar-bradley"]
    assert [c["person"]["slug"] for c in aug["commanders"]] == ["courtney-hodges"]
    assert [p["target"]["slug"] for p in jul["parents"]] == ["21-grupo-exercitos"]
    assert [p["target"]["slug"] for p in aug["parents"]] == ["12-grupo-exercitos"]


def test_same_person_different_posts_over_time(client):
    p = client.get(f"{API}/persons/omar-bradley", params={"date": "1944-08-15"}).json()
    current = [x["unit"]["slug"] for x in p["positions"] if x["valid_at_date"]]
    assert current == ["12-grupo-exercitos"]
    assert {x["unit"]["slug"] for x in p["positions"]} == {"1-exercito-eua", "12-grupo-exercitos"}


def test_unit_name_valid_at_date(client):
    jul = client.get(f"{API}/units/5-exercito-britanico-1916", params={"date": "1916-07-01"}).json()
    nov = client.get(f"{API}/units/5-exercito-britanico-1916", params={"date": "1916-11-01"}).json()
    assert [n["name"] for n in jul["at_date"]["names"]] == ["Reserve Army"]
    assert [n["name"] for n in nov["at_date"]["names"]] == ["Fifth Army"]
    assert len(jul["names"]) == 2, "full history remains available"


def test_unit_equipment_only_within_interval(client):
    on = client.get(f"{API}/units/secao-pesada-mgc", params={"date": "1916-09-15"}).json()["at_date"]["equipment"]
    off = client.get(f"{API}/units/secao-pesada-mgc", params={"date": "1916-07-01"}).json()["at_date"]["equipment"]
    assert [e["equipment"]["slug"] for e in on] == ["tanque-mark-i"] and off == []


def test_participants_by_date(client):
    def slugs(d):
        return {p["polity"]["slug"] for p in client.get(f"{API}/conflicts/primeira-guerra-mundial/participants", params={"date": d}).json()}
    assert "estados-unidos" not in slugs("1916-07-01")
    assert "estados-unidos" in slugs("1917-06-01")
    assert "imperio-russo" in slugs("1916-07-01") and "imperio-russo" not in slugs("1917-06-01")


def test_map_features_respect_date(client):
    def layers(d):
        fc = client.get(f"{API}/map/features", params={"conflict": "primeira-guerra-mundial", "date": d, "window": 0}).json()
        return fc["features"]
    jul1 = layers("1916-07-01")
    assert any(f["properties"]["slug"] == "somme-frente-britanica-1-jul-1916" for f in jul1)
    front = next(f for f in jul1 if f["properties"]["slug"] == "somme-frente-britanica-1-jul-1916")
    assert front["properties"]["approximate"] is True
    jul2 = layers("1916-07-02")
    assert not any(f["properties"]["slug"] == "somme-frente-britanica-1-jul-1916" for f in jul2)
    jun = layers("1916-06-01")
    assert not any(f["properties"]["layer"] == "battle" for f in jun), "future battles are never shown"
    dec = layers("1916-12-01")
    somme = next(f for f in dec if f["properties"]["slug"] == "batalha-do-somme")
    assert somme["properties"]["state"] == "past"


def test_boundary_snapshot_staleness(client):
    ww1 = client.get(f"{API}/map/state", params={"conflict": "primeira-guerra-mundial", "date": "1916-07-01"}).json()
    assert ww1["boundary_dataset"]["slug"] == "historical-basemaps-1914" and ww1["boundary_dataset"]["stale"] is False
    ww2 = client.get(f"{API}/map/state", params={"conflict": "segunda-guerra-mundial", "date": "1944-06-06"}).json()
    assert ww2["boundary_dataset"]["slug"] == "historical-basemaps-1938" and ww2["boundary_dataset"]["stale"] is True


def test_replay_steps_are_documented_dates_only(client, db):
    r = client.get(f"{API}/replay/campaign/campanha-da-normandia").json()
    step_dates = [s["date"] for s in r["steps"]]
    assert step_dates == sorted(step_dates)
    documented = {str(d) for d in db.scalars(select(m.Event.start_date))} | {str(d) for d in db.scalars(select(m.MapFeature.valid_from))}
    assert set(step_dates) <= documented
    assert "interpola" in r["method"]


def test_tree_requires_date(client):
    r = client.get(f"{API}/units/bef-1914/tree")
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_required"


# --- database-level constraints ---------------------------------------------

def _ids(db, model, *slugs):
    return [db.scalar(select(model.id).where(model.slug == s)) for s in slugs]


def test_db_rejects_overlapping_organic_subordination(db):
    from datetime import date
    unit_id, parent_id = _ids(db, m.Unit, "26-reserve-division", "2-armee-1914")
    db.add(m.UnitSubordination(unit_id=unit_id, parent_unit_id=parent_id, relation="organic", valid_from=date(1916, 7, 1), valid_to=date(1916, 7, 1)))
    with pytest.raises(IntegrityError, match="ex_unit_subordinations_organic_overlap"):
        db.flush()


def test_db_allows_attachment_overlapping_organic(db):
    from datetime import date
    unit_id, parent_id = _ids(db, m.Unit, "26-reserve-division", "2-armee-1914")
    db.add(m.UnitSubordination(unit_id=unit_id, parent_unit_id=parent_id, relation="attached", valid_from=date(1916, 7, 1), valid_to=date(1916, 7, 1)))
    db.flush()  # attachments may coexist with the organic parent


def test_db_rejects_two_titular_commanders(db):
    from datetime import date
    (unit_id,) = _ids(db, m.Unit, "1-exercito-eua")
    (person_id,) = _ids(db, m.Person, "george-patton")
    db.add(m.PersonPosition(person_id=person_id, unit_id=unit_id, kind="commander", title="teste", valid_from=date(1944, 7, 1), valid_to=date(1944, 7, 2)))
    with pytest.raises(IntegrityError, match="ex_person_positions_single_commander"):
        db.flush()


def test_db_rejects_inverted_interval(db):
    from datetime import date
    (polity_id,) = _ids(db, m.Polity, "belgica")
    db.add(m.PolityPeriod(polity_id=polity_id, valid_from=date(1920, 1, 1), valid_to=date(1919, 1, 1)))
    with pytest.raises(IntegrityError, match="valid_interval"):
        db.flush()


def test_db_rejects_published_media_without_verified_license(db):
    db.add(m.Media(slug="foto-teste", kind="photo", title="x", file_url="https://example.org/x.jpg", status="published", license_verified=False))
    with pytest.raises(IntegrityError, match="published_requires_license"):
        db.flush()
