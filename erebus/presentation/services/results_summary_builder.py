"""
Result summary builder for the EREBUS presentation layer.

This module transforms a structured ExecutionResponse into a compact,
user-friendly summary suitable for display in the graphical results page.

The goal is to present the most important findings and execution facts without
showing raw console output or low-level errors.
"""

from __future__ import annotations

from typing import Any

import presentation.constants as C
from presentation.module_ui_metadata import MODULE_UI_CONFIG


class ResultsSummaryBuilder:
    """
    Builds a compact UI-oriented summary from an ExecutionResponse.
    """

    def build(
        self,
        execution_response,
        config_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Builds a clean results summary.

        Args:
            execution_response: Structured execution response returned by the
                engine runner.
            config_overrides: Runtime configuration overrides used for the
                execution. This is used to identify which modules were enabled.

        Returns:
            dict[str, Any]: Structured summary for the results page.
        """
        modules = execution_response.modules or []
        active_modules = self._extract_active_modules(config_overrides)
        total_duration = sum(
            module.duration_seconds or 0
            for module in modules
        )

        module_cards = []
        aggregated_metrics = {}

        for module in modules:
            metrics = module.metrics or {}
            self._merge_important_metrics(aggregated_metrics, metrics)

            module_cards.append(
                {
                    "module_key": module.module_name,
                    "title": MODULE_UI_CONFIG.get(module.module_name, {}).get(
                        "title",
                        module.module_name,
                    ),
                    "status": self._normalize_status(module.status),
                    "duration_seconds": module.duration_seconds or 0,
                    "highlights": self._extract_module_highlights(metrics),
                }
            )

        return {
            "target": execution_response.target,
            "execution_id": execution_response.execution_id,
            "started_at": execution_response.started_at,
            "status": self._infer_final_status(modules),
            "total_duration_seconds": total_duration,
            "active_modules": active_modules,
            "global_highlights": self._format_global_highlights(aggregated_metrics),
            "module_cards": module_cards,
        }

    def _extract_active_modules(
        self,
        config_overrides: dict[str, Any] | None,
    ) -> list[dict[str, str]]:
        """
        Extracts the enabled modules from runtime configuration overrides.

        Args:
            config_overrides: Runtime configuration overrides.

        Returns:
            list[dict[str, str]]: Enabled module keys and titles.
        """
        if not isinstance(config_overrides, dict):
            return []

        modules = config_overrides.get("modules", {})
        if not isinstance(modules, dict):
            return []

        active = []

        for module_key, enabled in modules.items():
            if not enabled:
                continue

            active.append(
                {
                    "key": module_key,
                    "title": MODULE_UI_CONFIG.get(module_key, {}).get(
                        "title",
                        module_key,
                    ),
                }
            )

        return active

    def _merge_important_metrics(
        self,
        aggregate: dict[str, int],
        metrics: dict[str, Any],
    ) -> None:
        """
        Merges only important numeric metrics into the aggregate summary.

        Args:
            aggregate: Aggregate metrics dictionary updated in place.
            metrics: Module metrics dictionary.
        """
        for key in C.RESULTS_IMPORTANT_METRIC_ORDER:
            value = metrics.get(key)

            if isinstance(value, int):
                aggregate[key] = aggregate.get(key, 0) + value

    def _extract_module_highlights(
        self,
        metrics: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extracts the most important metrics for one module card.

        Args:
            metrics: Module metrics.

        Returns:
            list[dict[str, Any]]: Formatted module highlights.
        """
        highlights = []

        for key in C.RESULTS_IMPORTANT_METRIC_ORDER:
            value = metrics.get(key)

            if isinstance(value, int) and value > 0:
                highlights.append(
                    {
                        "label": C.RESULTS_METRIC_LABELS.get(key, key),
                        "value": value,
                    }
                )

            if len(highlights) >= 5:
                break

        return highlights

    def _format_global_highlights(
        self,
        aggregated_metrics: dict[str, int],
    ) -> list[dict[str, Any]]:
        """
        Formats the global highlights for the top summary card.

        Args:
            aggregated_metrics: Aggregated important metrics.

        Returns:
            list[dict[str, Any]]: Formatted global highlights.
        """
        highlights = []

        for key in C.RESULTS_IMPORTANT_METRIC_ORDER:
            value = aggregated_metrics.get(key)

            if isinstance(value, int) and value > 0:
                highlights.append(
                    {
                        "label": C.RESULTS_METRIC_LABELS.get(key, key),
                        "value": value,
                    }
                )

        return highlights

    def _infer_final_status(self, modules) -> str:
        """
        Infers the final execution status from the module responses.

        Rules:
            SUCCESS:
                Every executed module finished successfully.

            PARTIAL:
                At least one module failed or ended partially, but at least one
                executed module completed successfully.

            FAILED:
                Every executed module failed, or there are no successful module
                results at all and at least one module failed.

            SKIPPED:
                Every module was skipped.

            UNKNOWN:
                Modules exist, but their statuses cannot be interpreted.

        Args:
            modules: Module responses.

        Returns:
            str: Human-readable final status.
        """
        if not modules:
            return C.RESULTS_NO_RESULTS

        statuses = [
            self._normalize_status(module.status)
            for module in modules
        ]

        statuses = [
            status
            for status in statuses
            if status
        ]

        if not statuses:
            return "UNKNOWN"

        skipped_count = statuses.count("SKIPPED")
        success_count = statuses.count("SUCCESS")
        partial_count = statuses.count("PARTIAL")
        failed_count = statuses.count("FAILED")

        executable_count = len(statuses) - skipped_count

        if executable_count <= 0:
            return "SKIPPED"

        if failed_count == executable_count:
            return "FAILED"

        if failed_count > 0 or partial_count > 0:
            return "PARTIAL"

        if success_count == executable_count:
            return "SUCCESS"

        return "PARTIAL"

    def _normalize_status(self, status) -> str:
        """
        Normalizes a raw module status into a clean uppercase label.

        Args:
            status: Raw status value. It can be an enum, string or None.

        Returns:
            str: Normalized status label.
        """
        if status is None:
            return "UNKNOWN"

        normalized = str(status).strip().upper()

        if "." in normalized:
            normalized = normalized.split(".")[-1]

        return normalized or "UNKNOWN"