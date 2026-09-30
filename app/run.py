"""Server entry point for Minimals."""
from __future__ import annotations

import os

from waitress import serve

from app.create_app import create_app


def main() -> None:
    # create_app() applies boot-time migrations before seeding, so they must
    # not be run again here.
    app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("PORT", "8000"))
    if debug:
        app.run(host="127.0.0.1", port=port, debug=True)
    else:
        serve(app=app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
