"""Select AI provider overlay."""

from ui.overlay import Overlay
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option
from commands.messages import SelectAIEvent
import logging
from core.paths import LOG_FILE_STR

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class SelectAI(Overlay):
    """Overlay for selecting AI provider."""

    def __init__(self, providers: list, current: str = None, *args, **kwargs):
        """
        Args:
            providers: List of (name, display_name, is_available) tuples
            current: Current provider name
        """
        super().__init__(*args, **kwargs)
        self.providers = providers
        self.current = current

    def on_mount(self):
        super().on_mount()
        self.status = Static("Select AI Provider")
        self.mount(self.status)

        self.option_list = OptionList(classes="syntax_options")

        for name, display_name, is_available in self.providers:
            status = ""
            if name == self.current:
                status = " (current)"
            elif not is_available:
                status = " (no API key)"

            self.option_list.add_option(Option(f"{display_name}{status}", id=name))

        self.mount(self.option_list)
        self.option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        provider_name = event.option.id
        self.status.update(f"Selected: {event.option.prompt}")
        logging.info(f"Selected AI provider: {provider_name}")
        self.post_message(SelectAIEvent(provider_name))
        self.remove()
