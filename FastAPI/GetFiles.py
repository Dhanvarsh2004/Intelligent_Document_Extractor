from pathlib import Path

INPUT_FOLDER = Path(__file__).resolve().parent.parent /"Documents"/"Available_Documents"

def read_name(file_name):
    # Your logic to extract the fund name
    # Example:
    return file_name.split("_")[0]

def get_files():
    files = []

    for file_path in INPUT_FOLDER.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".pdf":

            fund_name = read_name(file_path.name)
            print(file_path.name)

            files.append({
                "file_path": str(file_path),
                "fund_name": fund_name
            })

    return files