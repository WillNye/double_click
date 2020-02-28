import json
import math
import os
from datetime import datetime as dt, timedelta

from double_click.request import GeneralSession, UserSession
    

class Model:
    # This could be a double_click.UserSession or double_click.GeneralSession object
    session: GeneralSession = None  # Define a class that inherits from Model to set a default session type
    url: str = None

    def __init__(self, **kwargs):
        self.url = kwargs.pop('url', self.url)
        self.session = kwargs.pop('session', self.session)
        if not isinstance(self.session, UserSession) and not isinstance(self.session, GeneralSession):
            self.session = GeneralSession(disable_progress_bar=False)

        self._as_dict = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def ttl(self):
        """Time to live. The local file cache will be refreshed after this number, in minutes, has passed.
        """
        return 120

    @property
    def file_path(self):
        """Location where the http response is stored locally. If none, response will not be stored.
        """
        return None

    @property
    def key_identifier(self):
        """The dictionary key to use for grouping the objects by, e.g. name.
        """
        raise NotImplementedError

    @property
    def requires(self) -> tuple:
        """The roles required to view the resource and if all roles are required.

        tuple[0] = required_roles
        tuple[1] = User must have all roles within required_roles if True
        tuple[2] = Passed as kwargs, operating similar to User.has_access

        Default is None, False, {} which means no auth.
        """
        return None, False, {}

    @property
    def as_dict(self):
        return self._as_dict

    @classmethod
    def _with_content(cls, **kwargs) -> dict:
        """Retrieves data from cache or API to be used object_* classmethods

        :param kwargs:
        :return: dict
        """
        model = cls(**kwargs)
        min_age = dt.now() - timedelta(minutes=model.ttl)
        if not os.path.exists(model.file_path) or dt.fromtimestamp(os.path.getmtime(model.file_path)) < min_age:
            return model._api_retrieve()
        else:
            with open(model.file_path) as config:
                return json.loads(config.read())

    @classmethod
    def objects_keys(cls, **kwargs) -> list:
        """Returns a list of values, primarily used for passing in click.Choice(Model.objects_keys())

        :param kwargs:
        :return: list
        """
        content = cls._with_content(**kwargs)
        model = cls(**kwargs)
        return [item.get(model.key_identifier) for item in content]

    @classmethod
    def objects_all(cls, as_dict: bool = False, **kwargs):
        """Returns all hits as a list of Model objects or dict(key_identifier=item_as_dict).

        :param as_dict: If true (default False), the response will be a dict instead of a list of models
        :param kwargs:
        :return:
        """
        content = cls._with_content(**kwargs)
        if as_dict:
            model = cls(**kwargs)
            return {item.get(model.key_identifier): item for item in content}
        else:
            return [cls(**{**model, **kwargs}) for model in content]

    @classmethod
    def objects_get(cls, key, **kwargs):
        """Returns a Model object matching the provided key.

        :param key:
        :param kwargs:
        :return: cls
        """
        model = cls.objects_all(as_dict=True)
        return cls(**{**model.get(key), **kwargs})

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

    def _api_retrieve(self):
        """Protected method to retrieve and all Model objects. Used within Model.objects.refresh
        :return: list(requests.Response)
        """
        page = 1
        response = self.session.get(self.url, params=dict(page=page))
        if response.status_code >= 400:
            return []

        content = response.json()
        results = content.get('results', [])
        count = content.get('count')

        if len(results) < count:
            remaining_pages = math.ceil(count/len(results)) + 2  # account for 1 indexed val with page 1 complete
            request_list = [(self.url, dict(params=dict(page=page))) for page in range(2, remaining_pages)]
            responses = self.session.bulk_get(request_list)
            for response in responses:
                if response.status_code < 400:
                    content = response.json()
                    results += content.get('results', [])

        return results

    def refresh(self):
        """Syncs the local file with the service
        """
        kwargs = self.requires[2] if len(self.requires) > 2 and isinstance(self.requires[2], dict) else {}
        if isinstance(self.session, UserSession) and not self.session.user.has_access(requires=list(self.requires[0]),
                                                                                      match_all=bool(self.requires[1]),
                                                                                      **kwargs):
            return False

        content = self._api_retrieve()
        if content and self.file_path:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as config:
                config.write(json.dumps(content, indent=4))

        return content

