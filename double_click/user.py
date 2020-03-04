class User:

    def __init__(self, username: str = None, access: dict = {}, **kwargs):
        """
        !access_dict structure matters, it will impact the response of ActiveUser.has_access!
        This allows dynamic resolution to help support as many authorization models as possible.
        For example, the way you would auth using permissions is different in these two access_dict structures:
            dict(service=dict(svc_name=dict(list(roles), list(permissions))))
            dict(service=dict(svc_name=dict(role=dict(role_name=list(permissions)))))

        :param username:
        :param access_dict:
        :param kwargs:
        """
        self.username = username
        self.access = access

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def access(self) -> dict:
        """
        :return: dict
        """
        return self._access_dict

    @access.setter
    def access(self, access_dict):
        if isinstance(access_dict, dict):
            self._access_dict = access_dict
        else:
            raise ValueError(f'access attribute must be of type dict not {type(access_dict)}')

    def get(self, attr, default=None):
        """Retrieves the attr value from the instance of the class, setting default if not exists.

        :param attr:
        :param default:
        :return: self.attr
        """
        val = getattr(self, attr, default)
        if val == default and default is not None:
            setattr(self, attr, default)

        return val

    def hide(self, requires: list = None, match_all: bool = False, **kwargs) -> bool:
        """Used for click.command(hidden=this.hide) or click.

        :param requires: list of roles that a user must have one or more of
        :param match_all: (default: False) If true a user must have all roles passed in required_roles
        :return: bool
        """
        return not self.has_access(requires, match_all, **kwargs)

    def has_access(self, requires: list = None, match_all: bool = False, **kwargs) -> bool:
        """Overwrite this for custom authorization

        Pass in the key space of the roles as kwargs.
        `requires` can be a list of whatever you want from the service, role, permission, etc.
            note: The preceding key must be passed
                    so if user permissions look like dict(service=dict(svc_name=dict(list(roles), list(permissions))))
                    the service name must be provided when passing a list of permissions, not just the permissions.

        :param requires: list of roles that a user must have one or more of represented
        :param match_all: (default: False) If true a user must have all roles passed in required_roles
        :return: bool
        """
        access = self.access
        if kwargs is None and requires is None:
            return True

        while kwargs:  # Walk user access by mapping kwarg keys to current depth of user.access
            key_hits = [key for key in kwargs.keys() if key in access.keys()]
            if len(key_hits) == 0:
                return False
            elif len(key_hits) == 1:
                access = access[key_hits[0]].get(kwargs.pop(key_hits[0]))
                if access is None:
                    return False
            else:
                raise ValueError(f'Invalid access structure. {self.username} hit on multiple keys {key_hits}')

        auth_list = [k for k in access.keys()]

        if requires is None:
            return True

        for _, value in access.items():
            if isinstance(value, list):
                auth_list += value

        if match_all:
            return all(authed in auth_list for authed in requires)
        else:
            return any(authed in auth_list for authed in requires)

    def authenticate(self, **kwargs) -> dict:
        raise NotImplementedError

