from ui.overlay import Overlay
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option
from commands.messages import SelectSyntaxEvent
import difflib
import logging
from core.paths import LOG_FILE_STR
logging.basicConfig(filename=LOG_FILE_STR, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class SelectSyntax(Overlay):
    def __init__(self, syntaxes: list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.syntaxes = syntaxes

    def _post_to_workspace(self, message):
        """Post message to workspace."""
        from workspace.workspace import Workspace
        workspace = self.app.query_one(Workspace)
        workspace.post_message(message)

    def on_mount(self):
        super().on_mount()
        # option list with search bar
        self.status = Static("Select syntax", classes="overlay_title")
        self.mount(self.status)
        self.search_bar = Input(placeholder=">")
        self.mount(self.search_bar)
        self.search_bar.focus()
        syntax_options = []
        for syntax in self.syntaxes:
            syntax_options.append(Option(syntax))
        self.option_list = OptionList(*syntax_options, classes="syntax_options")
        self.mount(self.option_list)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        self.status.update("Selected: " + event.option.prompt)
        logging.info(self.status.content)
        self._post_to_workspace(SelectSyntaxEvent(event.option.prompt))
        self.remove()
    async def on_input_changed(self, event: Input.Changed):
        query = event.value
        self.search_text = query

        # Fuzzy ranking
        all_commands = self.syntaxes
        if query:
            matches = difflib.get_close_matches(query, all_commands, n=len(all_commands), cutoff=0)
        else:
            matches = all_commands

        # Clear and re-mount OptionList with new order
        self.option_list.clear_options()
        for name in matches:
            self.option_list.add_option(Option(name))
    async def on_input_submitted(self, event: Input.Submitted):
        self.option_list.focus()
        self.option_list.action_first()