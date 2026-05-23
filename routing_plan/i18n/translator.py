class Translator:
    def __init__(self, locale=None):
        if locale is None:
            from qgis.core import QgsSettings
            locale = QgsSettings().value("locale/userLocale", "id_ID")
        lang = locale[:2] if locale else "id"
        self._lang = lang if lang in ("en", "id") else "id"
        self._load_strings()

    def _load_strings(self):
        if self._lang == "en":
            from .strings import EN as _strings
        else:
            from .strings import ID as _strings
        self._strings = _strings

    def _(self, key, **kwargs):
        text = self._strings.get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text


_instance = None


def get_translator():
    global _instance
    if _instance is None:
        _instance = Translator()
    return _instance


def tr(key, **kwargs):
    return get_translator()._(key, **kwargs)
