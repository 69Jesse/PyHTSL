import importlib.util
import sys
import time
import traceback
import warnings
from pathlib import Path

# Test the repo's pyhtsw, not whatever happens to be installed: running as
# `python3 tests/main.py` puts tests/ (not the repo root) on sys.path, which
# silently resolves `import pyhtsw` to site-packages.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pyhtsw import PyHTSWWarning, disable_global_export

disable_global_export()
warnings.simplefilter('error', PyHTSWWarning)
warnings.filterwarnings(
    'ignore',
    message='Actions were written outside',
    category=PyHTSWWarning,
)


def _fmt(seconds: float) -> str:
    if seconds < 1e-3:
        return f'{seconds * 1e6:.0f}us'
    if seconds < 1:
        return f'{seconds * 1e3:.0f}ms'
    return f'{seconds:.2f}s'


def main() -> int:
    here = Path(__file__).parent
    test_files = sorted(p for p in here.glob('test_*.py'))
    if not test_files:
        print('No tests found.')
        return 0

    failures: list[tuple[str, str]] = []
    total_start = time.perf_counter()
    for path in test_files:
        name = path.stem
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        start = time.perf_counter()
        try:
            spec.loader.exec_module(module)
        except SystemExit as error:
            # A test calling sys.exit would otherwise take the runner with it,
            # silently skipping every file sorting after it.
            if error.code not in (None, 0):
                elapsed = time.perf_counter() - start
                failures.append((name, f'sys.exit({error.code!r})'))
                print(f'FAIL {name} ({_fmt(elapsed)})')
                continue
        except Exception:
            elapsed = time.perf_counter() - start
            failures.append((name, traceback.format_exc()))
            print(f'FAIL {name} ({_fmt(elapsed)})')
            continue
        elapsed = time.perf_counter() - start
        print(f'PASS {name} ({_fmt(elapsed)})')

    total_elapsed = time.perf_counter() - total_start
    print()
    print(
        f'{len(test_files) - len(failures)}/{len(test_files)} passed in {_fmt(total_elapsed)}',
    )
    for name, tb in failures:
        print(f'\n--- {name} ---')
        print(tb)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
