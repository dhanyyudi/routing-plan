import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSettingsDefaults:
    def test_default_endpoint(self):
        from routing_plan.core.settings import DEFAULT_ENDPOINT
        assert "valhalla" in DEFAULT_ENDPOINT

    def test_default_costing(self):
        from routing_plan.core.settings import DEFAULT_COSTING
        assert DEFAULT_COSTING == "auto"

    def test_default_language(self):
        from routing_plan.core.settings import DEFAULT_LANGUAGE
        assert DEFAULT_LANGUAGE == "en"

    def test_default_units(self):
        from routing_plan.core.settings import DEFAULT_UNITS
        assert DEFAULT_UNITS == "kilometers"

    def test_default_timeout(self):
        from routing_plan.core.settings import TIMEOUT_SECONDS
        assert TIMEOUT_SECONDS == 60

    def test_prefix_is_routing_plan(self):
        from routing_plan.core.settings import PREFIX
        assert "routing_plan" in PREFIX
