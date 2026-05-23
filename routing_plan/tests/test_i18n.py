import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from routing_plan.i18n.translator import Translator


class TestTranslator:
    def test_id_locale_loads_id_strings(self):
        t = Translator(locale="id_ID")
        assert t._("directions") == "Petunjuk Arah"

    def test_en_locale_loads_en_strings(self):
        t = Translator(locale="en_US")
        assert t._("directions") == "Directions"

    def test_unknown_locale_falls_back_to_id(self):
        t = Translator(locale="fr_FR")
        assert t._("directions") == "Petunjuk Arah"

    def test_missing_key_returns_key(self):
        t = Translator(locale="en_US")
        assert t._("nonexistent_key") == "nonexistent_key"

    def test_format_kwargs(self):
        t = Translator(locale="en_US")
        result = t._("html_saved", path="/tmp/test.html")
        assert "/tmp/test.html" in result

    def test_id_format_kwargs(self):
        t = Translator(locale="id_ID")
        result = t._("html_saved", path="/tmp/test.html")
        assert "/tmp/test.html" in result
        assert "HTML" in result

    def test_no_format_kwargs_safe(self):
        t = Translator(locale="en_US")
        result = t._("cancel")
        assert result == "Cancel"

    def test_all_keys_defined_in_both_locales(self):
        from routing_plan.i18n.strings import ID, EN
        for key in ID:
            assert key in EN, f"Key '{key}' missing in EN"
        for key in EN:
            assert key in ID, f"Key '{key}' missing in ID"

    def test_singleton_reuses_instance(self):
        import routing_plan.i18n.translator as mod
        mod._instance = None
        # create with explicit locale to avoid QgsSettings import
        mod._instance = Translator(locale="id_ID")
        t1 = mod.get_translator()
        t2 = mod.get_translator()
        assert t1 is t2
        mod._instance = None
