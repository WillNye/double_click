# Double Click
> API centric CLIs made easy using Click and Python3.7+

### Why use Double Click?
Double Click removes the boiler plate of CLIs that primarily communicate with an API by adding features to integrate with Click like:
* User permissions - Hide command if user doesn't have access
* HTTP Session management - refresh auth during long running async operations
* HTTP Sessions tied to a user - Allows for things like `all_roles = {**google_session.user.access, **duo_session.user.access`
* Use HTTP response for click.Choices instead of hard coded values that may not be viable e.g. users
* Normalizing a requests.Response object to a human readable value
* Catching exceptions during async http requests and normalizing to a human readable value
* Displaying complex structures like a bullet list, table, or code snippets in the terminal.
* Local file caching for large API responses with custom TTL

- [ Installation ](#installation)
- [ Classes ](#classes)
    - [ double_click.user.User ](#user)    
        - [ User.access ](#user-access)  
        - [ User.get ](#user-get)
        - [ User.has_access ](#user-has-access) 
        - [ User.hide ](#user-hide)
        - [ User.authenticate ](#user-authenticate)
    - [ double_click.request.GeneralSession ](#general-session)
    - [ double_click.request.UserSession ](#user-session)
    - [ double_click.models.ModelAuth ](#modelauth)
    - [ double_click.models.Model ](#model)
        - [ Model.as_dict ](#model-as-dict)
        - [ Model.objects_all ](#model-objects-all)
        - [ Model.objects_get ](#model-objects-get)
        - [ Model.objects_identifier ](#model-objects-identifier)
        - [ Model._cache_set ](#model-cache-set)
        - [ Model._cache_retrieve ](#model-cache-retrieve)
        - [ Model._api_retrieve ](#model-api-retrieve)
        - [ Model.get ](#model-get)
        - [ Model.refresh ](#model-refresh)
- [ Helper Functions ](#functions)  
    - [ double_click.utils.echo ](#echo) 
    - [ double_click.utils.display_version ](#display-version)
    - [ double_click.utils.update_package ](#update-package)
    - [ double_click.utils.ensure_latest_package ](#ensure-latest-package) 
    - [ double_click.request.is_valid_url ](#is-valid-url) 
    - [ double_click.markdown.generate_md_table_str ](#md-table-str)
    - [ double_click.markdown.double_click.utils.generate_md_bullet_str ](#md-bullet-str) 
    - [ double_click.markdown.double_click.utils.generate_md_code_str ](#md-code-str)

<a name="installation"></a>
## Installation
* Create a virtual environment with python 3.7+

```bash
pip3 install double_click
```

<br>

<a name="classes"></a>
## Classes
<br>

<a name="user"></a>
### double_click.user.User(username: str = None, access_dict: dict = {}, **kwargs)
A base class meant to represent a single user, their permissions, and attributes available via `User.access`.
Typically used by `double_click.request.UserSession` but can be used as a standalone class.

*Required overrides:*
`authenticate() -> dict` must be implemented for any child class being used by a `UserSession` class.

---
<br>

<a name="user-access"></a>
#### `User.access -> dict`
The dict representation of a user.
<b>structure matters, it will impact the response of ActiveUser.has_access</b>
This allows dynamic resolution to help support as many authorization models as possible including RBAC and ABAC.
For example, the way you would auth using permissions is different in these two access_dict structures:
    `dict(service=dict(svc_name=dict(list(roles), list(permissions))))`
    `dict(service=dict(svc_name=dict(role=dict(role_name=list(permissions)))))`

---
<br>

<a name="user-get"></a>
#### `User.get(attr, default=None) -> any`
Retrieves the attr value from the instance of the class, setting default if not exists.

```python
# Example
from double_click import User

class GoogleUser(User):

    def authenticate(self, **kwargs):
        return {}
    
google_user = GoogleUser(username='TestUser')
google_user.api_key  # Throws attribute error
google_user.get('api_key') # Returns None  
google_user.get('api_key', 'ABC') # Returns ABC  
google_user.api_key  # Returns ABC  
```

---
<br>

<a name="user-has-access"></a>
#### `User.has_access(requires: list = None, match_all: bool = False, **kwargs) -> bool`
Used to determine if a user has the ability to access a resource based on the provided arguments. 
For custom auth, override or overload this method.

`requires` can be a list of whatever you want from the service, role, permission, etc.
> The preceding key must be passed so if user permissions look like dict(service=dict(svc_name=dict(list(roles), list(permissions)))) the service name must be provided when passing a list of permissions, not just the permissions.

```python
# Example
from double_click import User

class GoogleUser(User):

    def authenticate(self, **kwargs):
        return {}
    
access = dict(service=dict(Photos=dict(permissions=['Create', 'View', 'List'], roles=['Manager'])))
google_user = GoogleUser(username='TestUser', access=access)
print(google_user.has_access(service='Photos'))  # True
print(google_user.has_access(requires=['View'], service='Photos'))  # True
print(google_user.has_access(requires=['Manager'], service='Photos'))  # True
print(google_user.has_access(requires=['View', 'Update'], service='Photos'))  # True
print(google_user.has_access(requires=['View', 'List'], match_all=True, service='Photos'))  # True
print(google_user.has_access(requires=['View', 'Update'], match_all=True, service='Photos'))  # False
print(google_user.has_access(requires=['Manager']))  # False
```

---
<br>

<a name="user-hide"></a>
#### `User.hide(requires: list = None, match_all: bool = False, **kwargs) -> bool`
The negation of `User.has_access`. 
Primarily used for `click.command(hidden=user.hide())` or `click.group(hidden=user.hide())`

```python
# Example
from double_click import User

class GoogleUser(User):

    def authenticate(self, **kwargs):
        return {}
    
access = dict(service=dict(Photos=dict(permissions=['Create', 'View', 'List'], roles=['Manager'])))
google_user = GoogleUser(username='TestUser', access=access)
print(google_user.hide(service='Photos'))  # False
print(google_user.hide(requires=['View'], service='Photos'))  # False
print(google_user.hide(requires=['Manager'], service='Photos'))  # False
print(google_user.hide(requires=['Update'], service='Photos'))  # True
print(google_user.hide(requires=['Admin'], service='Photos'))  # True
```

---
<br>

<a name="user-authenticate"></a>
#### `User.authenticate(**kwargs)`
Called by UserSession.refresh_auth authenticate retrieves user token/key/etc. and returns the auth header.

Here is an example of how User.authenticate can be leveraged with a login classmethod and file caching (Mac example).
On login, a check is done to validate PROFILE_DIR exists. If it does and the token is valid, set the cls obj and return it.
If not, authenticate is called. authenticate calls set_user which gets the user access token, and roles which are returned as a dict.
authenticate takes the response, storing it in PROFILE_DIR and setting the class attributes.

```python
import json
import os
import sys
from datetime import datetime as dt, timedelta
from pathlib import Path

import requests
from double_click import echo, User

PROFILE_DIR = os.path.join(Path(os.path.getenv('TMPDIR')), 'google_cli/user.json')


class GoogleUser(User):
    password: str

    @classmethod
    def login(cls, username: str = None, password: str = None, **kwargs):
        """Used by Session and reset password. Check file cache, if empty or expired, get updated token and access.
        """
        google_usr = cls(username=username, password=password, **kwargs)

        if os.path.exists(PROFILE_DIR):
            min_age = dt.now() - timedelta(minutes=10)
            filetime = dt.fromtimestamp(os.path.getmtime(PROFILE_DIR))

            try:
                with open(PROFILE_DIR) as config:
                    credentials = json.loads(config.read())

                    if filetime > min_age:
                        google_usr.access = dict(service=credentials.pop('roles'))
                        for key, value in credentials.items():
                            setattr(google_usr, key, value)
                    else:
                        google_usr.username = credentials.pop('username', username)
                        google_usr.password = credentials.pop('password', password)
                        google_usr.authenticate()
            except json.decoder.JSONDecodeError:
                echo(f'Profile format invalid. Defaulting to {username}')
                google_usr.authenticate()
                return google_usr
        else:
            google_usr.authenticate()

        return google_usr

    @staticmethod
    def get_user(username: str, password: str) -> dict:
        """Retrieve user access token and roles.

        :param username:
        :param password:
        :return dict:
        """
        credentials = {
            "username": username,
            "password": password
        }

        response = requests.post(url='https://google.com/login', json=credentials)
        if response.status_code == 200:
            credentials['access_token'] = response.json().get('access_token')
            headers = {'Authorization': f'Bearer {credentials.get("access_token")}'}
            profile = requests.get(url='https://google.com/profile', headers=headers).json()
            credentials['roles'] = profile.get('roles', {})
            return credentials
        else:
            echo(response)
            sys.exit(1)

    def authenticate(self):
        """Store self.get_user response and set each key/value as class attributes
        :return:
        """
        if self.username and self.password:
            credentials = self.get_user(self.username, self.password)
            with open(PROFILE_DIR, 'w') as f:
                f.write(json.dumps(credentials, indent=4))

            self.access = credentials.pop('roles', {})
            for key, value in credentials.items():
                setattr(self, key, value)

            return {'Authorization': f'Bearer {self.get("access_token")}'}
```

---
<br>

<a name="modelauth"></a>
### double_click.models.ModelAuth(requires: list = None, match_all: bool = False, **kwargs)
Used by `Model` to auth user in `Model.refresh` before making API request.
> Not a replacement for actual auth on the backend!

```python
# Example
from double_click import Model, ModelAuth

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'
    _auth = ModelAuth(requires=['View', 'List'], match_all=True, service='Home')
```

---
<br>

<a name="model"></a>
### double_click.models.Model()
Base class that acts as a pseudo ORM for data returned from one or more responses from an API endpoint.
Provides optional mechanisms for caching response data that will be used for any objects_* calls while the cache is still valid.

*Required overrides:*
```
_url: str
_obj_identifier: any
```

*Optional overrides:*
```
_session: GeneralSession = None 
_ttl = 120  # Default behavior is to expect int but this can be changed. See Model._cache_set
_auth: ModelAuth = ModelAuth(None, False)
```

```python
# Example
from double_click import Model

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'
```

---
<br>

<a name="model-as-dict"></a>
#### `Model().as_dict -> dict`
Property that returns the dict representation of a Model instance.

---
<br>

<a name="model-objects-all"></a>
#### `Model.objects_all(as_dict: bool = False, **kwargs) -> list`
If as_dict is False, returns list of the Model objects, otherwise a list of dict(obj_identifier=obj_as_dict).

```python
# Example
from double_click import Model

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'


api_response = {
    "front_porch": dict(id=1, name='front_porch', commands=['on', 'off']),
    "tv": dict(id=2, name='tv', commands=['on', 'off']),
}

smart_devices = SmartDevice.objects_all()
print([smart_device.commands for smart_device in smart_devices])

smart_devices = SmartDevice.objects_all(as_dict=True) 
print([smart_device.get('commands') for _, smart_device in smart_devices.items()])
```

---
<br>

<a name="model-objects-get"></a>
#### `Model.objects_get(key, **kwargs) -> Model`
Classmethod that returns a Model instance representing the object matching that key.

```python
# Example
from double_click import Model

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'


api_response = {
    "front_porch": dict(id=1, name='front_porch', commands=['on', 'off']),
    "tv": dict(id=2, name='tv', commands=['on', 'off']),
}

smart_device = SmartDevice.objects_get('tv')
print(smart_device.id)  # 2
print(smart_device.as_dict)  # dict(id=2, name='tv', commands=['on', 'off'])

smart_device = SmartDevice.objects_get('front_porch')
print(smart_device.id)  # 1
```

---
<br>

<a name="model-objects-identifier"></a>
#### `Model.objects_identifier(**kwargs) -> list`
Classmethod that returns the list of keys. When calling `Model.objects_all(as_dict=True)`.
Typically used to pass into click.Choice like `click.Choice(Model.objects_keys())` 

```python
# Example
from double_click import Model

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'


api_response = {
    "front_porch": dict(id=1, name='front_porch', commands=['on', 'off']),
    "tv": dict(id=2, name='tv', commands=['on', 'off']),
}

print(SmartDevice.objects_identifier())  # ['front_porch', 'tv']
```

---
<br>

<a name="model-cache-set"></a>
#### `Model()._cache_set(content) -> dict`
Called by Model.refresh if _cache_key is not None. Protected method that sets cache content.
The purpose making this a dedicated method is to allow for custom caching.

For example, say we wanted to store the cached model in a local redis instance instead of TMP.
The override below will now write to redis and sets the ttl = _ttl * 60 so ttl is still represented as minutes.:
```python
# Example
import json

from double_click import Model
from redis import Redis

REDIS = Redis()

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'
    _cache_key = 'google:home:smart_device'

    def _cache_set(self, content):
        REDIS.set(json.dumps(content), ttl=self._ttl * 60)
```

---
<br>

<a name="model-cache-retrieve"></a>
#### `Model()._cache_retrieve() -> dict`
Protected method called by objects_all to attempt a cached return before calling _api_retrieve.

Similar to _cache_set, _cache_retrieve also needs to be overridden when using a custom cache.
```python
# Example
import json

from double_click import Model
from redis import Redis

REDIS = Redis()

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'
    _cache_key = 'google:home:smart_device'

    def _cache_set(self, content):
        REDIS.set(self._cache_key, json.dumps(content), ttl=self._ttl * 60)

    def _cache_get(self):
        content = REDIS.get(self._cache_key)
        return json.loads(content) if content else None
```

---
<br>

<a name="model-api-retrieve"></a>
#### `Model()._api_retrieve() -> list`
The _api_get method is responsible for making the http request and returning its response.

The default behavior expects a list response from the API with the following keys:
* results: list
* count: int

It will take this content and retrieve any additional pages via async requests. 
For this reason, the default behavior may not be recommended for endpoints with a large number responses or large response objects.
 
To override Model._api_retrieve():
```python
# Example
from double_click import Model

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'

    def _api_retrieve(self) -> list:
        response = self._session.get(self._url)
        return response.json() if response.status_code == 200 else []
```

<a name="model-get"></a>
#### `Model().get(attr, default=None) -> any`
Retrieves the attr value from the instance of the class, setting default if not exists.

```python
# Example
from double_click import Model

class SmartDevice(Model):
    _url = 'https://developers.google.com/home'
    _obj_identifier = 'name'



api_response = {
    "front_porch": dict(id=1, name='front_porch', commands=['on', 'off']),
    "tv": dict(id=2, name='tv', commands=['on', 'off']),
}
    
smart_device = SmartDevice.objects_get('tv')
smart_device.commands  # Returns ['on', 'off']
smart_device.alias  # Throws attribute error
smart_device.get('alias') # Returns None  
smart_device.get('alias', 'Living Room TV') # Returns Living Room TV  
smart_device.alias  # Returns Living Room TV  
```

--- 
<br>

<a name="functions"></a>
## Helper Functions

--- 

<br>

<a name="echo"></a>
### `double_click.utils.echo(output)`
Formats and displays the provided output.

Accepts every commonly used object or structure the echo function can:

* Resolve a requests.Response object to pp json or the response text depending on the response status code
* Pretty print a dict or list of dicts
* Display a string as markdown in the CLI `if str.startswith('#')`
* Display all other as the output's `__repr__` value

#### Parameters:  
  * **output** - `list(dict()) or dict() or Response or md str or output's __repr__ value` Content to print to CLI

--- 
<br>

<a name="md-table-str"></a>
#### `double_click.markdown.generate_md_table_str(row_list, headers)`
Creates a markdown table returned as a **str**.

##### Parameters:  
  * **row_list** - `list(list())` A list with each element representing a row in the table
  * **headers** - `list(str)` List of the column headers

--- 
<br>

<a name="md-bullet-str"></a>
#### `double_click.markdown.generate_md_bullet_str(bullet_list)`
Creates a markdown bullet list returned as a **str**.

##### Parameters:  
  * **bullet_list** - `list(str)` List of strings, each string represented as a bullet

--- 
<br>

<a name="md-code-str"></a>
#### `double_click.markdown.generate_md_code_str(code_snippet, description)`
Generates an indentation based code block with a description header with markdown formatting returned as a **str**.

##### Parameters:  
  * **code_snippet** - `str` Content to display as code
  * **description** - (Optional) `str` Code snippet header. Default: Snippet

--- 


