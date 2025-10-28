import pytest
import api_layer

class DummyContext:
    def __init__(
        self,
        user_project="test-project",
        project="test-project",
        location_id="us-central1",
        entry_group_id="egid",
        dc_glossary_id="dcgid",
        dp_glossary_id="glossary1",
        display_name="Test Glossary"
    ):
        self.user_project = user_project
        self.project = project
        self.location_id = location_id
        self.entry_group_id = entry_group_id
        self.dc_glossary_id = dc_glossary_id
        self.dp_glossary_id = dp_glossary_id
        self.display_name = display_name

class DummyEntry:
    def __init__(self, name):
        self.name = name

@pytest.fixture
def context():
    return DummyContext(user_project="test-project")
def dummy_relationships(entry_name, _):
    return [f"relationship_for_{entry_name}"]
def dc_entries():
    return [DummyEntry(name=f"entry_{i}") for i in range(3)]

def dummy_relationships(entry_name, user_project):
    return [f"relationship_for_{entry_name}"]

@pytest.fixture
def dc_entries():
    return [DummyEntry(name=f"entry_{i}") for i in range(3)]

def test_fetch_dc_glossary_taxonomy_relationships_basic(monkeypatch, context, dc_entries):
    # Patch the function used inside
    monkeypatch.setattr(api_layer, "fetch_relationships_dc_glossary_term",
                        lambda name, user_project: dummy_relationships(name, user_project))
    
    # Patch the global constant in api_layer
    monkeypatch.setattr(api_layer, "MAX_WORKERS", 2)

    result = api_layer.fetch_dc_glossary_taxonomy_relationships(context, dc_entries)

    assert isinstance(result, dict)
    monkeypatch.setattr(api_layer, "fetch_relationships_dc_glossary_term", lambda *_: [])
    for entry in dc_entries:
        assert result[entry.name] == [f"relationship_for_{entry.name}"]

def test_fetch_dc_glossary_taxonomy_relationships_exception_handling(monkeypatch, context, dc_entries):
    def side_effect(name, _):
        if name == dc_entries[1].name:
            raise Exception("API error")
        return [f"relationship_for_{name}"]
    monkeypatch.setattr(api_layer, "fetch_relationships_dc_glossary_term", side_effect)
    with pytest.raises(Exception):
        api_layer.fetch_dc_glossary_taxonomy_relationships(context, dc_entries)

def test_fetch_relationships_dc_glossary_entry_basic(monkeypatch):
    # Simulate a single page response with relationships
    dummy_relationships = [{"id": "rel1"}, {"id": "rel2"}]
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {"relationships": dummy_relationships}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_entry_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_entry("entry_1", "test-project")
    assert result == dummy_relationships

def test_fetch_relationships_dc_glossary_entry_empty(monkeypatch):
    # Simulate a response with no relationships
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {"relationships": []}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_entry_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_entry("entry_4", "test-project")
    assert result == []

def test_fetch_relationships_dc_glossary_term_basic(monkeypatch):
    # Simulate a single page response with relationships
    dummy_relationships = [{"id": "rel1"}, {"id": "rel2"}]
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {"relationships": dummy_relationships}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_term("taxonomy_1", "test-project")
    assert result == dummy_relationships

def test_fetch_relationships_dc_glossary_term_pagination(monkeypatch):
    # Simulate two pages of relationships
    responses = [
        {"json": {"relationships": [{"id": "rel1"}], "nextPageToken": "token123"}, "error_msg": None},
        {"json": {"relationships": [{"id": "rel2"}]}, "error_msg": None}
    ]
    call_count = {"count": 0}
    def dummy_fetch_api_response(method, url, user_project):
        resp = responses[call_count["count"]]
        call_count["count"] += 1
        return resp
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_term("taxonomy_2", "test-project")
    assert result == [{"id": "rel1"}, {"id": "rel2"}]

def test_fetch_relationships_dc_glossary_term_error(monkeypatch):
    # Simulate an error response
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {}, "error_msg": "Some error"}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_term("taxonomy_3", "test-project")
    assert result == []

def test_fetch_relationships_dc_glossary_term_empty(monkeypatch):
    # Simulate a response with no relationships
    def dummy_fetch_api_response(*_):
        return {"json": {"relationships": []}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_term("taxonomy_4", "test-project")
    assert result == []

    # Simulate a response with entries
    dummy_entries = [{"id": "entry1"}, {"id": "entry2"}]
    def dummy_entries_api_response(*_):
        return {"json": {"entries": dummy_entries}, "error_msg": None}
    monkeypatch.setattr(api_layer, "_fetch_glossary_taxonomy_entries_page", dummy_entries_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_entries_to_objects", lambda entries: entries)
    result = api_layer.fetch_dc_glossary_taxonomy_entries(DummyContext())
    assert result == dummy_entries

def test_fetch_dc_glossary_taxonomy_entries_pagination(monkeypatch):
    # Simulate two pages of entries
    responses = [
        {"json": {"entries": [{"id": "entry1"}], "nextPageToken": "token123"}, "error_msg": None},
        {"json": {"entries": [{"id": "entry2"}]}, "error_msg": None}
    ]
    call_count = {"count": 0}
    def dummy_fetch_api_response(*_):
        # Prevent IndexError if called more times than responses available
        if call_count["count"] < len(responses):
            resp = responses[call_count["count"]]
            call_count["count"] += 1
            return resp
        return {"json": {"entries": []}, "error_msg": None}
    monkeypatch.setattr(api_layer, "_fetch_glossary_taxonomy_entries_page", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_entries_to_objects", lambda entries: entries)
    result = api_layer.fetch_dc_glossary_taxonomy_entries(DummyContext())
    assert result == [{"id": "entry1"}, {"id": "entry2"}]
    # Reset call_count for repeated test
    call_count["count"] = 0
    result = api_layer.fetch_dc_glossary_taxonomy_entries(DummyContext())
    assert result == [{"id": "entry1"}, {"id": "entry2"}]
    def dummy_fetch_api_response(*_):
        return {"json": {}, "error_msg": "Some error"}
    monkeypatch.setattr(api_layer, "_fetch_glossary_taxonomy_entries_page", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_entries_to_objects", lambda entries: entries)
    with pytest.raises(SystemExit):
        api_layer.fetch_dc_glossary_taxonomy_entries(DummyContext())
        api_layer.fetch_dc_glossary_taxonomy_entries(DummyContext())

def test_fetch_dc_glossary_taxonomy_entries_empty(monkeypatch):
    # Simulate a response with no entries
    def dummy_fetch_api_response(*_):
        return {"json": {"entries": []}, "error_msg": None}
    monkeypatch.setattr(api_layer, "_fetch_glossary_taxonomy_entries_page", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_glossary_taxonomy_entries_to_objects", lambda entries: entries)
    result = api_layer.fetch_dc_glossary_taxonomy_entries(DummyContext())
    assert result == []

def test_discover_glossaries_success(monkeypatch):
    dummy_results = [
        {"searchResultSubtype": "entry.glossary", "linkedResource": "//glossary1"},
        {"searchResultSubtype": "entry.glossary", "linkedResource": "//glossary2"},
        {"searchResultSubtype": "entry.not_glossary", "linkedResource": "//other"}
    ]
    def dummy_fetch_api_response(method, url, user_project, request_body):
        return {"json": {"results": dummy_results}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    def dummy_fetch_api_response(*_):
        return {"json": {"results": dummy_results}, "error_msg": None}
    result = api_layer.discover_glossaries("proj-1", "user-proj")
    assert result == ["https://glossary1", "https://glossary2"]
    monkeypatch.setattr(api_layer.logger, "info", lambda *_: None)

def test_discover_glossaries_error(monkeypatch):
    # Simulate an error response
    def dummy_fetch_api_response(method, url, user_project, request_body):
        return {"json": {}, "error_msg": "API error"}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer.logger, "error", lambda *_: None)
    result = api_layer.discover_glossaries("proj-1", "user-proj")
    assert result == []

def test_discover_glossaries_no_results(monkeypatch):
    # Simulate a response with no results
    def dummy_fetch_api_response(method, url, user_project, request_body):
        return {"json": {"results": []}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer.logger, "warning", lambda *_: None)
    result = api_layer.discover_glossaries("proj-1", "user-proj")
    assert result == []

def test_discover_glossaries_missing_results_key(monkeypatch):
    # Simulate a response with missing 'results' key
    def dummy_fetch_api_response(method, url, user_project, request_body):
        return {"json": {}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    result = api_layer.discover_glossaries("proj-1", "user-proj")
    assert result == []

def test_fetch_relationships_dc_glossary_entry_single_page(monkeypatch):
    # Simulate a single page response with relationships
    dummy_relationships = [{"id": "rel1"}, {"id": "rel2"}]
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {"relationships": dummy_relationships}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_entry_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_entry("entry_1", "test-project")
    assert result == dummy_relationships

def test_fetch_relationships_dc_glossary_entry_pagination(monkeypatch):
    # Simulate two pages of relationships
    responses = [
        {"json": {"relationships": [{"id": "rel1"}], "nextPageToken": "token123"}, "error_msg": None},
        {"json": {"relationships": [{"id": "rel2"}]}, "error_msg": None}
    ]
    call_count = {"count": 0}
    def dummy_fetch_api_response(method, url, user_project):
        resp = responses[call_count["count"]]
        call_count["count"] += 1
        return resp
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_entry_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_entry("entry_2", "test-project")
    assert result == [{"id": "rel1"}, {"id": "rel2"}]

def test_fetch_relationships_dc_glossary_entry_error(monkeypatch):
    # Simulate an error response
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {}, "error_msg": "Some error"}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_entry_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_entry("entry_3", "test-project")
    assert result == []

def test_fetch_relationships_dc_glossary_entry_empty(monkeypatch):
    # Simulate a response with no relationships
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {"relationships": []}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer, "convert_entry_relationships_to_objects", lambda rels: rels)
    result = api_layer.fetch_relationships_dc_glossary_entry("entry_4", "test-project")
    assert result == []

def test_extract_project_number_from_info_success(monkeypatch):
    # Should extract the number from a valid name
    project_info = {"name": "projects/123456789"}
    result = api_layer._extract_project_number_from_info(project_info)
    assert result == "123456789"

def test_extract_project_number_from_info_embedded(monkeypatch):
    # Should extract the number from a name with extra path
    project_info = {"name": "projects/987654321/locations/global"}
    result = api_layer._extract_project_number_from_info(project_info)
    assert result == "987654321"

def test_extract_project_number_from_info_missing_name(monkeypatch):
    # Should call sys.exit(1) if 'name' is missing
    project_info = {}
    monkeypatch.setattr(api_layer.logger, "error", lambda msg: None)
    with pytest.raises(SystemExit):
        api_layer._extract_project_number_from_info(project_info)

def test_extract_project_number_from_info_invalid_name(monkeypatch):
    # Should call sys.exit(1) if name does not contain a project number
    project_info = {"name": "invalid_name"}
    monkeypatch.setattr(api_layer.logger, "error", lambda msg: None)
    with pytest.raises(SystemExit):
        api_layer._extract_project_number_from_info(project_info)

def test__fetch_project_info_success(monkeypatch):
    # Simulate a successful API response
    dummy_json = {"name": "projects/123456789"}
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": dummy_json, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    result = api_layer._fetch_project_info("test-project", "user-project")
    assert result == dummy_json

def test__fetch_project_info_error(monkeypatch):
    # Simulate an error response from the API
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {}, "error_msg": "API error"}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer.logger, "error", lambda msg: None)
    with pytest.raises(SystemExit):
        api_layer._fetch_project_info("test-project", "user-project")

def test__fetch_project_info_empty_json(monkeypatch):
    # Simulate a successful response with empty JSON
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    result = api_layer._fetch_project_info("test-project", "user-project")
    assert result == {}
def test__build_project_url_basic():
    # Should build the correct URL for a simple project ID
    project_id = "my-project"
    expected_url = "https://cloudresourcemanager.googleapis.com/v3/projects/my-project"
    assert api_layer._get_project_url(project_id) == expected_url

def test__build_project_url_with_special_chars():
    # Should handle project IDs with dashes, numbers, and underscores
    project_id = "proj-123_test"
    expected_url = "https://cloudresourcemanager.googleapis.com/v3/projects/proj-123_test"
    assert api_layer._get_project_url(project_id) == expected_url

def test__build_project_url_empty_string():
    # Should handle empty project ID gracefully
    project_id = ""
    expected_url = "https://cloudresourcemanager.googleapis.com/v3/projects/"
    assert api_layer._get_project_url(project_id) == expected_url

def test__build_project_url_numeric_id():
    # Should handle numeric project IDs
    project_id = "123456789"
    expected_url = "https://cloudresourcemanager.googleapis.com/v3/projects/123456789"
    assert api_layer._get_project_url(project_id) == expected_url



def test__fetch_glossary_display_name_success(monkeypatch):
    # Simulate a successful API response with displayName
    dummy_json = {"displayName": "Glossary Display Name"}
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": dummy_json, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    context = DummyContext()
    result = api_layer.fetch_glossary_display_name(context)
    assert result == "Glossary Display Name"

def test__fetch_glossary_display_name_missing_display_name(monkeypatch):
    # Simulate a successful API response without displayName
    dummy_json = {}
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": dummy_json, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    context = DummyContext()
    result = api_layer.fetch_glossary_display_name(context)
    assert result == context.dp_glossary_id

def test__fetch_glossary_display_name_error(monkeypatch):
    # Simulate an error response from the API
    def dummy_fetch_api_response(method, url, user_project):
        return {"json": {}, "error_msg": "API error"}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    monkeypatch.setattr(api_layer.logger, "error", lambda msg: None)
    context = DummyContext()
    with pytest.raises(SystemExit):
        api_layer.fetch_glossary_display_name(context)

def test__build_dataplex_lookup_entry_url_basic():
    class DummySearchEntryResult:
        linkedResource = "//my-entry-id"
        relativeResourceName = "projects/proj-1/locations/us-central1/entryGroups/egid/entries/old-id"
    result = api_layer._build_dataplex_lookup_entry_url(DummySearchEntryResult())
    expected_url = (
        "https://dataplex.googleapis.com/v1/projects/proj-1/locations/us-central1:lookupEntry"
        "?entry=projects/proj-1/locations/us-central1/entryGroups/egid/entries/my-entry-id"
    )
    assert result == expected_url

def test__build_dataplex_lookup_entry_url_leading_slashes():
    class DummySearchEntryResult:
        linkedResource = "///new-id"
        relativeResourceName = "projects/proj-2/locations/europe-west1/entryGroups/egid/entries/old-id"
    result = api_layer._build_dataplex_lookup_entry_url(DummySearchEntryResult())
    expected_url = (
        "https://dataplex.googleapis.com/v1/projects/proj-2/locations/europe-west1:lookupEntry"
        "?entry=projects/proj-2/locations/europe-west1/entryGroups/egid/entries/new-id"
    )
    assert result == expected_url

def test__build_dataplex_lookup_entry_url_no_match():
    class DummySearchEntryResult:
        linkedResource = "/entry-id"
        relativeResourceName = "invalid/resource/name/entries/old-id"
    result = api_layer._build_dataplex_lookup_entry_url(DummySearchEntryResult())
    expected_url = (
        "https://dataplex.googleapis.com/v1/:lookupEntry"
        "?entry=invalid/resource/name/entries/entry-id"
    )
    assert result == expected_url

def test__build_dataplex_lookup_entry_url_complex_linked_resource():
    class DummySearchEntryResult:
        linkedResource = "//complex-id-123_ABC"
        relativeResourceName = "projects/proj-3/locations/asia-east1/entryGroups/egid/entries/old-id"
    result = api_layer._build_dataplex_lookup_entry_url(DummySearchEntryResult())
    expected_url = (
        "https://dataplex.googleapis.com/v1/projects/proj-3/locations/asia-east1:lookupEntry"
        "?entry=projects/proj-3/locations/asia-east1/entryGroups/egid/entries/complex-id-123_ABC"
    )
    assert result == expected_url

def test_create_dataplex_glossary_already_exists(monkeypatch):
    # Simulate glossary already exists (409 error)
    called = {}
    def dummy_post_dataplex_glossary(context):
        return {"json": {"error": {"code": 409, "status": "ALREADY_EXISTS"}}, "error_msg": None}
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary", dummy_post_dataplex_glossary)
    monkeypatch.setattr(api_layer, "_is_glossary_already_exists", lambda resp: True)
    monkeypatch.setattr(api_layer.logger, "info", lambda msg: called.setdefault("info", msg))
    context = DummyContext()
    api_layer.create_dataplex_glossary(context)
    assert "already exists" in called.get("info", "")

def test_create_dataplex_glossary_success(monkeypatch):
    # Simulate successful creation (no error_msg)
    called = {}
    def dummy_post_dataplex_glossary(context):
        return {"json": {"result": "ok"}, "error_msg": None}
    def dummy_is_glossary_already_exists(resp):
        return False
    def dummy_get_dataplex_glossary(context):
        return {"json": {"displayName": context.display_name}, "error_msg": None}
    def dummy_handle_dataplex_glossary_response(api_response, context):
        called["handled"] = (api_response, context)
        
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary", dummy_post_dataplex_glossary)
    monkeypatch.setattr(api_layer, "_is_glossary_already_exists", dummy_is_glossary_already_exists)
    monkeypatch.setattr(api_layer, "_get_dataplex_glossary", dummy_get_dataplex_glossary)
    monkeypatch.setattr(api_layer, "_handle_dataplex_glossary_response", dummy_handle_dataplex_glossary_response)
    monkeypatch.setattr(api_layer.logger, "info", lambda msg: called.setdefault("info", msg))
    monkeypatch.setattr(api_layer, "time", type("T", (), {"sleep": lambda s, *_: called.setdefault("slept", s)})())
    context = DummyContext()
    api_layer.create_dataplex_glossary(context)
    assert "creation initiated" in called.get("info", "")
    assert called.get("handled")[1].display_name == context.display_name

def test_create_dataplex_glossary_error(monkeypatch):
    # Simulate error in Dataplex API response
    called = {}
    def dummy_post_dataplex_glossary(context):
        return {"json": {}, "error_msg": "API error"}
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary", dummy_post_dataplex_glossary)
    monkeypatch.setattr(api_layer, "_is_glossary_already_exists", lambda resp: False)
    monkeypatch.setattr(api_layer.logger, "error", lambda msg: called.setdefault("error", msg))
    context = DummyContext()
    api_layer.create_dataplex_glossary(context)
    assert "Unexpected response" in called.get("error", "")

def test_create_dataplex_glossary_calls_all_helpers(monkeypatch):
    # Ensure all helpers are called in the happy path
    called = {"post": False, "is_exists": False, "get": False, "handle": False, "sleep": False, "info": False}
    def dummy_post_dataplex_glossary(context):
        called["post"] = True
        return {"json": {"result": "ok"}, "error_msg": None}
    def dummy_is_glossary_already_exists(resp):
        called["is_exists"] = True
        return False
    def dummy_get_dataplex_glossary(context):
        called["get"] = True
        return {"json": {"displayName": context.display_name}, "error_msg": None}
    def dummy_handle_dataplex_glossary_response(api_response, display_name):
        called["handle"] = True
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary", dummy_post_dataplex_glossary)
    monkeypatch.setattr(api_layer, "_is_glossary_already_exists", dummy_is_glossary_already_exists)
    monkeypatch.setattr(api_layer, "_get_dataplex_glossary", dummy_get_dataplex_glossary)
    monkeypatch.setattr(api_layer, "_handle_dataplex_glossary_response", dummy_handle_dataplex_glossary_response)
    monkeypatch.setattr(api_layer.logger, "info", lambda msg: called.__setitem__("info", True))
    monkeypatch.setattr(api_layer, "time", type("T", (), {"sleep": lambda s, *_: called.__setitem__("sleep", True)})())
    context = DummyContext()
    api_layer.create_dataplex_glossary(context)
    assert all(called.values())

def test__post_dataplex_glossary_success(monkeypatch):
    # Simulate a successful API response
    called = {}
    def dummy_post_dataplex_glossary_url(context):
        called["url"] = f"url_for_{context.dp_glossary_id}"
        return called["url"]
    def dummy_trim_spaces_in_display_name(display_name):
        called["trimmed"] = display_name.strip()
        return display_name.strip()
    def dummy_fetch_api_response(method, url, user_project, request_body):
        called["method"] = method
        called["url2"] = url
        called["user_project"] = user_project
        called["request_body"] = request_body
        return {"json": {"result": "ok"}, "error_msg": None}
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary_url", dummy_post_dataplex_glossary_url)
    monkeypatch.setattr(api_layer, "trim_spaces_in_display_name", dummy_trim_spaces_in_display_name)
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    context = DummyContext(project="proj", dp_glossary_id="glossary1", user_project="user-proj", display_name="  My Glossary  ")
    result = api_layer._post_dataplex_glossary(context)
    assert result == {"json": {"result": "ok"}, "error_msg": None}
    assert called["url"] == "url_for_glossary1"
    assert called["trimmed"] == "My Glossary"
    assert called["url2"] == "url_for_glossary1"
    assert called["user_project"] == "user-proj"
    assert called["request_body"] == {"displayName": "My Glossary"}

def test__post_dataplex_glossary_error(monkeypatch):
    # Simulate an error API response
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary_url", lambda context: "dummy_url")
    monkeypatch.setattr(api_layer, "trim_spaces_in_display_name", lambda display_name: display_name)
    def dummy_fetch_api_response(method, url, user_project, request_body):
        return {"json": {}, "error_msg": "API error"}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    context = DummyContext(project="proj", dp_glossary_id="glossary1", user_project="user-proj", display_name="Glossary")
    result = api_layer._post_dataplex_glossary(context)
    assert result == {"json": {}, "error_msg": "API error"}

def test__post_dataplex_glossary_display_name_trim(monkeypatch):
    # Ensure display name is trimmed before sending
    monkeypatch.setattr(api_layer, "_post_dataplex_glossary_url", lambda context: "dummy_url")
    monkeypatch.setattr(api_layer, "trim_spaces_in_display_name", lambda display_name: display_name.strip())
    captured = {}
    def dummy_fetch_api_response(method, url, user_project, request_body):
        captured["request_body"] = request_body
        return {"json": {"result": "ok"}, "error_msg": None}
    monkeypatch.setattr(api_layer.api_call_utils, "fetch_api_response", dummy_fetch_api_response)
    context = DummyContext(project="proj", dp_glossary_id="glossary1", user_project="user-proj", display_name="   Glossary Name   ")
    api_layer._post_dataplex_glossary(context)
    assert captured["request_body"]["displayName"] == "Glossary Name"
