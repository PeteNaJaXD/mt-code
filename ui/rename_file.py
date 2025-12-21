from textual.widgets import Static, Input
from ui.overlay import Overlay
from commands.messages import RenameFileProvided
import os


class RenameFilePopup(Overlay):
    def __init__(self, current_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_path = current_path

    def _post_to_workspace(self, message):
        """Post message to workspace."""
        from workspace.workspace import Workspace
        workspace = self.app.query_one(Workspace)
        workspace.post_message(message)

    def on_mount(self):
        super().on_mount()
        self.mount(Static("Rename file", classes="overlay_title"))
        self.file_name_input = Input(
            placeholder="new/path/to/file",
            value=self.current_path,
            classes="rename_file"
        )
        self.mount(self.file_name_input)
        self.file_name_input.focus()
        # Select just the filename part for easy editing
        if "/" in self.current_path:
            filename_start = self.current_path.rfind("/") + 1
        else:
            filename_start = 0
        self.file_name_input.cursor_position = len(self.current_path)

    async def on_input_submitted(self, event: Input.Submitted):
        if "rename_file" in event.input.classes:
            new_path = event.input.value
            if new_path and new_path != self.current_path:
                self._post_to_workspace(RenameFileProvided(self.current_path, new_path))
            self.remove()
