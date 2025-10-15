"""CLI entry point for CMUS Rich."""

import argparse
import asyncio
import sys
from pathlib import Path

from cmus_rich.core.app import CMUSRichApp


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CMUS Rich - A modern, feature-rich terminal music player"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to configuration file",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    args = parser.parse_args()

    if args.version:
        from cmus_rich import __version__

        print(f"CMUS Rich version {__version__}")
        sys.exit(0)

    # Create and run application
    app = CMUSRichApp(config_path=args.config)

    if args.debug:
        app.config.log_level = "DEBUG"

    try:
        asyncio.run(app_main(app))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


async def app_main(app: CMUSRichApp) -> None:
    """Async main function."""
    await app.initialize()
    await app.run()


if __name__ == "__main__":
    main()
