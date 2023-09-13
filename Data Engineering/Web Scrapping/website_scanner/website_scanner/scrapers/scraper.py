from abc import ABC, abstractmethod

class Scraper(ABC) :

    @abstractmethod
    def __init__(self) -> None : ...

    def __post_init__(self) -> None :
        self._has_required_attributes()
        
    def _has_required_attributes(self):
        req_attrs = []
        for attr in req_attrs:
            if not hasattr(self, attr):
                raise AttributeError("Missing attribute "+attr)

    @abstractmethod
    def get_raw_HTML(self) -> str : ...

    @abstractmethod
    def set_site(self, site: str) -> None: ...
    
    @abstractmethod
    def close_session(self) -> None: ...