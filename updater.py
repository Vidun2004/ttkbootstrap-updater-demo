import requests
import threading
import subprocess
import tempfile
import os
import sys
import certifi
from packaging.version import Version

# Fix SSL certificates for PyInstaller bundles
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/Vidun2004/ttkbootstrap-updater-demo/main/release/version.json"


def get_resource_path(relative_path):
    """Get correct path whether running as script or PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_local_version():
    import json
    try:
        path = get_resource_path("version.json")
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def check_for_update(on_update_available, on_error=None):
    def _check():
        try:
            response = requests.get(UPDATE_MANIFEST_URL, timeout=10)
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

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


def download_and_install(url, progress_callback=None, done_callback=None, error_callback=None):
    def _download():
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            suffix = ".exe" if url.endswith(".exe") else ".tmp"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

            with tmp as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total:
                            pct = int((downloaded / total) * 100)
                            progress_callback(pct)

            if done_callback:
                done_callback(tmp.name)

            subprocess.Popen([tmp.name])

        except Exception as e:
            if error_callback:
                error_callback(str(e))

    thread = threading.Thread(target=_download, daemon=True)
    thread.start()