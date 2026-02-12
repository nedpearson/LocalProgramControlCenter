import os
import threading
import uvicorn
import webbrowser

from local_nexus_controller.settings import settings


def main() -> None:
    if settings.open_browser and os.environ.get("LOCAL_NEXUS_BROWSER_OPENED") != "1":
        # Prevent multiple opens when uvicorn reload spawns a child process.
        os.environ["LOCAL_NEXUS_BROWSER_OPENED"] = "1"

        def _open() -> None:
            host = settings.host
            # Browsers can't navigate to 0.0.0.0; use loopback for local convenience.
            if host in {"0.0.0.0", "::"}:
                host = "127.0.0.1"
            url = f"http://{host}:{settings.port}/"
            webbrowser.open(url, new=2)

        threading.Timer(0.75, _open).start()

    reload_dirs = [str(settings.project_root / "local_nexus_controller")]

    uvicorn.run(
        "local_nexus_controller.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        reload_dirs=reload_dirs if settings.reload else None,
        reload_includes=["*.py", "*.html", "*.css", "*.js"] if settings.reload else None,
    )


if __name__ == "__main__":
    main()
