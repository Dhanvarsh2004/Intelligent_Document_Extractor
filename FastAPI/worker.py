from pathlib import Path
import subprocess
import sys

from GetFiles import get_files

MAIN_FILE = Path(__file__).parent.parent / "main.py"

files = get_files()

for file in files:

    subprocess.run(
        [
            sys.executable,
            str(MAIN_FILE),
            file["file_path"],
            file["fund_name"]
        ]
    )
