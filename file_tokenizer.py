"""Generate ACTG tokens for files in the repository.

Usage:
    python file_tokenizer.py [--length N] [--paths path1 path2 ...]

By default walks current project folder (script's parent) and prints token for each file.
"""
import argparse
import os
from pathlib import Path
from dna_utils import generate_actg_token_for_file

EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules'}
EXCLUDE_FILES = {'registry.csv', 'flask_app.log'}


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn in EXCLUDE_FILES:
                continue
            yield Path(dirpath) / fn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--length', type=int, default=32, help='Number of ACTG bases to output')
    parser.add_argument('--paths', nargs='*', help='Optional list of files or folders to include')
    args = parser.parse_args()

    base = Path(__file__).parent
    targets = []
    if args.paths:
        for p in args.paths:
            pth = Path(p)
            if not pth.is_absolute():
                pth = (base / pth).resolve()
            targets.append(pth)
    else:
        targets = [base]

    seen = []
    for t in targets:
        if t.is_file():
            seen.append(t)
        else:
            for f in iter_files(t):
                seen.append(f)

    for p in sorted(seen):
        try:
            tok = generate_actg_token_for_file(str(p), length=args.length)
            print(f"{p.relative_to(base)}\t{tok}")
        except Exception as e:
            print(f"{p.relative_to(base)}\tERROR: {e}")


if __name__ == '__main__':
    main()
