import json
import math
import os
from datetime import datetime as dt, timedelta

from aiovast.requests import VastSession

from double_click.user import UserSession


class Model:
    # This could be a double_click.UserSession, requests.Session, or aiovast.requests.VastSession obj
    session = None  # Define a class that inherits from Model to set a default session type
    url: str = None

    def __init__(self, **kwargs):
        self._options_dict = {}
        self._choice_list = []
        self._content = []
        self._dict_ref = {}
        self.session = kwargs.get('session', self.session)
        self.url = kwargs.get('url', self.url)

        if not isinstance(self.session, UserSession) and not isinstance(self.session, VastSession):
            self.session = VastSession(disable_progress_bar=False)

        if self._file_path:
            min_age = dt.now() - timedelta(minutes=self._ttl)
            if not os.path.exists(self._file_path) or dt.fromtimestamp(os.path.getmtime(self._file_path)) < min_age:
                self.update()
            else:
                with open(self._file_path) as config:
                    self._content = json.loads(config.read())
                    self._set()
        else:
            self.update()

    @property
    def _ttl(self):
        """Time to live. The local file cache will be refreshed after this number, in minutes, has passed.
        """
        return 120

    @property
    def _file_path(self):
        """Location where the http response is stored locally. If none, response will not be stored.
        """
        return None

    @property
    def _key_identifier(self):
        """The dictionary key to use for grouping the objects by, e.g. name.
        """
        raise NotImplementedError

    @property
    def _requires_roles(self) -> tuple:
        """The roles required to view the resource and if all roles are required.

        tuple[0] = required_roles
        tuple[1] = User must have all roles within required_roles if True

        Default is None, False which means no auth.
        """
        return None, False

    @classmethod
    def choices(cls, **kwargs):
        return cls(**kwargs)._choice_list

    @classmethod
    def all(cls, as_dict: bool = False, **kwargs):
        if not as_dict:
            pass
        else:
            return cls(**kwargs)._content

    @classmethod
    def get_object(cls, key, **kwargs):
        model = cls(**kwargs)
        model._dict_ref = model._options_dict.get(key)
        for key, value in model.to_dict().items():
            setattr(model, key, value)

        return model

    def get(self, attr, default=None):
        val = getattr(self, attr, default)
        if val == default and not isinstance(default, None):
            setattr(self, attr, default)

        return val

    def to_dict(self):
        return self._dict_ref

    def _api_get(self):
        """Protected method to retrieve the objects
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
            responses = self.session.get_request(request_list)

            for response in responses:
                if response.status_code < 400:
                    content = response.json()
                    results += content.get('results', [])

        return results

    def _set(self):
        """Sets _choice_list and _options_dict by grouping content using the _key_identifier
        """
        for item in self.all(as_dict=True):
            self._choice_list.append(item.get(self._key_identifier))
            self._options_dict[item.get(self._key_identifier)] = item

    def update(self):
        """Overwrite this for custom authorization
        """
        if not self.session.user.has_access(*self._requires_roles):
            return False

        content = self._api_get()
        self._content = content if len(content) > 0 else self._content
        self._set()

        if self._file_path:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, 'w') as config:
                config.write(json.dumps(self.list, indent=4))



