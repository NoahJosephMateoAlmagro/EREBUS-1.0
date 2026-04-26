"""
Execution page for the EREBUS graphical interface.

This page contains the target input, execution controls, global settings and
module configuration widgets.
"""

from copy import deepcopy

import customtkinter as ctk

from application.config import APP_CONFIG
import presentation.constants as C
from presentation.module_ui_metadata import (
    MODULE_UI_CONFIG,
    SETTING_LABELS,
    SETTING_TOOLTIPS,
)
from presentation.widgets.cards import create_card
from presentation.widgets.tooltip import Tooltip


class ExecutionPage(ctk.CTkFrame):
    """
    Page used to configure and launch an EREBUS execution.

    The page owns all widgets related to target selection, module activation
    and runtime configuration overrides.
    """

    def __init__(self, parent, fonts, on_start, on_stop):
        """
        Initializes the execution page.

        Args:
            parent: Parent widget.
            fonts: Application font catalog.
            on_start: Callback executed when the user starts an execution.
            on_stop: Callback executed when the user requests a safe stop.
        """
        super().__init__(parent, corner_radius=0)

        self.fonts = fonts
        self.on_start = on_start
        self.on_stop = on_stop

        self.module_switches = {}
        self.module_cards = {}
        self.module_settings_frames = {}
        self.config_entries = {}

        self.execution_scroll = None
        self.execution_card = None
        self.global_card = None
        self.modules_card = None
        self.modules_container = None

        self.target_entry = None
        self.run_button = None
        self.stop_button = None
        self.status_label = None
        self.all_modules_switch = None

        self._build()

    def _build(self):
        """
        Builds the execution page.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.execution_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
        )
        self.execution_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.execution_scroll.grid_columnconfigure(0, weight=1)

        self._build_execution_card()
        self._build_global_settings_card()
        self._build_modules_card()

    def _build_execution_card(self):
        """
        Builds the execution control card.

        This card contains the target domain input, the execution button,
        the stop button and the current execution status.
        """
        self.execution_card = create_card(self.execution_scroll, row=0)

        self.execution_card.grid_columnconfigure(0, weight=1)
        self.execution_card.grid_columnconfigure(1, weight=0)

        header = ctk.CTkFrame(self.execution_card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(22, 6))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text=C.EXECUTION_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            header,
            text=C.STATUS_READY,
            font=self.fonts["small_bold"],
            corner_radius=10,
            padx=18,
            pady=8,
        )
        self.status_label.grid(row=0, column=1, sticky="e", padx=(24, 0))

        description = ctk.CTkLabel(
            self.execution_card,
            text=C.EXECUTION_DESCRIPTION,
            font=self.fonts["body"],
            wraplength=1000,
            justify="left",
        )
        description.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

        form = ctk.CTkFrame(self.execution_card, fg_color="transparent")
        form.grid(row=2, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 22))

        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=0)
        form.grid_columnconfigure(3, weight=0)

        target_label = ctk.CTkLabel(
            form,
            text="Target domain",
            font=self.fonts["body_bold"],
        )
        target_label.grid(row=0, column=0, sticky="w", padx=(0, 14), pady=10)

        self.target_entry = ctk.CTkEntry(
            form,
            placeholder_text="example.com",
            height=44,
            font=self.fonts["body"],
        )
        self.target_entry.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=10)

        self.run_button = ctk.CTkButton(
            form,
            text="Start analysis",
            height=44,
            width=185,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.on_start,
        )
        self.run_button.grid(row=0, column=2, sticky="e", pady=10)

        self.stop_button = ctk.CTkButton(
            form,
            text="Stop",
            height=44,
            width=120,
            corner_radius=6,
            font=self.fonts["button"],
            command=self.on_stop,
            state="disabled",
        )
        self.stop_button.grid(row=0, column=3, sticky="e", padx=(10, 0), pady=10)

    def _build_global_settings_card(self):
        """
        Builds the global configuration card.
        """
        self.global_card = create_card(self.execution_scroll, row=1)

        title = ctk.CTkLabel(
            self.global_card,
            text=C.GENERAL_CONFIGURATION_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(22, 6))

        description = ctk.CTkLabel(
            self.global_card,
            text=C.GENERAL_CONFIGURATION_DESCRIPTION,
            font=self.fonts["body"],
        )
        description.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))

        body = ctk.CTkFrame(self.global_card, fg_color="transparent")
        body.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 22))
        body.grid_columnconfigure((0, 1, 2), weight=1)

        self._add_setting_entry(
            parent=body,
            row=0,
            column=0,
            section="logging",
            key="timezone",
        )

        self._add_option_menu(
            parent=body,
            row=0,
            column=1,
            section="logging",
            key="mode",
            values=C.OPTION_LOGGING_MODES,
        )

        self._add_switch_setting(
            parent=body,
            row=0,
            column=2,
            section="debug",
            key="clear_db_on_run",
            text="Clear database on run",
        )

    def _build_modules_card(self):
        """
        Builds the analysis modules configuration card.

        This card contains the list of modules that can be enabled or disabled,
        as well as a global switch to enable or disable all modules at once.
        """
        self.modules_card = create_card(self.execution_scroll, row=2)
        self.modules_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.modules_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 6))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = ctk.CTkLabel(
            header,
            text=C.MODULES_TITLE,
            font=self.fonts["section"],
        )
        title.grid(row=0, column=0, sticky="w")

        self.all_modules_switch = ctk.CTkSwitch(
            header,
            text="Enable all",
            font=self.fonts["body_bold"],
            switch_width=72,
            switch_height=34,
            command=self.on_all_modules_toggle,
        )
        self.all_modules_switch.grid(row=0, column=1, sticky="e", padx=(24, 0))

        description = ctk.CTkLabel(
            self.modules_card,
            text=C.MODULES_DESCRIPTION,
            font=self.fonts["body"],
            wraplength=1000,
            justify="left",
        )
        description.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        self.modules_container = ctk.CTkFrame(self.modules_card, fg_color="transparent")
        self.modules_container.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))
        self.modules_container.grid_columnconfigure(0, weight=1)

        for row, module_key in enumerate(APP_CONFIG["modules"].keys()):
            self._add_module_row(self.modules_container, row, module_key)

        self._sync_all_modules_switch()

    def _add_module_row(self, parent, row, module_key):
        """
        Adds one module card to the module list.

        Args:
            parent: Parent frame where the module card is placed.
            row: Grid row.
            module_key: Internal module key from APP_CONFIG.
        """
        metadata = MODULE_UI_CONFIG.get(module_key, {})
        title = metadata.get("title", module_key)
        description = metadata.get("description", "")
        depends_on = metadata.get("depends_on", [])

        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=0, sticky="ew", pady=10)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=self.fonts["module_title"],
        )
        title_label.grid(row=0, column=0, sticky="w")

        description_label = ctk.CTkLabel(
            header,
            text=description,
            font=self.fonts["small"],
            wraplength=950,
            justify="left",
        )
        description_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        if depends_on:
            dependency_text = "Depends on: " + ", ".join(
                MODULE_UI_CONFIG.get(dep, {}).get("title", dep)
                for dep in depends_on
            )

            dependency_label = ctk.CTkLabel(
                header,
                text=dependency_text,
                font=self.fonts["small_bold"],
            )
            dependency_label.grid(row=2, column=0, sticky="w", pady=(7, 0))

        switch = ctk.CTkSwitch(
            header,
            text="Enabled",
            font=self.fonts["small_bold"],
            command=lambda key=module_key: self.on_module_toggle(key),
        )
        switch.grid(row=0, column=1, rowspan=3, sticky="e", padx=(18, 0))

        if APP_CONFIG["modules"].get(module_key):
            switch.select()
        else:
            switch.deselect()

        settings_frame = ctk.CTkFrame(card, corner_radius=8)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        settings_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.module_switches[module_key] = switch
        self.module_cards[module_key] = card
        self.module_settings_frames[module_key] = settings_frame

        self._build_module_settings(module_key)

        if not switch.get():
            settings_frame.grid_remove()

    def _build_module_settings(self, module_key):
        """
        Builds the settings section for a module.

        Args:
            module_key: Internal module key.
        """
        settings_frame = self.module_settings_frames[module_key]
        metadata = MODULE_UI_CONFIG.get(module_key, {})
        settings = metadata.get("settings", [])

        for child in settings_frame.winfo_children():
            child.destroy()

        if not settings:
            empty_label = ctk.CTkLabel(
                settings_frame,
                text="This module has no specific settings.",
                font=self.fonts["small"],
            )
            empty_label.grid(row=0, column=0, sticky="w", padx=16, pady=14)
            return

        for index, (section, key) in enumerate(settings):
            self._add_setting_entry(
                parent=settings_frame,
                row=index // 3,
                column=index % 3,
                section=section,
                key=key,
            )

    def _add_setting_entry(self, parent, row, column, section, key):
        """
        Adds a text input field for a configuration value.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            section: Configuration section.
            key: Configuration key.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=12, pady=12)
        wrapper.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            wrapper,
            text=SETTING_LABELS.get(key, key),
            font=self.fonts["small_bold"],
            cursor="hand2",
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 7))

        Tooltip(
            label,
            SETTING_TOOLTIPS.get(key, "No description available for this setting."),
        )

        value = APP_CONFIG.get(section, {}).get(key, "")

        entry = ctk.CTkEntry(
            wrapper,
            height=40,
            font=self.fonts["small"],
        )
        entry.insert(0, self._format_setting_value(section, key, value))
        entry.grid(row=1, column=0, sticky="ew")

        self.config_entries[f"{section}.{key}"] = entry

    def _add_option_menu(self, parent, row, column, section, key, values):
        """
        Adds an option menu for a configuration value.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            section: Configuration section.
            key: Configuration key.
            values: Available option values.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=12, pady=12)
        wrapper.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            wrapper,
            text=SETTING_LABELS.get(key, key),
            font=self.fonts["small_bold"],
            cursor="hand2",
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 7))

        Tooltip(
            label,
            SETTING_TOOLTIPS.get(key, "No description available for this setting."),
        )

        option = ctk.CTkOptionMenu(
            wrapper,
            values=values,
            height=40,
            font=self.fonts["small"],
            dropdown_font=self.fonts["small"],
        )
        option.set(str(APP_CONFIG.get(section, {}).get(key, values[0])))
        option.grid(row=1, column=0, sticky="ew")

        self.config_entries[f"{section}.{key}"] = option

    def _add_switch_setting(self, parent, row, column, section, key, text):
        """
        Adds a switch for a boolean configuration value.

        Args:
            parent: Parent frame.
            row: Grid row.
            column: Grid column.
            section: Configuration section.
            key: Configuration key.
            text: Label text.
        """
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=12, pady=12)
        wrapper.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            wrapper,
            text=text,
            font=self.fonts["small_bold"],
            cursor="hand2",
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        Tooltip(
            label,
            SETTING_TOOLTIPS.get(key, "No description available for this setting."),
        )

        switch = ctk.CTkSwitch(
            wrapper,
            text="",
            font=self.fonts["small"],
        )
        switch.grid(row=1, column=0, sticky="w")

        if APP_CONFIG.get(section, {}).get(key):
            switch.select()
        else:
            switch.deselect()

        self.config_entries[f"{section}.{key}"] = switch

    def on_all_modules_toggle(self):
        """
        Handles the global module switch.

        When enabled, all modules are enabled. When disabled, all modules are
        disabled and their settings sections are hidden.
        """
        enable_all = bool(self.all_modules_switch.get())

        if enable_all:
            self._enable_all_modules()
            self.set_status(C.STATUS_ALL_MODULES_ENABLED)
        else:
            self._disable_all_modules()
            self.set_status(C.STATUS_ALL_MODULES_DISABLED)

    def _enable_all_modules(self):
        """
        Enables all modules and shows their settings sections.

        The activation follows APP_CONFIG order, which should place parent
        modules before dependent modules.
        """
        for module_key in APP_CONFIG["modules"].keys():
            switch = self.module_switches.get(module_key)

            if not switch:
                continue

            switch.select()
            self.module_settings_frames[module_key].grid()

        self._sync_all_modules_switch()

    def _disable_all_modules(self):
        """
        Disables all modules and hides their settings sections.
        """
        for module_key in APP_CONFIG["modules"].keys():
            switch = self.module_switches.get(module_key)

            if not switch:
                continue

            switch.deselect()
            self.module_settings_frames[module_key].grid_remove()

        self._sync_all_modules_switch()

    def _sync_all_modules_switch(self):
        """
        Synchronizes the global module switch with the individual module switches.

        If every module is enabled, the global switch is selected. Otherwise,
        it is deselected.
        """
        if not self.all_modules_switch:
            return

        all_enabled = all(
            bool(switch.get())
            for switch in self.module_switches.values()
        )

        if all_enabled:
            self.all_modules_switch.select()
        else:
            self.all_modules_switch.deselect()

    def on_module_toggle(self, module_key):
        """
        Handles module activation and dependency validation.

        Args:
            module_key: Internal module key.
        """
        switch = self.module_switches[module_key]

        if switch.get():
            if not self._dependencies_enabled(module_key):
                switch.deselect()

                missing = self._get_missing_dependencies(module_key)
                missing_names = [
                    MODULE_UI_CONFIG.get(dep, {}).get("title", dep)
                    for dep in missing
                ]

                self.set_status(f"Missing dependency: {', '.join(missing_names)}")
                self._sync_all_modules_switch()
                return

            self.module_settings_frames[module_key].grid()
            self.set_status(C.STATUS_READY)

        else:
            self.module_settings_frames[module_key].grid_remove()
            self._disable_children_of(module_key)
            self.set_status(C.STATUS_READY)

        self._sync_all_modules_switch()

    def _dependencies_enabled(self, module_key):
        """
        Checks whether all dependencies for a module are enabled.

        Args:
            module_key: Internal module key.

        Returns:
            bool: True if all dependencies are enabled, False otherwise.
        """
        missing = self._get_missing_dependencies(module_key)
        return len(missing) == 0

    def _get_missing_dependencies(self, module_key):
        """
        Gets the missing dependencies for a module.

        Args:
            module_key: Internal module key.

        Returns:
            list: Missing dependency module keys.
        """
        metadata = MODULE_UI_CONFIG.get(module_key, {})
        dependencies = metadata.get("depends_on", [])

        missing = []

        for dependency in dependencies:
            dependency_switch = self.module_switches.get(dependency)

            if not dependency_switch or not dependency_switch.get():
                missing.append(dependency)

        return missing

    def _disable_children_of(self, parent_module_key):
        """
        Disables every module that depends on the provided parent module.

        Args:
            parent_module_key: Module key used as dependency by other modules.
        """
        for module_key, metadata in MODULE_UI_CONFIG.items():
            dependencies = metadata.get("depends_on", [])

            if parent_module_key in dependencies:
                switch = self.module_switches.get(module_key)

                if switch and switch.get():
                    switch.deselect()
                    self.module_settings_frames[module_key].grid_remove()
                    self._disable_children_of(module_key)

    def get_target(self):
        """
        Gets the target domain entered by the user.

        Returns:
            str: Target domain.
        """
        return self.target_entry.get().strip()

    def set_status(self, text):
        """
        Updates the execution status label.

        Args:
            text: Status text.
        """
        if self.status_label:
            self.status_label.configure(text=text)

    def set_running_state(self, running):
        """
        Updates execution buttons according to the running state.

        Args:
            running: Whether an execution is currently running.
        """
        if self.run_button:
            self.run_button.configure(state="disabled" if running else "normal")

        if self.stop_button:
            self.stop_button.configure(state="normal" if running else "disabled")

    def set_cancelling_state(self):
        """
        Updates execution controls when cancellation has been requested.
        """
        if self.stop_button:
            self.stop_button.configure(state="disabled")

        self.set_status(C.STATUS_CANCELLING)

    def get_config_overrides(self):
        """
        Builds runtime configuration overrides from the UI values.

        Returns:
            dict: Configuration overrides to be merged with APP_CONFIG.
        """
        overrides = {
            "modules": {},
            "tools": {},
            "debug": {},
            "logging": {},
            "limits": {},
            "timeouts": {},
            "retries": {},
        }

        for module_key, switch in self.module_switches.items():
            overrides["modules"][module_key] = bool(switch.get())

        for full_key, widget in self.config_entries.items():
            section, key = full_key.split(".", 1)

            raw_value = self._get_widget_value(widget)
            parsed_value = self._parse_setting_value(section, key, raw_value)

            overrides[section][key] = parsed_value

        return overrides

    def get_persistent_state(self) -> dict:
        """
        Extracts the stable user-editable state of the execution page.

        This method is intended for JSON persistence. It stores only stable form
        values and excludes transient runtime state such as progress or current
        execution status.

        Returns:
            dict: Persistent execution form state.
        """
        return {
            "target": self.get_target(),
            "config_overrides": deepcopy(self.get_config_overrides()),
        }

    def apply_persistent_state(self, data: dict) -> None:
        """
        Applies persisted execution form values to the current page.

        Args:
            data: Persistent execution form state previously loaded from disk.
        """
        if not isinstance(data, dict):
            return

        target = data.get("target", "")
        config_overrides = data.get("config_overrides", {})

        self._apply_target_value(target)
        self._apply_config_overrides(config_overrides)

    def _apply_target_value(self, target: str) -> None:
        """
        Applies a persisted target value to the target input widget.

        Args:
            target: Persisted domain or target string.
        """
        if not self.target_entry:
            return

        try:
            self.target_entry.delete(0, "end")
            if target:
                self.target_entry.insert(0, target)
        except Exception:
            pass

    def _apply_config_overrides(self, config_overrides: dict) -> None:
        """
        Applies persisted configuration overrides to the page widgets.

        Args:
            config_overrides: Persisted runtime configuration overrides.
        """
        if not isinstance(config_overrides, dict):
            return

        self._load_overrides_into_widgets(config_overrides)

    def _load_overrides_into_widgets(self, config_overrides: dict) -> None:
        """
        Maps a persisted override dictionary back into the execution page widgets.

        Args:
            config_overrides: Persisted runtime configuration overrides.
        """
        modules = config_overrides.get("modules", {})
        if isinstance(modules, dict):
            for module_key, enabled in modules.items():
                switch = self.module_switches.get(module_key)
                frame = self.module_settings_frames.get(module_key)

                if not switch:
                    continue

                if enabled:
                    switch.select()
                    if frame:
                        frame.grid()
                else:
                    switch.deselect()
                    if frame:
                        frame.grid_remove()

            for module_key, switch in self.module_switches.items():
                if switch.get():
                    if not self._dependencies_enabled(module_key):
                        switch.deselect()
                        frame = self.module_settings_frames.get(module_key)
                        if frame:
                            frame.grid_remove()

            self._sync_all_modules_switch()

        for section, values in config_overrides.items():
            if section == "modules" or not isinstance(values, dict):
                continue

            for key, value in values.items():
                full_key = f"{section}.{key}"
                widget = self.config_entries.get(full_key)

                if not widget:
                    continue

                self._apply_widget_value(widget, value)

    def _apply_widget_value(self, widget, value) -> None:
        """
        Applies a persisted value to a supported CustomTkinter widget.

        Args:
            widget: Target widget.
            value: Persisted value.
        """
        try:
            if isinstance(widget, ctk.CTkSwitch):
                if bool(value):
                    widget.select()
                else:
                    widget.deselect()
                return

            if isinstance(widget, ctk.CTkOptionMenu):
                widget.set(str(value))
                return

            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
                widget.insert(0, str(value))
                return

        except Exception:
            pass

    def _get_widget_value(self, widget):
        """
        Extracts a value from a CustomTkinter widget.

        Args:
            widget: CustomTkinter widget.

        Returns:
            Any: Widget value.
        """
        if isinstance(widget, ctk.CTkSwitch):
            return bool(widget.get())

        if isinstance(widget, ctk.CTkOptionMenu):
            return widget.get()

        return widget.get().strip()

    def _format_setting_value(self, section, key, value):
        """
        Formats a configuration value before displaying it in the UI.

        Args:
            section: Configuration section.
            key: Configuration key.
            value: Raw value.

        Returns:
            str: Display-ready value.
        """
        return str(value)

    def _parse_setting_value(self, section, key, value):
        """
        Parses a UI value before sending it to the execution runner.

        Args:
            section: Configuration section.
            key: Configuration key.
            value: Raw UI value.

        Returns:
            Any: Parsed configuration value.
        """
        if isinstance(value, bool):
            return value

        if section in {"limits", "timeouts", "retries"}:
            try:
                return int(value)
            except ValueError:
                self.set_status(f"Invalid value: {SETTING_LABELS.get(key, key)}")
                return value

        return value

    def apply_theme(self, palette):
        """
        Applies the active theme to the execution page.

        Args:
            palette: Active theme palette.
        """
        self.configure(fg_color=palette["panel"])

        if self.execution_scroll:
            self.execution_scroll.configure(fg_color=palette["panel"])

        for card_widget in [
            self.execution_card,
            self.global_card,
            self.modules_card,
        ]:
            if card_widget:
                card_widget.configure(fg_color=palette["card"])

        for module_card in self.module_cards.values():
            module_card.configure(fg_color=palette["soft"])

        for settings_frame in self.module_settings_frames.values():
            settings_frame.configure(fg_color=palette["card"])

        if self.status_label:
            self.status_label.configure(
                fg_color=palette["soft"],
                text_color=palette["primary"],
            )

        if self.all_modules_switch:
            self.all_modules_switch.configure(
                progress_color=palette["primary"],
                button_color=palette["text"],
                button_hover_color=palette["primary_hover"],
                text_color=palette["text"],
            )

        if self.run_button:
            self.run_button.configure(
                fg_color=palette["primary"],
                hover_color=palette["primary_hover"],
                text_color=palette["inverse_text"],
            )

        if self.stop_button:
            self.stop_button.configure(
                fg_color=palette["danger"],
                hover_color=palette["danger_hover"],
                text_color="#FFFFFF",
            )