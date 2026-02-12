import os
import sys
import subprocess
import threading
import webbrowser

try:
    import uvicorn
except ImportError:
    print("=" * 60)
    print("MISSING DEPENDENCIES")
    print("=" * 60)
    print("uvicorn is not installed. Installing dependencies...")
    print()

    installation_methods = [
        (["pip3", "install", "-r", "requirements.txt"], "pip3 install"),
        (["pip", "install", "-r", "requirements.txt"], "pip install"),
        ([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], "python -m pip"),
        (["pip3", "install", "--user", "-r", "requirements.txt"], "pip3 install --user"),
        (["pip", "install", "--user", "-r", "requirements.txt"], "pip install --user"),
    ]

    success = False
    for cmd, desc in installation_methods:
        try:
            print(f"Trying: {desc}...")
            subprocess.check_call(cmd, stderr=subprocess.STDOUT)
            print(f"\n✓ Dependencies installed successfully using {desc}")
            print("Please restart the application.\n")
            success = True
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    if not success:
        print("\n✗ Failed to install dependencies using all methods")
        print("\nPlease install manually using one of these commands:")
        print("  pip install -r requirements.txt")
        print("  pip3 install -r requirements.txt")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
        print()
        sys.exit(1)

    sys.exit(0)

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
