#!/usr/bin/env python3
"""Extract the #641 read decisions and call sites without running product code."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


def inspect(root):
    selections = {
        'board/board_data.py': {'finished', 'plan_read', 'answer', 'handle'},
        'skills/dispatch/scripts/status.py': {'print_summary', 'batch_children'},
    }
    relevant = {'read_ticket', 'batch_children', 'spec_tree',
                'self._read_trees', 'comment_reader.read', 'STORE.answer'}
    result = []
    for relative, names in selections.items():
        path = root / 'mmw-v4' / relative
        source = path.read_text()
        entry = {'file': str(path), 'sha256': hashlib.sha256(source.encode()).hexdigest(),
                 'functions': []}
        for function in ast.walk(ast.parse(source)):
            if not isinstance(function, ast.FunctionDef) or function.name not in names:
                continue
            calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)
                     and ast.unparse(node.func) in relevant]
            item = {'name': function.name, 'line': function.lineno,
                    'calls': [{'line': call.lineno, 'source': ast.unparse(call)}
                              for call in sorted(calls, key=lambda node: node.lineno)]}
            if function.name in {'finished', 'plan_read'}:
                item['definition'] = ast.unparse(function)
            entry['functions'].append(item)
        result.append(entry)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.checkout.resolve()), ensure_ascii=False, indent=2))
