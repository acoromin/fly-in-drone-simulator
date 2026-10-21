import sys
from pathlib import Path

import pygame

from renderer.application import Application


def main() -> int:
    """Open the map library or an optional map passed on the command line."""
    if len(sys.argv) > 2:
        print(f'Usage: python3 {sys.argv[0]} [map_file]', file=sys.stderr)
        return 1
    try:
        path = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
        Application(path).run()
        return 0
    except pygame.error as error:
        print(f'Graphics error: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nSimulation interrupted.', file=sys.stderr)
        return 130
    finally:
        pygame.quit()


if __name__ == '__main__':
    raise SystemExit(main())
