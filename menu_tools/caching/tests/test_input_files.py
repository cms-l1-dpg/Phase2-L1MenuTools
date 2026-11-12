from menu_tools.caching.input_files import resolve_input_files


def test_resolve_local_file(tmp_path):
    input_file = tmp_path / "input.root"
    input_file.touch()

    assert resolve_input_files(str(input_file)) == [str(input_file)]


def test_resolve_local_glob_is_sorted(tmp_path):
    second = tmp_path / "second.root"
    first = tmp_path / "first.root"
    second.touch()
    first.touch()

    assert resolve_input_files(str(tmp_path / "*.root")) == [str(first), str(second)]


def test_resolve_missing_or_empty_input(tmp_path):
    assert resolve_input_files("") == []
    assert resolve_input_files(str(tmp_path / "*.root")) == []
