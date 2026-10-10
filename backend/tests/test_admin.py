"""Administrative workflow: authentication, validation, duplicates, review and publication."""

API = "/api/v1"


def test_admin_requires_authentication(client):
    assert client.get(f"{API}/admin/meta").status_code == 401
    assert client.post(f"{API}/admin/battle", json={"values": {}}).status_code == 401


def test_invalid_login(client):
    r = client.post(f"{API}/auth/login", data={"username": "ninguem@x.org", "password": "errada"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"


def test_meta_lists_editable_fields(client, auth_headers):
    meta = client.get(f"{API}/admin/meta", headers=auth_headers("editor")).json()
    unit = next(e for e in meta["entities"] if e["key"] == "unit")
    names = {f["name"] for f in unit["fields"]}
    assert {"name", "echelon", "polity_id", "formed_on"} <= names


def test_validation_errors_are_field_level(client, auth_headers):
    r = client.post(f"{API}/admin/person", headers=auth_headers("editor"),
                    json={"values": {"name": "Pessoa Teste", "birth_date": "1900-13-40", "wikidata_id": "abc"}})
    assert r.status_code == 422
    fields = {d["field"] for d in r.json()["error"]["details"]}
    assert {"birth_date", "wikidata_id"} <= fields


def test_inverted_dates_rejected_before_db(client, auth_headers):
    r = client.post(f"{API}/admin/person", headers=auth_headers("editor"),
                    json={"values": {"name": "Pessoa Datas", "birth_date": "1900-01-01", "death_date": "1890-01-01"}})
    assert r.status_code == 422 and r.json()["error"]["details"][0]["field"] == "death_date"


def test_duplicate_detection(client, auth_headers):
    h = auth_headers("editor")
    r = client.post(f"{API}/admin/person", headers=h, json={"values": {"name": "Douglas Haig"}})
    assert r.status_code == 409 and r.json()["error"]["code"] == "possible_duplicate"
    assert any(c["slug"] == "douglas-haig" for c in r.json()["error"]["details"])
    r = client.post(f"{API}/admin/person", headers=h, json={"values": {"name": "Douglas Haig"}, "confirm_duplicate": True})
    assert r.status_code == 201 and r.json()["values"]["slug"] == "douglas-haig-2"


def test_full_review_workflow(client, auth_headers):
    editor, reviewer = auth_headers("editor"), auth_headers("reviewer")
    r = client.post(f"{API}/admin/person", headers=editor, json={"values": {"name": "Pessoa Fluxo Teste Única"}, "comment": "teste"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["values"]["status"] == "draft"
    # drafts are invisible to the public
    assert client.get(f"{API}/persons/pessoa-fluxo-teste-unica").status_code == 404
    # editor submits for review but cannot publish
    assert client.post(f"{API}/admin/person/{pid}/status", headers=editor, json={"status": "in_review"}).status_code == 200
    assert client.post(f"{API}/admin/person/{pid}/status", headers=editor, json={"status": "published"}).status_code == 403
    queue = client.get(f"{API}/admin/review-queue", headers=reviewer).json()
    assert any(i["entity"] == "person" and i["id"] == pid for i in queue)
    # publishing without a source is blocked
    r = client.post(f"{API}/admin/person/{pid}/status", headers=reviewer, json={"status": "published"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "citation_required"
    src = client.get(f"{API}/admin/lookup/source", headers=reviewer, params={"q": "Wikidata"}).json()[0]
    r = client.post(f"{API}/admin/citation", headers=reviewer, json={"values": {"source_id": src["id"], "entity_type": "person", "entity_id": pid}})
    assert r.status_code == 201
    assert client.post(f"{API}/admin/person/{pid}/status", headers=reviewer, json={"status": "published"}).status_code == 200
    assert client.get(f"{API}/persons/pessoa-fluxo-teste-unica").status_code == 200
    # editors cannot modify published records
    r = client.patch(f"{API}/admin/person/{pid}", headers=editor, json={"values": {"summary": "x"}})
    assert r.status_code == 403
    revs = client.get(f"{API}/admin/revisions", headers=reviewer, params={"entity": "person", "entity_id": pid}).json()
    assert {x["action"] for x in revs} >= {"create", "status"}


def test_temporal_conflict_reported_as_409(client, auth_headers):
    h = auth_headers("admin")
    unit = client.get(f"{API}/admin/lookup/unit", headers=h, params={"q": "26ª Divisão"}).json()[0]
    parent = client.get(f"{API}/admin/lookup/unit", headers=h, params={"q": "2º Exército (Império"}).json()[0]
    r = client.post(f"{API}/admin/unit_subordination", headers=h, json={"values": {
        "unit_id": unit["id"], "parent_unit_id": parent["id"], "relation": "organic", "valid_from": "1916-07-01", "valid_to": "1916-07-01"}})
    assert r.status_code == 409 and "Sobreposição temporal" in r.json()["error"]["message"]


def test_import_staging_requires_review(client, auth_headers):
    h = auth_headers("reviewer")
    r = client.post(f"{API}/admin/imports/batch", headers=h, json={
        "entity_type": "place", "source_name": "teste-lote",
        "records": [{"external_id": "x1", "name": "Localidade Importada", "geom": [2.0, 49.0]}]})
    assert r.status_code == 201
    recs = client.get(f"{API}/admin/imports/records", headers=h, params={"status": "pending"}).json()
    rec = next(x for x in recs if x["external_source"] == "teste-lote")
    r = client.post(f"{API}/admin/imports/records/{rec['id']}/approve", headers=h, json={})
    assert r.status_code == 200
    created = client.get(f"{API}/admin/place/{r.json()['id']}", headers=h).json()
    assert "requer revisão" in created["values"]["provenance_note"]


def test_wikidata_import_disabled_in_tests(client, auth_headers):
    r = client.post(f"{API}/admin/imports/wikidata", headers=auth_headers("editor"), json={"qid": "Q132568", "entity_type": "battle"})
    assert r.status_code == 503
