import importlib.util
import sys
import traceback
from pathlib import Path

from pyhtsl import disable_global_export

disable_global_export()


def main() -> int:
    here = Path(__file__).parent
    test_files = sorted(p for p in here.glob('test_*.py'))
    if not test_files:
        print('No tests found.')
        return 0

    failures: list[tuple[str, str]] = []
    for path in test_files:
        name = path.stem
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            failures.append((name, traceback.format_exc()))
            print(f'FAIL {name}')
            continue
        print(f'PASS {name}')

    print()
    print(f'{len(test_files) - len(failures)}/{len(test_files)} passed')
    for name, tb in failures:
        print(f'\n--- {name} ---')
        print(tb)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
