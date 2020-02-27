class User:

    def __init__(self, username: str = None, access_dict: dict = {}, **kwargs):
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
        self._access_dict = access_dict

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def access(self):
        """
        :return: dict
        """
        return self._access_dict

    def get(self, attr, default=None):
        """Retrieves the attr value from the instance of the class, setting default if not exists.

        :param attr:
        :param default:
        :return: self.attr
        """
        val = getattr(self, attr, default)
        if val == default and default is None:
            setattr(self, attr, default)

        return val

    def update_access(self, access_dict):
        self._access_dict = access_dict

    def hide(self, required_roles: list = None, requires_all: bool = False):
        """Used for click.command(hidden=this.hide) or click.

        :param required_roles: list of roles that a user must have one or more of
        :param requires_all: (default: False) If true a user must have all roles passed in required_roles
        :return: bool
        """
        return not self.has_access(required_roles, requires_all)

    def has_access(self, requires: list = None, match_all: bool = False, **kwargs):
        """Overwrite this for custom authorization

        Pass in the key space of the roles as kwargs.
        `requires` can be a list of whatever you want from the service, role, permission, etc.
            note: The preceding key must be passed
                    so if user permissions look like dict(service=dict(svc_name=dict(list(roles), list(permissions))))
                    the service name must be provided when passing a list of permissions, not just the permissions.

        For example, if permissions dict looks like service=dict(svc_name=dict(list(roles), list(permissions))))
            Valid:
                user.has_access()
                user.has_access(requires=['service1'])
                user.has_access(requires=['employee', 'manager'], service=service1)
                user.has_access(requires=['add_user', 'update_user'], match_all = True, service=service1)

                OR in the case of service=dict(svc_name=dict(role=dict(role_name=list(permissions)))))
                    user.has_access(requires=['add_user'], service=service1, role=employee)
            Invalid:
                user.has_access(requires=['employee', 'manager'])

                OR in the case of service=dict(svc_name=dict(role=dict(role_name=list(permissions))))
                    user.has_access(requires=['add_user'], service=service1)

        :param requires: list of roles that a user must have one or more of represented
        :param match_all: (default: False) If true a user must have all roles passed in required_roles
        :return: bool
        """
        access = self.access

        if requires is None:
            return True

        while kwargs:
            key_hits = [key for key in kwargs.keys() if key in access.keys()]
            if key_hits == 0:
                return False
            elif key_hits == 1:
                access.pop(key_hits[0])
            else:
                raise ValueError(f'Invalid access structure. {self.username} hit on multiple keys {key_hits}')

        auth_list = []
        for key, list_val in access.items():
            auth_list.append(key)
            if isinstance(list_val, list):
                auth_list.append(list_val)

        if match_all:
            return all(authed in requires for authed in auth_list)
        else:
            return any(authed in requires for authed in auth_list)

    def authenticate(self, **kwargs):
        raise NotImplementedError
