PREFIX = "routing_plan/"
DEFAULT_ENDPOINT_VALHALLA = "https://valhalla.dhanypedia.it.com"
DEFAULT_ENDPOINT_OSRM = "https://router.project-osrm.org"
DEFAULT_ENGINE = "valhalla"
DEFAULT_COSTING = "auto"
DEFAULT_LANGUAGE = "en"
DEFAULT_UNITS = "kilometers"
TIMEOUT_SECONDS = 60
# Backwards-compat alias
DEFAULT_ENDPOINT = DEFAULT_ENDPOINT_VALHALLA


def _s(key):
    return PREFIX + key


def _settings():
    from qgis.core import QgsSettings
    return QgsSettings()


class PluginSettings:
    @staticmethod
    def get_engine():
        return _settings().value(_s("engine"), DEFAULT_ENGINE)

    @staticmethod
    def set_engine(name):
        _settings().setValue(_s("engine"), name)

    @staticmethod
    def get_endpoint():
        """Return the active engine's endpoint for backwards compat."""
        eng = PluginSettings.get_engine()
        return PluginSettings.get_endpoint_for(eng)

    @staticmethod
    def set_endpoint(url):
        """Set the active engine's endpoint for backwards compat."""
        eng = PluginSettings.get_engine()
        PluginSettings.set_endpoint_for(eng, url)

    @staticmethod
    def get_endpoint_for(engine):
        default = DEFAULT_ENDPOINT_VALHALLA if engine == "valhalla" else DEFAULT_ENDPOINT_OSRM
        return _settings().value(_s(f"endpoint_{engine}"), default)

    @staticmethod
    def set_endpoint_for(engine, url):
        _settings().setValue(_s(f"endpoint_{engine}"), url.rstrip("/"))

    @staticmethod
    def get_osrm_warning_shown():
        return _settings().value(_s("osrm_warning_shown"), False, type=bool)

    @staticmethod
    def set_osrm_warning_shown(val):
        _settings().setValue(_s("osrm_warning_shown"), bool(val))

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
            "engine": PluginSettings.get_engine(),
            "endpoint_valhalla": PluginSettings.get_endpoint_for("valhalla"),
            "endpoint_osrm": PluginSettings.get_endpoint_for("osrm"),
            "default_costing": PluginSettings.get_default_costing(),
            "language": PluginSettings.get_language(),
            "units": PluginSettings.get_units(),
            "timeout": PluginSettings.get_timeout(),
        }

    @staticmethod
    def reset_all():
        s = _settings()
        for key in ["engine", "endpoint_valhalla", "endpoint_osrm",
                    "default_costing", "language", "units", "timeout"]:
            s.remove(_s(key))
