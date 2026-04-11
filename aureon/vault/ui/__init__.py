"""
Aureon Vault UI — Flask interface for communicating with the vault.

Usage:
    from aureon.vault.ui import create_app, run_server

    # As a standalone server:
    run_server(host="127.0.0.1", port=5566, start_loop=True)

    # Embedded in an existing Flask app:
    from aureon.vault import AureonSelfFeedbackLoop
    loop = AureonSelfFeedbackLoop()
    app = create_app(loop=loop)
"""

from aureon.vault.ui.server import create_app, run_server

__all__ = ["create_app", "run_server"]
