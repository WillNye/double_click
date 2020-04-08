import json
import math
import os
from datetime import datetime as dt, timedelta
from pathlib import Path

from double_click.request import GeneralSession, UserSession


class ModelAuth:

    def __init__(self, requires: list = None, match_all: bool = False, **kwargs):
        self.requires = requires
        self.match_all = match_all
        self.kwargs = kwargs
    

class Model:
    # This could be a double_click.UserSession or double_click.GeneralSession object
    _session: GeneralSession = None  # Define a class that inherits from Model to set a default session type
    _url: str = None
    _ttl = 120
    _cache_key = None
    _obj_identifier: any
    _auth: ModelAuth = ModelAuth(None, False)

    def __init__(self, **kwargs):
        self._url = kwargs.pop('url', self._url)
        self._session = kwargs.pop('session', self._session)
        if not isinstance(self._session, UserSession) and not isinstance(self._session, GeneralSession):
            self._session = GeneralSession(disable_progress_bar=False)

        self._as_dict = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    @classmethod
    def objects_identifier(cls, **kwargs) -> list:
        """Returns a list of values, primarily used for passing in click.Choice(Model.objects_keys())

        :param kwargs:
        :return: list
        """
        model = cls.objects_all(as_dict=True, **kwargs)
        return list(model.keys())

    @classmethod
    def objects_all(cls, as_dict: bool = False, **kwargs):
        """Returns all hits as a list of Model objects or dict(obj_identifier=item_as_dict).

        :param as_dict: If true (default False), the response will be a dict instead of a list of models
        :param kwargs:
        :return:
        """
        model = cls(**kwargs)
        content = model._cache_retrieve()
        if not content:
            content = model.refresh()

        if as_dict:
            return {item.get(model._obj_identifier): item for item in content}
        else:
            return [cls(**{**model, **kwargs}) for model in content]

    @classmethod
    def objects_get(cls, key, **kwargs):
        """Returns a Model object matching the provided key.

        :param key:
        :param kwargs:
        :return: cls
        """
        model_dict = cls.objects_all(as_dict=True)
        return cls(**{**model_dict.get(key, {}), **kwargs})

    def get(self, attr, default=None):
        """Perform a safe lookup on an instance of the Model with the ability to provide a default if attr not set.

        :param attr:
        :param default:
        :return:
        """
        val = getattr(self, attr, default)
        if val == default and default is not None:
            setattr(self, attr, default)
        return val

    def _cache_retrieve(self) -> list:
        """Protected method to retrieve model responses from cache.
        :return: list(requests.Response)
        """
        min_age = dt.now() - timedelta(minutes=self._ttl)
        cache_key = Path(os.path.expanduser(self._cache_key))
        if os.path.exists(cache_key) and dt.fromtimestamp(os.path.getmtime(cache_key)) < min_age:
            with open(cache_key) as config:
                return json.loads(config.read())

    def _cache_set(self, content):
        """Called by Model.refresh if _cache_key is not None. Protected method that sets cache content.

        :param content:
        """
        cache_key = Path(os.path.expanduser(self._cache_key))
        os.makedirs(os.path.dirname(cache_key), exist_ok=True)
        with open(cache_key, 'w') as config:
            config.write(json.dumps(content, indent=2))

    def _api_retrieve(self) -> list:
        """Protected method that retrieves all Model objects from the api.
        :return: list(requests.Response)
        """
        page = 1
        response = self._session.get(self._url, params=dict(page=page))
        if response.status_code >= 400:
            return []

        content = response.json()
        results = content.get('results', [])
        count = content.get('count')

        if len(results) < count:
            remaining_pages = math.ceil(count/len(results)) + 2  # account for 1 indexed val with page 1 complete
            request_list = [(self._url, dict(params=dict(page=page))) for page in range(2, remaining_pages)]
            responses = self._session.bulk_get(request_list)
            for response in responses:
                if response.status_code < 400:
                    content = response.json()
                    results += content.get('results', [])

        return results

    def refresh(self) -> list:
        """Syncs the local file with the service
        """
        if isinstance(self._session, UserSession) and not self._session.user.has_access(requires=self._auth.requires,
                                                                                        match_all=self._auth.match_all,
                                                                                        **self._auth.kwargs):
            return []

        content = self._api_retrieve()
        if content and self._cache_key:
            self._cache_set(content)
        return content

