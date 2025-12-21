from textual import events
from textual.widgets import TextArea, Static, Input
from core.file_management import read_file, delete_file, save_file
from textual.containers import Container
from ui.editor_view import EditorView
from textual.message import Message
from typing import Literal
from ui.overlay import Overlay
from textual.content import Content
from commands.messages import LineInputSubmitted
from rich.console import RenderableType
import logging
from core.paths import LOG_FILE_STR
logging.basicConfig(filename=LOG_FILE_STR, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
from textual.events import Key



class LineInput(Overlay):
    def __init__(self, num_lines: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_lines = str(num_lines)
        self.styles.height = "25%"

    def _post_to_workspace(self, message):
        """Post message to workspace."""
        from workspace.workspace import Workspace
        workspace = self.app.query_one(Workspace)
        workspace.post_message(message)

    def on_mount(self):
        super().on_mount()
        self.mount(Static("Enter line to jump to", classes="overlay_title"))
        self.mount(Static(self.num_lines + " lines", classes="grey"))
        self.text_input = Input(placeholder="line", classes="line_input", type="integer")
        self.mount(self.text_input)
        self.text_input.focus()

    async def on_input_submitted(self, event: Input.Submitted):
        self._post_to_workspace(LineInputSubmitted(event.input.value))
        self.remove()




