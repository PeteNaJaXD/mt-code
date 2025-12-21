from textual.containers import Container, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from textual.events import Key, Resize
from textual.widgets import Static, Button


class Overlay(Container):
    """Base overlay class with responsive width/height based on terminal size."""

    def __init__(self, width: int = None, height: int = None, center_on_screen: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._overlay_width = width
        self._overlay_height = height
        self._center_on_screen = center_on_screen

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
        self.styles.position = "absolute"
        self._apply_responsive_size()
        if self._center_on_screen:
            self.call_after_refresh(self._center_overlay)

    def _center_overlay(self):
        """Center the overlay on the screen using absolute coordinates."""
        screen_width = self.screen.size.width
        screen_height = self.screen.size.height
        overlay_width = self.size.width
        overlay_height = self.size.height
        x = (screen_width - overlay_width) // 2
        y = (screen_height - overlay_height) // 2
        self.styles.offset = (x, y)

    def on_resize(self, event: Resize):
        """Update overlay size and position when terminal is resized."""
        self._apply_responsive_size()
        if self._center_on_screen:
            self._center_overlay()

    def on_key(self, event: Key):
        if event.key == "escape":
            self.remove()
