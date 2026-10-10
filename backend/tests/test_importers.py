"""Wikidata mapping logic (offline, with a canned payload)."""

from app.importers.wikidata import WikidataImporter

ENTITY = {
    "labels": {"pt": {"value": "Batalha do Somme"}, "en": {"value": "Battle of the Somme"}},
    "descriptions": {"en": {"value": "battle of World War I"}},
    "claims": {
        "P580": [{"rank": "normal", "mainsnak": {"datavalue": {"value": {"time": "+1916-07-01T00:00:00Z", "precision": 11}}}}],
        "P582": [{"rank": "normal", "mainsnak": {"datavalue": {"value": {"time": "+1916-00-00T00:00:00Z", "precision": 9}}}}],
        "P625": [{"rank": "normal", "mainsnak": {"datavalue": {"value": {"latitude": 50.0155, "longitude": 2.6975}}}}],
    },
}


def test_maps_only_day_precision_dates():
    rec = WikidataImporter(client=object()).map_entity("Q132568", ENTITY, "battle")
    assert rec.proposed["name"] == "Batalha do Somme"
    assert rec.proposed["start_date"] == "1916-07-01"
    assert "end_date" not in rec.proposed, "year-precision dates must not be applied automatically"
    assert any("precisão de ano" in w for w in rec.warnings)
    assert rec.proposed["location"] == [2.6975, 50.0155]
    assert rec.license == "CC0 1.0"
