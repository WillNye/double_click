import unittest

import pytest

from double_click import User


class GoogleUser(User):

    def authenticate(self, **kwargs):
        return {}


class TestUser(unittest.TestCase):

    def test_get(self):
        google_user = GoogleUser(username='TestUser')

        with pytest.raises(AttributeError) as ae:
            google_user.api_key  # If the attribute was never set it's going to throw an exception
        self.assertEqual(google_user.get('api_key'), None)  # Get returns None if the attr does not exist
        with pytest.raises(AttributeError) as ae:
            google_user.api_key  # If no default was provided the attr won't be set for the instance

        self.assertEqual(google_user.get('api_key', 'ABC'), 'ABC')  # Set and return the default value
        self.assertEqual(google_user.get('api_key'), 'ABC')  # Get will now return the value provided previously
        self.assertEqual(google_user.api_key, 'ABC')  # It will also be available as a class attribute

    def test_has_access(self):
        access = dict(service=dict(Photos=dict(permissions=['Create', 'View', 'List'], roles=['Manager'])))
        google_user = GoogleUser(username='TestUser', access=access)

        # A few ways that demonstrate the flexibility of has_access
        self.assertTrue(google_user.has_access(service='Photos'))
        self.assertTrue(google_user.has_access(requires=['View'], service='Photos'))
        self.assertTrue(google_user.has_access(requires=['Manager'], service='Photos'))
        self.assertTrue(google_user.has_access(requires=['View', 'Update'], service='Photos'))
        self.assertTrue(google_user.has_access(requires=['View', 'List'], match_all=True, service='Photos'))

        self.assertFalse(google_user.has_access(requires=['View', 'Update'], match_all=True, service='Photos'))
        self.assertFalse(google_user.has_access(requires=['Manager']))
        self.assertFalse(google_user.has_access(requires=['View'], service='Home'))

    def test_hide(self):
        access = dict(service=dict(Photos=dict(permissions=['Create', 'View', 'List'], roles=['Manager'])))
        google_user = GoogleUser(username='TestUser', access=access)

        # hide is the negation of has_access
        self.assertFalse(google_user.hide(service='Photos'))
        self.assertFalse(google_user.hide(requires=['View'], service='Photos'))
        self.assertFalse(google_user.hide(requires=['Manager'], service='Photos'))
        self.assertFalse(google_user.hide(requires=['View', 'Update'], service='Photos'))
        self.assertFalse(google_user.hide(requires=['View', 'List'], match_all=True, service='Photos'))

        self.assertTrue(google_user.hide(requires=['View', 'Update'], match_all=True, service='Photos'))
        self.assertTrue(google_user.hide(requires=['Manager']))

