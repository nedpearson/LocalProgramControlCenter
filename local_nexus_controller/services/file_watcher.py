"""
File watcher service for monitoring ZIP files in a folder and auto-importing them.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

from local_nexus_controller.db import engine
from local_nexus_controller.models import ImportBundle
from local_nexus_controller.services.auto_discovery import extract_and_scan_zip
from local_nexus_controller.services.registry_import import import_bundle
from sqlmodel import Session


class FileWatcher:
    """
    Watches a folder for new ZIP files and automatically processes them.
    """

    def __init__(self, watch_folder: str, extract_to: str, check_interval: int = 10):
        self.watch_folder = Path(watch_folder)
        self.extract_to = Path(extract_to)
        self.check_interval = check_interval
        self.processed_files: set[str] = set()
        self.running = False
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        """Start watching the folder in a background thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        print(f"File watcher started: {self.watch_folder}")

    def stop(self) -> None:
        """Stop watching the folder."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("File watcher stopped")

    def _watch_loop(self) -> None:
        """Main loop that checks for new ZIP files."""
        while self.running:
            try:
                self._check_for_zips()
            except Exception as e:
                print(f"File watcher error: {e}")

            time.sleep(self.check_interval)

    def _check_for_zips(self) -> None:
        """Check for new ZIP files and process them."""
        if not self.watch_folder.exists():
            return

        for zip_file in self.watch_folder.glob("*.zip"):
            # Skip if already processed
            if str(zip_file) in self.processed_files:
                continue

            print(f"Found new ZIP file: {zip_file.name}")
            self._process_zip(zip_file)

    def _process_zip(self, zip_path: Path) -> None:
        """Process a single ZIP file."""
        try:
            # Mark as processed immediately to avoid double processing
            self.processed_files.add(str(zip_path))

            # Extract and scan
            bundle = extract_and_scan_zip(zip_path, self.extract_to)

            if bundle:
                # Import to database
                with Session(engine) as session:
                    import_bundle(session, bundle)
                    session.commit()

                print(f"Successfully imported: {bundle.service.name}")

                # Optionally move or delete the ZIP file
                # zip_path.unlink()  # Uncomment to delete after processing

            else:
                print(f"No valid program found in: {zip_path.name}")

        except Exception as e:
            print(f"Failed to process {zip_path.name}: {e}")
            # Remove from processed set so we can retry later
            self.processed_files.discard(str(zip_path))


# Global file watcher instance
_watcher: FileWatcher | None = None


def start_file_watcher(watch_folder: str, extract_to: str) -> None:
    """Start the global file watcher."""
    global _watcher
    if _watcher is None:
        _watcher = FileWatcher(watch_folder, extract_to)
        _watcher.start()


def stop_file_watcher() -> None:
    """Stop the global file watcher."""
    global _watcher
    if _watcher:
        _watcher.stop()
        _watcher = None
