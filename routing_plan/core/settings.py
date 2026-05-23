PREFIX = "routing_plan/"
DEFAULT_ENDPOINT = "https://valhalla.dhanypedia.it.com"
DEFAULT_COSTING = "auto"
DEFAULT_LANGUAGE = "en"
DEFAULT_UNITS = "kilometers"
TIMEOUT_SECONDS = 60


def _s(key):
    return PREFIX + key


def _settings():
    from qgis.core import QgsSettings
    return QgsSettings()


class PluginSettings:
    @staticmethod
    def get_endpoint():
        return _settings().value(_s("endpoint"), DEFAULT_ENDPOINT)

    @staticmethod
    def set_endpoint(url):
        _settings().setValue(_s("endpoint"), url.rstrip("/"))

    @staticmethod
    def get_default_costing():
        return _settings().value(_s("default_costing"), DEFAULT_COSTING)

    @staticmethod
    def set_default_costing(costing):
        _settings().setValue(_s("default_costing"), costing)

    @staticmethod
    def get_language():
        return _settings().value(_s("language"), DEFAULT_LANGUAGE)

    @staticmethod
    def set_language(lang):
        _settings().setValue(_s("language"), lang)

    @staticmethod
    def get_units():
        return _settings().value(_s("units"), DEFAULT_UNITS)

    @staticmethod
    def set_units(units):
        _settings().setValue(_s("units"), units)

    @staticmethod
    def get_timeout():
        return int(_settings().value(_s("timeout"), TIMEOUT_SECONDS))

    @staticmethod
    def set_timeout(secs):
        _settings().setValue(_s("timeout"), int(secs))

    @staticmethod
    def get_auto_clear_previous():
        return _settings().value(_s("auto_clear_previous"), True, type=bool)

    @staticmethod
    def set_auto_clear_previous(val):
        _settings().setValue(_s("auto_clear_previous"), bool(val))

    @staticmethod
    def to_dict():
        return {
            "endpoint": PluginSettings.get_endpoint(),
            "default_costing": PluginSettings.get_default_costing(),
            "language": PluginSettings.get_language(),
            "units": PluginSettings.get_units(),
            "timeout": PluginSettings.get_timeout(),
        }

    @staticmethod
    def reset_all():
        s = _settings()
        for key in ["endpoint", "default_costing", "language", "units", "timeout"]:
            s.remove(_s(key))
