import ast
import json

src = open('aiko/dialogue_rules/response_expansions.py', encoding='utf-8').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EXTRA' for t in node.targets):
        print('FOUND EXTRA')
        d = node.value
        print('type:', type(d).__name__, 'num_sections:', len(d.keys))
        data = {}
        for k, v in zip(d.keys, d.values):
            key = ast.literal_eval(k)
            val = ast.literal_eval(v)
            data[key] = val
        out = 'aiko/dialogue_rules/_extra_dump.json'
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('saved:', out)
        print('sections:', list(data.keys()))
