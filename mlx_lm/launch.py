# Copyright © 2026 Apple Inc.

from .launcher.cli import main

if __name__ == "__main__":
    print(
        "Calling `python -m mlx_lm.launch...` directly is deprecated."
        " Use `mlx_lm.launch...` or `python -m mlx_lm launch ...` instead."
    )
    main()
