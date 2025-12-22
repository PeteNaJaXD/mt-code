"""Select Python interpreter overlay."""

from ui.overlay import Overlay
from textual.widgets import OptionList, Static, Input, Button
from textual.widgets.option_list import Option
from textual.containers import Horizontal
from commands.messages import PythonInterpreterSelected
from core.python_config import get_python_config
import logging
from core.paths import LOG_FILE_STR

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class PythonInterpreterSelect(Overlay):
    """Overlay for selecting Python interpreter."""

    DEFAULT_CSS = """
    PythonInterpreterSelect {
        width: 60;
        height: auto;
        max-height: 20;
    }

    PythonInterpreterSelect .interpreter_options {
        height: auto;
        max-height: 10;
        margin-bottom: 1;
    }

    PythonInterpreterSelect .custom_path_container {
        height: 3;
        margin-top: 1;
    }

    PythonInterpreterSelect Input {
        width: 100%;
    }
    """

    def __init__(self, working_dir: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.working_dir = working_dir
        self.python_config = get_python_config()

    def on_mount(self):
        super().on_mount()
        self.title = Static("Select Python Interpreter", classes="overlay_title")
        self.mount(self.title)

        # Get available interpreters
        interpreters = self.python_config.detect_available_interpreters(self.working_dir)
        current_path = self.python_config.get_interpreter_path()

        self.option_list = OptionList(classes="interpreter_options")

        # Add "System Default" option
        default_label = "System Default (python3)"
        if not current_path:
            default_label += " (current)"
        self.option_list.add_option(Option(default_label, id=""))

        # Add detected interpreters
        for interp in interpreters:
            label = f"{interp['label']}: {interp['path']}"
            if interp['path'] == current_path:
                label += " (current)"
            self.option_list.add_option(Option(label, id=interp['path']))

        self.mount(self.option_list)

        # Add custom path input
        self.custom_label = Static("Or enter custom path:")
        self.mount(self.custom_label)

        self.custom_input = Input(
            placeholder="/path/to/python",
            value=current_path if current_path else ""
        )
        self.mount(self.custom_input)

        self.option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        interpreter_path = event.option.id
        self._select_interpreter(interpreter_path)

    def on_input_submitted(self, event: Input.Submitted):
        custom_path = event.value.strip()
        self._select_interpreter(custom_path)

    def _select_interpreter(self, path: str):
        """Select an interpreter and save to config."""
        self.python_config.set_interpreter_path(path)

        if path:
            logging.info(f"Selected Python interpreter: {path}")
        else:
            logging.info("Selected system default Python interpreter")

        self.post_message(PythonInterpreterSelected(path))
        self.remove()
