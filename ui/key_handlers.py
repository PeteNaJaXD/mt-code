"""Key handling mixin for CodeEditor.

This module contains key event handling including:
- Auto-pairing of brackets, quotes
- Keyboard shortcuts (ctrl+s, ctrl+a, etc.)
"""

import asyncio
import logging
from core.paths import LOG_FILE_STR

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class KeyHandlersMixin:
    """Mixin class providing key handling functionality to CodeEditor."""

    def _init_key_handlers_state(self):
        """Initialize key handler state variables. Call from __init__."""
        self.pairs = {
            "(": ")",
            "[": "]",
            "{": "}",
        }

    def _handle_key_event(self, event):
        """
        Handle key events for auto-pairing and shortcuts.
        Call from _on_key. Returns True if event was fully handled.
        """
        # Check if cursor moved away from completions
        self._check_cursor_moved_from_completion()

        # Close completions on most key presses except escape/tab
        if self._completions_overlay and event.key not in ["escape", "tab"]:
            self._close_completions_overlay()

        # Handle shift+backspace as regular backspace
        if self._handle_shift_backspace(event):
            return False  # Let parent handle modified event

        # Handle auto-pairing
        if self._handle_auto_pair(event):
            return True

        # Handle quotes
        if self._handle_quotes(event):
            return True

        # Handle shortcuts
        self._handle_shortcuts(event)

        return False

    def _handle_shift_backspace(self, event):
        """Normalize shift+backspace to regular backspace."""
        try:
            keyname = getattr(event, "key", None)
        except Exception:
            keyname = None

        if keyname and (
            keyname == "shift+backspace" or
            (keyname == "backspace" and getattr(event, "shift", False))
        ):
            try:
                event.key = "backspace"
                event.shift = False
            except Exception:
                pass
            return True
        return False

    def _handle_auto_pair(self, event):
        """Handle auto-pairing of brackets. Returns True if handled."""
        if event.character in self.pairs:
            self.insert(event.character + self.pairs[event.character])
            self.move_cursor_relative(columns=-1)
            event.prevent_default()
            return True

        if event.character in self.pairs.values():
            try:
                char = str(self.get_line(self.cursor_location[0]))[self.cursor_location[1]]
                if char == event.character:
                    self.move_cursor_relative(columns=1)
                    event.prevent_default()
                    return True
            except IndexError:
                pass

        return False

    def _handle_quotes(self, event):
        """Handle auto-pairing of quotes. Returns True if handled."""
        if event.character == '"':
            return self._handle_quote_char('"', event)
        elif event.character == "'":
            return self._handle_quote_char("'", event)
        return False

    def _handle_quote_char(self, quote_char, event):
        """Handle a specific quote character."""
        try:
            char = str(self.get_line(self.cursor_location[0]))[self.cursor_location[1]]
            if char == quote_char:
                self.move_cursor_relative(columns=1)
            else:
                self.insert(quote_char * 2)
                self.move_cursor_relative(columns=-1)
            event.prevent_default()
            return True
        except IndexError:
            self.insert(quote_char * 2)
            self.move_cursor_relative(columns=-1)
            event.prevent_default()
            return True

    def _handle_shortcuts(self, event):
        """Handle keyboard shortcuts."""
        if event.key == "ctrl+a":
            self.select_all()

        if event.key == "ctrl+s":
            self.save_file()

        if event.key == "ctrl+space":
            asyncio.create_task(self.show_completions())
            event.prevent_default()
