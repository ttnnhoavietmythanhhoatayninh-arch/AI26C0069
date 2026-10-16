"""Compatibility entrypoint; all configuration comes from CLI/environment."""
from main import main
if __name__ == '__main__':
    raise SystemExit(main())
