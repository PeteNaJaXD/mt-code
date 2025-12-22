import os
from typing import List


def read_file(file_path: str) -> str:
    """Read a file and return its contents.

    Args:
        file_path: Path to the file to read.

    Returns:
        The file contents as a string, or a placeholder for binary files.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        # File is not valid UTF-8 (likely a binary file)
        return "[Binary file - cannot be displayed as text]"
    except Exception as e:
        return f"[Error reading file: {e}]"


def save_file(file_path: str, content: List[str]) -> None:
    """Write the given lines to a file, overwriting any existing content.

    Args:
        file_path: Path to the file to write.
        content: Iterable of strings to write (lines).
    """
    # Ensure parent directory exists
    parent = os.path.dirname(file_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    with open(file_path, "w") as f:
        f.writelines(content)


def delete_file(file_path: str) -> bool:
    """Delete the given file if it exists.

    Args:
        file_path: Path to the file to delete.

    Returns:
        True if the file was deleted, False if it did not exist.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    else:
        return False

