from textual import events
from textual.widgets import TextArea, Static, Input
from core.file_management import read_file, delete_file, save_file
from textual.containers import Container
from ui.editor_view import EditorView
from textual.message import Message
from typing import Literal
from ui.overlay import Overlay
from textual.content import Content
from commands.messages import GitCommitMessageSubmitted
from rich.console import RenderableType
import logging
from core.paths import LOG_FILE_STR
logging.basicConfig(filename=LOG_FILE_STR, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
from textual.events import Key



class GitCommitMessage(Overlay):
    def __init__(self, message_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_id = message_id

    def _post_to_workspace(self, message):
        """Post message to workspace."""
        from workspace.workspace import Workspace
        workspace = self.app.query_one(Workspace)
        workspace.post_message(message)

    def on_mount(self):
        super().on_mount()
        self.mount(Static("Enter commit message", classes="overlay_title"))
        self.text_input = Input(placeholder="commit_message", classes="git_commit_message")
        self.mount(self.text_input)
        self.text_input.focus()

    async def on_input_submitted(self, event: Input.Submitted):
        self._post_to_workspace(GitCommitMessageSubmitted(self.message_id, event.input.value, event.input))
        self.remove()




