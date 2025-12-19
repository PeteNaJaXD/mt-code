from textual.containers import Container, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from textual.events import Key, Resize
from textual.widgets import Static, Button


class Overlay(Container):
    """Base overlay class with responsive width/height based on terminal size."""

    def __init__(self, width: int = None, height: int = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._overlay_width = width
        self._overlay_height = height

    def _get_responsive_size(self, terminal_width: int, terminal_height: int) -> tuple[str, str]:
        """Calculate responsive width/height percentages based on terminal size."""
        # Width breakpoints - smaller terminal = larger overlay
        if terminal_width < 60:
            width_pct = "95%"
        elif terminal_width < 80:
            width_pct = "85%"
        elif terminal_width < 120:
            width_pct = "70%"
        else:
            width_pct = "50%"

        # Height breakpoints - smaller terminal = larger overlay
        if terminal_height < 20:
            height_pct = "95%"
        elif terminal_height < 30:
            height_pct = "90%"
        elif terminal_height < 40:
            height_pct = "80%"
        elif terminal_height < 50:
            height_pct = "70%"
        else:
            height_pct = "60%"

        return width_pct, height_pct

    def _apply_responsive_size(self):
        """Apply responsive sizing based on current terminal dimensions."""
        if self._overlay_width or self._overlay_height:
            # Custom dimensions override responsive sizing
            if self._overlay_width:
                self.styles.width = self._overlay_width
            if self._overlay_height:
                self.styles.height = self._overlay_height
        else:
            # Use responsive sizing
            terminal_width = self.app.size.width
            terminal_height = self.app.size.height
            width_pct, height_pct = self._get_responsive_size(terminal_width, terminal_height)
            self.styles.width = width_pct
            self.styles.height = height_pct

    def on_mount(self):
        self.classes = "overlay"
        self._apply_responsive_size()

    def on_resize(self, event: Resize):
        """Update overlay size when terminal is resized."""
        self._apply_responsive_size()

    def on_key(self, event: Key):
        if event.key == "escape":
            self.remove()
