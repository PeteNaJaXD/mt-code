from textual import events
from textual.widgets import TextArea, Static, Input
from core.file_management import read_file, delete_file, save_file
from textual.containers import Container
from ui.overlay import Overlay
from textual.message import Message
from typing import Literal
from textual.content import Content
from rich.console import RenderableType
import logging
from commands.messages import FilePathProvided
from core.paths import LOG_FILE_STR
logging.basicConfig(filename=LOG_FILE_STR, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")




class SaveAsPopup(Overlay):
    def _post_to_active_editor(self, message):
        """Post message to active editor."""
        from workspace.workspace import Workspace
        workspace = self.app.query_one(Workspace)
        editor = workspace.tab_manager.get_active_editor()
        if editor:
            editor.post_message(message)

    def on_mount(self):
        super().on_mount()
        self.mount(Static("Save as", classes="overlay_title"))
        self.file_name_input = Input(placeholder="relative/path/to/save", classes="save_as")
        self.mount(self.file_name_input)
        self.file_name_input.focus()

    async def on_input_submitted(self, event: Input.Submitted):
        if "save_as" in event.input.classes:
            self.file_path = event.input.value
            from commands.messages import SaveAsProvided
            self._post_to_active_editor(SaveAsProvided(self.file_path))
            self.remove()