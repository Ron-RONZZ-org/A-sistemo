"""Tests for Wi-Fi service — _deduplicate_networks."""

from __future__ import annotations

from A_sistemo.services.wifi_service import WiFiNetwork, _deduplicate_networks


class TestDeduplicateNetworks:
    """Pure-function tests for _deduplicate_networks (no nmcli needed)."""

    def test_dedup_keeps_best_signal(self) -> None:
        """Same SSID at multiple signal strengths — keep the strongest."""
        networks = [
            WiFiNetwork(name="MyWiFi", active=False, signal=40, security="WPA2"),
            WiFiNetwork(name="MyWiFi", active=False, signal=80, security="WPA2"),
            WiFiNetwork(name="MyWiFi", active=False, signal=60, security="WPA2"),
        ]
        result = _deduplicate_networks(networks)
        assert len(result) == 1
        assert result[0].signal == 80
        assert result[0].ap_count == 3

    def test_single_entry_passes_through(self) -> None:
        """Non-duplicated SSIDs pass through unchanged."""
        networks = [
            WiFiNetwork(name="A", active=False, signal=50),
            WiFiNetwork(name="B", active=False, signal=60),
            WiFiNetwork(name="C", active=False, signal=70),
        ]
        result = _deduplicate_networks(networks)
        assert len(result) == 3
        assert all(n.ap_count == 1 for n in result)

    def test_preserves_active_flag(self) -> None:
        """active=True if ANY entry for that SSID was active."""
        networks = [
            WiFiNetwork(name="Eduroam", active=False, signal=40),
            WiFiNetwork(name="Eduroam", active=True, signal=60),
            WiFiNetwork(name="Other", active=False, signal=90),
        ]
        result = _deduplicate_networks(networks)
        by_name = {n.name: n for n in result}
        assert by_name["Eduroam"].active is True
        assert by_name["Other"].active is False

    def test_prefers_active_on_equal_signal(self) -> None:
        """When signals are equal, prefer the active entry."""
        networks = [
            WiFiNetwork(name="Office", active=False, signal=70),
            WiFiNetwork(name="Office", active=True, signal=70),
        ]
        result = _deduplicate_networks(networks)
        assert result[0].active is True
        assert result[0].ap_count == 2

    def test_keeps_hidden_network_entries(self) -> None:
        """Networks with empty SSID (hidden) each stay as separate entries."""
        networks = [
            WiFiNetwork(name="", active=False, signal=80),
            WiFiNetwork(name="", active=False, signal=60),
            WiFiNetwork(name="Visible", active=False, signal=90),
        ]
        result = _deduplicate_networks(networks)
        # Empty SSIDs cannot be grouped — both pass through
        empty = [n for n in result if not n.name]
        visible = [n for n in result if n.name]
        assert len(empty) == 2
        assert len(visible) == 1

    def test_aggregates_ap_count(self) -> None:
        """ap_count reflects total BSSIDs for that SSID."""
        networks = [
            WiFiNetwork(name="Guest", active=False, signal=30),
            WiFiNetwork(name="Guest", active=False, signal=50),
            WiFiNetwork(name="Guest", active=False, signal=70),
            WiFiNetwork(name="Guest", active=False, signal=90),
            WiFiNetwork(name="Staff", active=False, signal=80),
        ]
        result = _deduplicate_networks(networks)
        by_name = {n.name: n for n in result}
        assert by_name["Guest"].ap_count == 4
        assert by_name["Staff"].ap_count == 1

    def test_empty_input(self) -> None:
        """Empty list returns empty list."""
        assert _deduplicate_networks([]) == []
