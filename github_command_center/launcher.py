from __future__ import annotations

import sys


def main() -> int:
    try:
        from .app import main as app_main
    except ImportError:
        from .app import GitHubCommandCenter
        app = GitHubCommandCenter()
        app.mainloop()
        return 0
    result = app_main()
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
