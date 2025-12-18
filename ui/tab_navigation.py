"""Tab navigation mixin for TabManager.

This module contains tab navigation logic including:
- Finding next/previous tabs
- Finding nearest tabs when closing
"""

import logging
from core.paths import LOG_FILE_STR

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class TabNavigationMixin:
    """Mixin providing tab navigation functionality to TabManager."""

    def get_next_tab(self, tab_id: str) -> str | None:
        """Get the next tab in order, wrapping to first if at end."""
        logging.info("get_next_tab called with tab_id=%s", tab_id)
        logging.info("Current tab_order=%s", self.tab_order)

        if not self.tab_order:
            logging.info("tab_order empty")
            return None

        try:
            current_index = self.tab_order.index(tab_id)
        except ValueError:
            logging.info("tab_id not found in tab_order: %s", tab_id)
            return None

        # Look ahead
        if current_index + 1 < len(self.tab_order):
            next_tab = self.tab_order[current_index + 1]
            logging.info("Next tab ahead: %s", next_tab)
            return next_tab

        # Nothing ahead, return the tab with the lowest numeric value
        numeric_tabs = [int(tid) for tid in self.tab_order if tid.isdigit()]
        if numeric_tabs:
            lowest_tab = str(min(numeric_tabs))
            logging.info("Nothing ahead, returning lowest tab_id: %s", lowest_tab)
            return lowest_tab

        # Fallback: just return the first tab in order
        fallback_tab = self.tab_order[0]
        logging.info("Fallback to first tab in order: %s", fallback_tab)
        return fallback_tab

    def get_nearest_tab(self, tab_id: str) -> str | None:
        """Get the nearest tab by numeric distance."""
        logging.info("get_nearest_tab called with tab_id=%s", tab_id)
        logging.info("Current tab_order=%s", self.tab_order)

        if not self.tab_order:
            logging.info("tab_order empty")
            return None

        try:
            current = int(tab_id)
        except ValueError:
            logging.info("tab_id is not numeric: %s", tab_id)
            return None

        nearest_id = None
        nearest_distance = None

        for other in self.tab_order:
            if other == tab_id:
                logging.info("Skipping same tab_id %s", other)
                continue

            try:
                other_int = int(other)
            except ValueError:
                logging.info("Skipping non-numeric tab id: %s", other)
                continue

            distance = abs(other_int - current)

            logging.info(
                "Comparing removed tab %s -> remaining tab %s | distance=%d",
                tab_id,
                other,
                distance
            )

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_id = other
                logging.info(
                    "New nearest tab: %s (distance=%d)",
                    nearest_id,
                    nearest_distance
                )

        logging.info("Final nearest tab for %s is %s", tab_id, nearest_id)
        return nearest_id

    def get_nearest_tab_after(self, tab_id: str) -> str | None:
        """Get the nearest tab with higher ID, wrapping to lowest if none."""
        logging.info("get_nearest_tab_after called with tab_id=%s", tab_id)
        logging.info("Current tab_order=%s", self.tab_order)

        if not self.tab_order:
            logging.info("tab_order empty")
            return None

        try:
            current = int(tab_id)
        except ValueError:
            logging.info("tab_id is not numeric: %s", tab_id)
            return None

        # Find all numeric tabs
        numeric_tabs = []
        for other in self.tab_order:
            try:
                numeric_tabs.append(int(other))
            except ValueError:
                logging.info("Skipping non-numeric tab id: %s", other)

        # Prefer the smallest tab ID that is higher than current
        higher_tabs = [tid for tid in numeric_tabs if tid > current]
        if higher_tabs:
            nearest_id = str(min(higher_tabs))
            logging.info("Found nearest higher tab: %s", nearest_id)
            return nearest_id

        # If no higher tabs, wrap around to the lowest tab ID
        if numeric_tabs:
            nearest_id = str(min(numeric_tabs))
            logging.info("No higher tabs, wrapping to lowest tab: %s", nearest_id)
            return nearest_id

        return None

    def get_nearest_tab_before(self, tab_id: str) -> str | None:
        """Get the nearest tab with lower ID, wrapping to lowest if none."""
        logging.info("get_nearest_tab_before called with tab_id=%s", tab_id)
        logging.info("Current tab_order=%s", self.tab_order)

        if not self.tab_order:
            logging.info("tab_order empty")
            return None

        try:
            current = int(tab_id)
        except ValueError:
            logging.info("tab_id is not numeric: %s", tab_id)
            return None

        # Find all numeric tabs
        numeric_tabs = []
        for other in self.tab_order:
            try:
                numeric_tabs.append(int(other))
            except ValueError:
                logging.info("Skipping non-numeric tab id: %s", other)

        # Prefer the highest tab ID that is lower than current
        lower_tabs = [tid for tid in numeric_tabs if tid < current]
        if lower_tabs:
            nearest_id = str(max(lower_tabs))
            logging.info("Found nearest lower tab: %s", nearest_id)
            return nearest_id

        # If no lower tabs, return the lowest tab ID (wrap around)
        if numeric_tabs:
            nearest_id = str(min(numeric_tabs))
            logging.info("No lower tabs, wrapping to lowest tab: %s", nearest_id)
            return nearest_id

        return None

    def next_tab(self, active_tab):
        """Switch to the next tab."""
        next_tab_id = self.get_nearest_tab_after(active_tab)
        self.switch_tab(next_tab_id)

    def previous_tab(self, active_tab):
        """Switch to the previous tab."""
        next_tab_id = self.get_nearest_tab_before(active_tab)
        self.switch_tab(next_tab_id)
