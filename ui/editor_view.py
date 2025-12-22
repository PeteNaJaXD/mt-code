from textual.app import App
from textual.widgets import Static, Button, TextArea, Input
from textual.containers import Vertical, Horizontal, Container
from textual.events import Key
from textual.document._document import Location
from textual.binding import Binding
from typing import Tuple
from textual.message import Message
import logging
from core.buffer import Buffer
from core.file_management import delete_file, read_file, save_file
import asyncio
from ui.save_as import SaveAsPopup
from ui.code_editor import CodeEditor
from commands.messages import EditorSavedAs, FilePathProvided, UseFile, EditorOpenFile, SaveAsProvided, EditorSaveFile, EditorDirtyFile, FileChangedExternally
from pathlib import Path
from ui.open_file import OpenFilePopup
from core.paths import LOG_FILE_STR
logging.basicConfig(filename=LOG_FILE_STR, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
import random
import string
import os
class EditorView(Container):
    def __init__(self, file_path="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self.tab_id: str | None = None  # will be set by TabManager
        self._file_watch_task: asyncio.Task | None = None
        self._last_mtime: float = 0
        self._file_watch_interval = 1.0  # Check every 1 second

    def random_hash(self):
        first = random.choice(string.ascii_lowercase)
        rest = ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=5)
        )
        return first + rest
    def hide(self):
        self.styles.display = "none"
        # Close completions overlay when hiding the editor
        if hasattr(self, 'code_area') and self.code_area:
            self.code_area._close_completions_overlay()
    def show(self):
        self.styles.display = "block"
    
    def on_mount(self):
        self.newid = self.random_hash()
        # If a file_path was provided, ensure the file exists on disk.
        # If no file_path was provided (empty string), treat this editor as
        # an in-memory buffer and do not attempt to create a filesystem file.
        if self.file_path:
            if not os.path.exists(self.file_path):
                # Create the file path (and parent dir) if necessary
                parent = os.path.dirname(self.file_path)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
                with open(self.file_path, "w") as f:
                    f.write("")
            # Record initial modification time
            self._last_mtime = self._get_file_mtime()
        self.code_area = CodeEditor.code_editor(tab_id=self.tab_id, file=self.file_path, classes="editor", id=self.newid)
        self.code_area.indent_type = "spaces"
        self.code_area.indent_width = 4
        self.code_area.show_line_numbers = True
        self.last_text = self.code_area.text
        self.mount(self.code_area)
        # Start file watcher
        if self.file_path:
            self._start_file_watcher()

    def _get_file_mtime(self) -> float:
        """Get the modification time of the file."""
        try:
            return Path(self.file_path).stat().st_mtime
        except (FileNotFoundError, OSError):
            return 0

    def _start_file_watcher(self):
        """Start the file watcher task."""
        if self._file_watch_task is None or self._file_watch_task.done():
            self._file_watch_task = asyncio.create_task(self._watch_file_for_changes())

    def _stop_file_watcher(self):
        """Stop the file watcher task."""
        if self._file_watch_task and not self._file_watch_task.done():
            self._file_watch_task.cancel()
            self._file_watch_task = None

    async def _watch_file_for_changes(self):
        """Watch the file for external changes."""
        # Don't watch log files or other files that change frequently
        skip_extensions = {'.log', '.tmp', '.swp', '.pyc'}
        if self.file_path and Path(self.file_path).suffix.lower() in skip_extensions:
            return

        try:
            while True:
                await asyncio.sleep(self._file_watch_interval)
                if not self.file_path:
                    continue

                current_mtime = self._get_file_mtime()
                if current_mtime > self._last_mtime and self._last_mtime > 0:
                    logging.debug(f"File changed externally: {self.file_path}")
                    self._last_mtime = current_mtime
                    self.post_message(FileChangedExternally(self.tab_id, self.file_path))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Error in file watcher: {e}")

    def update_mtime(self):
        """Update the last modification time (call after saving)."""
        self._last_mtime = self._get_file_mtime()

    def reload_file(self):
        """Reload the file content from disk."""
        if self.file_path and os.path.exists(self.file_path):
            content = read_file(self.file_path)
            self.code_area.load_text_silent(content)
            self._last_mtime = self._get_file_mtime()
            logging.info(f"Reloaded file: {self.file_path}")
        
    async def on_text_area_changed(self, event: TextArea.Changed):
        # import here or top-level
        from commands.messages import EditorDirtyFile
        # include tab id when posting
        self.post_message(EditorDirtyFile(self.tab_id, self.file_path))

    def on_editor_save_file(self, event: EditorSaveFile):
        """Update mtime after saving to avoid false change detection."""
        if event.tab_id == self.tab_id:
            self.update_mtime()

    def on_editor_saved_as(self, event: EditorSavedAs):
        logging.info(event.contents)
        self.contents = event.contents
        self.screen.mount(SaveAsPopup())
    def on_editor_open_file(self, event: EditorOpenFile):
        self.screen.mount(OpenFilePopup())
    def on_file_path_provided(self, event: FilePathProvided):
        logging.info("file path provided!")
        file_path = event.file_path
        self.file_path = file_path
        if os.path.exists(file_path):
            contents = read_file(file_path)
        else:
            contents = self.contents
        save_file(file_path, contents)
        # For global FilePathProvided events (e.g., OpenFilePopup from Workspace),
        # we create a new tab. For SaveAs (editor-local) flows, SaveAsPopup will
        # post a SaveAsProvided message which is handled separately by
        # `on_save_as_provided`.
        # Do not post UseFile here to avoid duplicate tab creation.
        self.post_message(EditorSaveFile(self.tab_id))
        return

    def on_save_as_provided(self, event: "SaveAsProvided"):
        # Handle SaveAs submissions originating from this editor's SaveAsPopup.
        # Save the contents to the chosen path and instruct the TabManager to
        # replace the current active tab with an editor bound to the file.
        logging.info("save-as provided: %s", event.file_path)
        file_path = event.file_path
        self.file_path = file_path
        if os.path.exists(file_path):
            contents = read_file(file_path)
        else:
            contents = self.contents
        save_file(file_path, contents)
        # notify higher-level manager to use this file for the current tab
        self.post_message(UseFile(file_path))
    async def on_key(self, event: Key):
        pass
    def undo(self):
        self.code_area.undo()
    def redo(self):
        self.code_area.redo()



