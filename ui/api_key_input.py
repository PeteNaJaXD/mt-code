"""API Key input overlay."""

from ui.overlay import Overlay
from textual.widgets import Input, Static, Button, OptionList
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical
from textual.app import ComposeResult
from commands.messages import APIKeySet
from core.ai_config import get_ai_config
import logging
from core.paths import LOG_FILE_STR

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class APIKeyInput(Overlay):
    """Overlay for setting API keys."""

    DEFAULT_CSS = """
    APIKeyInput #key-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    APIKeyInput #key-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    APIKeyInput #provider-select {
        height: 5;
        margin-bottom: 1;
    }

    APIKeyInput #key-input {
        margin-bottom: 1;
    }

    APIKeyInput #key-status {
        height: 2;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    APIKeyInput #button-row {
        height: 3;
        align: center middle;
    }

    APIKeyInput #button-row Button {
        margin: 0 1;
    }
    """

    PROVIDERS = [
        ("openai", "OpenAI"),
        ("claude", "Claude (Anthropic)")
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_provider = "openai"
        self.config = get_ai_config()

    def compose(self) -> ComposeResult:
        with Vertical(id="key-container"):
            yield Static("Set API Key", id="key-title")
            yield OptionList(
                *[Option(display, id=name) for name, display in self.PROVIDERS],
                id="provider-select"
            )
            yield Input(placeholder="Enter API key...", password=True, id="key-input")
            yield Static("", id="key-status")
            with Horizontal(id="button-row"):
                yield Button("Save", id="save-btn", variant="success")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self):
        super().on_mount()
        self._update_status()
        # Focus the provider select
        provider_select = self.query_one("#provider-select", OptionList)
        provider_select.focus()

    def _update_status(self):
        """Update the status text showing if key is set."""
        status = self.query_one("#key-status", Static)
        key = self.config.get_api_key(self.selected_provider)
        if key:
            # Show masked key
            masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
            status.update(f"Current key: {masked}")
        else:
            status.update("No API key set")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        """Handle provider selection."""
        if event.option_list.id == "provider-select":
            self.selected_provider = event.option.id
            self._update_status()
            # Focus the input
            key_input = self.query_one("#key-input", Input)
            key_input.focus()

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "save-btn":
            self._save_key()
        elif event.button.id == "cancel-btn":
            self.remove()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle enter in input."""
        if event.input.id == "key-input":
            self._save_key()

    def _save_key(self):
        """Save the API key."""
        key_input = self.query_one("#key-input", Input)
        api_key = key_input.value.strip()

        if api_key:
            self.config.set_api_key(self.selected_provider, api_key)
            logging.info(f"Saved API key for {self.selected_provider}")
            self.post_message(APIKeySet(self.selected_provider))

        self.remove()
