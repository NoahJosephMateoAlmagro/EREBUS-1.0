"""
Navigation controller for EREBUS.

This module contains the controller responsible for showing and hiding pages
inside the main content area.
"""


class NavigationController:
    """
    Controls page navigation inside the application.
    """

    def __init__(self, app, layout):
        """
        Initializes the navigation controller.

        Args:
            app: Root application instance.
            layout: Built application layout.
        """
        self.app = app
        self.layout = layout

    def show_tab(self, tab_name: str) -> None:
        """
        Displays the selected page and hides the rest.

        If the selected page defines an on_show method, it is executed after the
        page becomes visible. This allows pages such as Data to refresh their
        content when the user opens the tab.

        Args:
            tab_name: Internal tab name to display.
        """
        for page in self.layout.pages.values():
            page.grid_remove()

        page = self.layout.pages.get(tab_name)

        if page:
            page.grid()
            page.tkraise()
            self._run_page_show_hook(page)

        self.app.active_tab = tab_name
        self.app.appearance.apply_theme()

    def raise_active_tab(self, tab_name: str) -> None:
        """
        Raises the selected page without reapplying the theme.

        This is useful during theme and scale changes because the appearance
        controller already applies the current palette.

        If the selected page defines an on_show method, it is executed after the
        page becomes visible.

        Args:
            tab_name: Internal tab name to raise.
        """
        for page in self.layout.pages.values():
            page.grid_remove()

        page = self.layout.pages.get(tab_name)

        if page:
            page.grid()
            page.tkraise()
            self._run_page_show_hook(page)

        self.app.active_tab = tab_name

    def _run_page_show_hook(self, page) -> None:
        """
        Runs the optional page visibility hook.

        Args:
            page: Page instance that has just been displayed.
        """
        if hasattr(page, "on_show"):
            page.on_show()