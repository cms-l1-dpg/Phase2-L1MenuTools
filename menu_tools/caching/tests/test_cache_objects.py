import yaml

from menu_tools.caching import cache_objects


def test_configured_read_timeout_is_forwarded(tmp_path, monkeypatch):
    config = {
        "test_version": {
            "test_sample": {
                "ntuple_path": "root://example.invalid/input.root",
                "trees_branches": {"Events": {"TestObject": ["pt"]}},
            }
        }
    }
    config_path = tmp_path / "cache.yaml"
    config_path.write_text(yaml.safe_dump(config))
    monkeypatch.chdir(tmp_path)

    cacher = cache_objects.ObjectCacher(
        version="test_version",
        sample="test_sample",
        obj="TestObject",
        tree="Events",
        branches=["pt"],
        cfg_file=str(config_path),
        read_timeout=123,
    )

    monkeypatch.setattr(
        cache_objects,
        "resolve_input_files",
        lambda input_path: ["root://example.invalid/input.root"],
    )
    iterate_options = []

    def fake_iterate(*args, **kwargs):
        iterate_options.append(kwargs)
        return []

    monkeypatch.setattr(cache_objects.uproot, "iterate", fake_iterate)
    cacher._concat_array_from_ntuples()

    assert iterate_options[0]["timeout"] == 123
