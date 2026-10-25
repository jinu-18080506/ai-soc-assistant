from soc.state import ProcessedStore


def test_new_store_is_empty(tmp_path):
    assert not ProcessedStore(tmp_path / "s.json").is_processed("a")


def test_mark_persists_across_instances(tmp_path):
    path = tmp_path / "s.json"
    ProcessedStore(path).mark("a")
    assert ProcessedStore(path).is_processed("a")


def test_creates_missing_parent_folder(tmp_path):
    store = ProcessedStore(tmp_path / "deep" / "dir" / "s.json")
    store.mark("a")
    assert (tmp_path / "deep" / "dir" / "s.json").exists()


def test_corrupt_file_starts_empty_instead_of_crashing(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{{{ not json", encoding="utf-8")
    assert not ProcessedStore(path).is_processed("a")
