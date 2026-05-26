import requests
import threading
import subprocess
import tempfile
import os
from packaging.version import Version

# This URL points to YOUR hosted version.json
# For now we'll use a placeholder — you'll replace this after GitHub setup
UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/release/version.json"

LOCAL_VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")


def get_local_version():
    import json
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def check_for_update(on_update_available, on_error=None):
    """
    Runs in a background thread.
    Calls on_update_available(latest_version, download_url, release_notes)
    if a newer version exists.
    """
    def _check():
        try:
            response = requests.get(UPDATE_MANIFEST_URL, timeout=5)
            response.raise_for_status()
            data = response.json()

            latest = data.get("latest", "0.0.0")
            url = data.get("url", "")
            notes = data.get("notes", "")

            local = get_local_version()

            if Version(latest) > Version(local):
                on_update_available(latest, url, notes)
        except Exception as e:
            if on_error:
                on_error(str(e))

    t = threading.Thread(target=_check, daemon=True)
    t.start()


def download_and_install(url, on_progress, on_done, on_error):
    """
    Downloads the installer to a temp file and runs it.
    on_progress(percent_int) called during download.
    on_done() called when installer launched.
    on_error(message) called on failure.
    """
    def _download():
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            suffix = ".exe" if os.name == "nt" else ".sh"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = int((downloaded / total) * 100)
                        on_progress(percent)

            tmp.close()

            # Make executable on non-windows
            if os.name != "nt":
                os.chmod(tmp.name, 0o755)

            # Launch the installer
            subprocess.Popen([tmp.name])
            on_done()

        except Exception as e:
            on_error(str(e))

    t = threading.Thread(target=_download, daemon=True)
    t.start()