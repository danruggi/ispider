__all__ = ["ISpider"]


def __getattr__(name):
    if name == "ISpider":
        from .ispider import ISpider

        return ISpider
    raise AttributeError(name)
