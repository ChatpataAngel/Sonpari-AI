from aiko.local_memory import LocalMemory


def test_local_memory_persists_and_forgets(tmp_path):
    path=tmp_path/"memory.json"
    store=LocalMemory(path)
    changes=store.remember("my favorite color is blue")
    assert changes
    assert store.all()["color"] == "blue"
    again=LocalMemory(path)
    assert again.all()["color"] == "blue"
    again.forget()
    assert again.all() == {}
