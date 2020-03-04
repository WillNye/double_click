import unittest

from double_click.request import is_valid_url, GeneralSession, RequestObject


class TestValidateURL(unittest.TestCase):

    def test_valid_url(self):
        self.assertTrue(is_valid_url('http://google.com', raises=False))
        self.assertTrue(is_valid_url('https://google.com', raises=False))
        self.assertTrue(is_valid_url('http://www.google.com', raises=False))
        self.assertTrue(is_valid_url('https://www.google.com', raises=False))
        self.assertTrue(is_valid_url('https://wikipedia.org', raises=False))

    def test_invalid_url(self):
        self.assertFalse(is_valid_url('google.com', raises=False))
        self.assertFalse(is_valid_url('https:/google.com', raises=False))
        self.assertFalse(is_valid_url('http//www.google.com', raises=False))
        self.assertFalse(is_valid_url('https://www.google', raises=False))

        self.assertRaises(ValueError, is_valid_url, 'google.com')


class TestGeneralSession(unittest.TestCase):

    def test_format_bulk_request(self):
        request_list = ['https://github.com', 'https://google.com', 'https://pypi.org']

        # Test list(url)
        formatted_requests = GeneralSession.format_bulk_request(
            request_list
        )
        for formatted_request in formatted_requests:
            self.assertIsInstance(formatted_request, RequestObject)
            self.assertIn(formatted_request.url, request_list)

        # Test list(list(url))
        formatted_requests = GeneralSession.format_bulk_request(
            [['https://github.com'], ['https://google.com'], ['https://pypi.org']]
        )
        for formatted_request in formatted_requests:
            self.assertIsInstance(formatted_request, RequestObject)
            self.assertIn(formatted_request.url, request_list)

        # Include examples of passing request params
        requests_dict = {
            'https://github.com': dict(params=dict(page=1)),
            'https://google.com/login': dict(data=dict(username='user', password='password')),
            'https://pypi.org': dict(json=dict(name='double_click'))
        }

        # Test list(list(url, dict))
        formatted_requests = GeneralSession.format_bulk_request([
            ['https://github.com', dict(params=dict(page=1))],
            ['https://google.com/login', dict(data=dict(username='user', password='password'))],
            ['https://pypi.org', dict(json=dict(name='double_click'))]
        ])
        for formatted_request in formatted_requests:
            self.assertIsInstance(formatted_request, RequestObject)
            self.assertIn(formatted_request.url, requests_dict)
            self.assertEqual(requests_dict[formatted_request.url], formatted_request.request_kwargs)

        # Test list(dict(url, request_kwargs))
        formatted_requests = GeneralSession.format_bulk_request([
            dict(url='https://github.com', params=dict(page=1)),
            dict(url='https://google.com/login', data=dict(username='user', password='password')),
            dict(url='https://pypi.org', json=dict(name='double_click'))
        ])
        for formatted_request in formatted_requests:
            self.assertIsInstance(formatted_request, RequestObject)
            self.assertIn(formatted_request.url, requests_dict)
            self.assertEqual(requests_dict[formatted_request.url], formatted_request.request_kwargs)

    def test_bad_request(self):
        basic_session = GeneralSession()
        response = basic_session.get('https://fakeendpointadspfaisdjfpodsaijfadspoijasdf.com')
        self.assertEqual(response.status_code, 666)
        self.assertIn('Failed to establish a new connection', response.text)
