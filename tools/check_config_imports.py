#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
`from config import X` ifadelerinin gerçekten config.py'de tanımlı bir ada
işaret ettiğini doğrular.

Neden ayrı bir kontrol: config.py'deki global hisse listesi kullanıcı bazlı
veritabanına taşındığında arge_sinyali.py'de kalan `from config import TICKERS`
satırı fark edilmedi. Bu modül sadece elle çalıştırıldığı için hata aylarca
görünmez kaldı — bağımlılık kurmayı gerektirmeyen bu statik kontrol, aynı
sınıftan hataları CI'da anında yakalar.

Kullanım:
    python tools/check_config_imports.py
"""

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def config_level_names(config_path: pathlib.Path) -> set:
    tree = ast.parse(config_path.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def main() -> int:
    defined = config_level_names(ROOT / "config.py")
    problems = []

    for path in sorted(ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "config":
                for alias in node.names:
                    if alias.name not in defined:
                        problems.append((path.name, node.lineno, alias.name))

    if problems:
        print("HATA: config.py'de tanımlı olmayan adlar içe aktarılıyor:\n")
        for filename, lineno, name in problems:
            print(f"  {filename}:{lineno}  from config import {name}")
        print(f"\n{len(problems)} sorun bulundu.")
        return 1

    print("Tüm `from config import ...` ifadeleri geçerli.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
