"""Run trusted desktop parser functions without starting Qt or accessing its DB.

Default: compare against frozen outputs. --capture-reference creates new outputs
exclusively (never overwrites); their functional approval remains pending.
"""
import argparse
import ast
import calendar
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import unicodedata

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def desktop_functions(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    namespace = dict(re=re, Decimal=Decimal, ROUND_HALF_UP=ROUND_HALF_UP,
                     datetime=datetime, calendar=calendar, unicodedata=unicodedata,
                     Path=Path, os=os, shutil=shutil)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def normalized(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def totals(output):
    people = output['colaboradores']
    rubrics = [r for p in people for r in p['rubricas']]
    return dict(employees=len(people), payroll_lines=len(rubrics),
                by_type={t: str(sum((Decimal(r['valor']) for r in rubrics if r['tipo'] == t), Decimal('0')))
                         for t in sorted({r['tipo'] for r in rubrics})},
                net=str(sum((Decimal(p['liquido']) for p in people), Decimal('0'))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desktop-source', type=Path, required=True)
    parser.add_argument('--capture-reference', action='store_true')
    args = parser.parse_args()
    source = args.desktop_source
    functions = desktop_functions(source)
    for case in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith('extrato_')):
        entry = next(case.glob('input.*'))
        fn = 'parse_pdf' if entry.suffix == '.pdf' else 'parse_excel'
        observed = normalized(functions[fn](str(entry)))
        if args.capture_reference:
            if (case / 'manifest.json').exists():
                print(f'{case.name}: existing reference preserved')
                continue
            # Independent arithmetic/identity sanity checks before freezing desktop output.
            empty = case.name.endswith('_empty')
            assert len(observed['colaboradores']) == (0 if empty else 2), case.name
            if not empty:
                assert observed['competencia'] == '09/2026', case.name
                assert [p['nome'] for p in observed['colaboradores']] == ['ANA SINTÉTICA', 'JOÃO FICTÍCIO']
                assert totals(observed)['net'] == '4500.00'
                if case.name == 'extrato_pdf_accent':
                    assert 'P' not in totals(observed)['by_type']
                else:
                    assert Decimal(totals(observed)['by_type']['P']) == Decimal('5000')
                assert Decimal(totals(observed)['by_type']['D']) == Decimal('479' if case.name.endswith('_edge') else '500')
                assert totals(observed)['payroll_lines'] == (2 if case.name == 'extrato_pdf_accent' else 6 if case.name.endswith('_edge') else 4)
            expected = case / 'expected.json'
            with expected.open('x', encoding='utf-8') as f:
                json.dump(observed, f, ensure_ascii=False, indent=2)
                f.write('\n')
            manifest = dict(schema_version=1, case_id=case.name, provenance='entirely_synthetic',
                            approval='pending_functional_and_windows_review',
                            reference=dict(desktop_version='2.18', source_sha256=sha(source), function=fn,
                                           os=platform.system(), python=platform.python_version(),
                                           libraries={n: importlib.metadata.version(n) for n in ['pdfplumber','python-calamine']}),
                            input=dict(file=entry.name, sha256=sha(entry)),
                            expected=dict(file=expected.name, sha256=sha(expected), totals=totals(observed)),
                            comparison='ordered full JSON; Decimal serialized as text; no rounding tolerance',
                            context=dict(company='synthetic_901', competence=observed['competencia'],
                                         database='none', clock='not_used', configuration='parser_only'),
                            txt_reference=None,
                            notes=['No operational data or original document content copied.',
                                   'PDF/Excel parser stage only; no persistence, export or GUI executed.'])
            with (case / 'manifest.json').open('x', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
                f.write('\n')
        else:
            manifest = json.loads((case / 'manifest.json').read_text(encoding='utf-8'))
            assert sha(source) == manifest['reference']['source_sha256'], 'Desktop source differs from reference'
            assert sha(entry) == manifest['input']['sha256'], f'{case.name}: input changed'
            expected = case / manifest['expected']['file']
            assert sha(expected) == manifest['expected']['sha256'], f'{case.name}: expected changed'
            assert observed == json.loads(expected.read_text(encoding='utf-8')), f'{case.name}: desktop output differs'
        print(f'{case.name}: OK ({totals(observed)["employees"]} employees, {totals(observed)["payroll_lines"]} lines)')


if __name__ == '__main__':
    main()
