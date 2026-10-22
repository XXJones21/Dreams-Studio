import ast
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "nodes.py").read_text(encoding="utf-8")


def _load(name):
    tree = ast.parse(SRC)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    ns = {"re": __import__("re")}
    exec(compile(ast.Module([fn], []), "nodes.py", "exec"), ns)
    return ns[name]


def test_ordered_clips_sorts_numerically_and_drops_empty():
    ordered = _load("_ordered_clips")
    clips = {"clip10": "k", "clip2": "c", "clip0": "a", "clip1": "b", "clip3": None}
    assert ordered(clips) == ["a", "b", "c", "k"]


def test_ordered_clips_accepts_dotted_keys():
    ordered = _load("_ordered_clips")
    assert ordered({"clips.clip1": "b", "clips.clip0": "a"}) == ["a", "b"]
