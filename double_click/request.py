import asyncio
import concurrent.futures

import requests
from colored import fg, style
from tqdm import tqdm

from double_click.user import User
from double_click.utils import EventLoop, is_valid_url


class RequestObject:

    def __init__(self, url, request_kwargs={}):
        if is_valid_url(url):
            self.url = url

        self.request_kwargs = request_kwargs

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration


class GeneralSession(requests.Session):
    raise_exception = False
    disable_progress_bar = False
    progress_bar_color = 'green_3a'
    max_concurrency = 500

    def __init__(self, *args, **kwargs):
        self.raise_exception = kwargs.pop('raise_exception', self.raise_exception)
        self.disable_progress_bar = kwargs.pop('disable_progress_bar', self.disable_progress_bar)
        self.progress_bar_color = kwargs.pop('progress_bar_color', self.progress_bar_color)
        self.max_concurrency = kwargs.pop('max_concurrency', self.max_concurrency)
        super().__init__()

    @staticmethod
    def format_bulk_request(request_list) -> list:
        formatted_requests = []
        for call in request_list:
            request_kwargs = {}

            if isinstance(call, RequestObject):
                formatted_requests.append(call)
            elif isinstance(call, dict):
                url = call.pop('url')
                if not url:
                    raise ValueError('The url key must provided within the dict')
                request_kwargs = call
            elif isinstance(call, str):
                url = call
            else:
                try:
                    iter(call)
                    url = call[0]
                    for iter_call in call[1:]:
                        if isinstance(iter_call, dict):
                            request_kwargs = {**request_kwargs, **iter_call}
                except TypeError:
                    raise ValueError(f'Unable to iterate {call} to set request')

            formatted_requests.append(RequestObject(url=url, request_kwargs=request_kwargs))

        return formatted_requests

    def refresh_auth(self):
        """Use this to add to verify auth is still valid or refresh if out of date.

        :return:
        """
        raise NotImplementedError

    def _make_request(self, request_call, url, retry=True, **request_kwargs) -> requests.Response:
        """Makes an http request, suppress errors and include content.

        :param session_call: URL the POST request will be made.
        :return: Response
        """
        try:
            response = request_call(url, **request_kwargs)
            if response.status_code == 401:  # Fingers crossed the API has proper status codes
                try:
                    self.refresh_auth()
                    if retry:
                        return self._make_request(request_call, url, retry=False, **request_kwargs)
                except NotImplementedError:
                    return response

            return response

        except Exception as e:
            if self.raise_exception:
                raise
            else:
                response = requests.Response()
                response.url = url
                response.status_code = 666
                response.request_kwargs = request_kwargs
                response._content = str(e).encode('utf-8')
                return response

    def _bulk(self, call, request_list: list, loop: EventLoop = None, **kwargs) -> list:
        """Makes multiple GET requests in a ThreadPoolExecutor.

        :param request_list: list(dict(url, params-optional, data-optional, stream-optional)).
        :param max_concurrency: int - Number of post requests that can be made in parallel.
        :param disable_progress: bool - Disable progress bar. Default False
        :param loop: Advanced: pass an event loop
        :return: list(Response)
        """

        async def request_pool(thread_concurrency):
            bar_format = '{l_bar}%s{bar}%s| {n_fmt}/{total_fmt} [{elapsed}<{remaining},' \
                         ' {rate_fmt}{postfix}]' % (fg(self.progress_bar_color), style.RESET)
            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_concurrency) as executor:
                futures = [
                    loop.run_in_executor(
                        executor,
                        call,
                        None,
                        request_obj
                    ) for request_obj in self.format_bulk_request(request_list)]

                return [await f for f in tqdm(asyncio.as_completed(futures),
                                              total=len(futures),
                                              disable=kwargs.get('disable_progress_bar', self.disable_progress_bar),
                                              bar_format=bar_format)]
        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        concurrency = min(len(request_list), kwargs.get('max_concurrency', self.max_concurrency))
        return loop.run_until_complete(request_pool(concurrency))

    def get(self, url: str = None, request_object: RequestObject = None, **kwargs):
        if request_object:
            url = request_object.url
            kwargs = request_object.request_kwargs
        return self._make_request(super().get, url, **kwargs)

    def put(self, url: str = None, request_object: RequestObject = None, **kwargs):
        if request_object:
            url = request_object.url
            kwargs = request_object.request_kwargs
        return self._make_request(super().put, url, **kwargs)

    def patch(self, url: str = None, request_object: RequestObject = None, **kwargs):
        if request_object:
            url = request_object.url
            kwargs = request_object.request_kwargs
        return self._make_request(super().patch, url, **kwargs)

    def post(self, url: str = None, request_object: RequestObject = None, **kwargs):
        if request_object:
            url = request_object.url
            kwargs = request_object.request_kwargs
        return self._make_request(super().post, url, **kwargs)

    def delete(self, url: str = None, request_object: RequestObject = None, **kwargs):
        if request_object:
            url = request_object.url
            kwargs = request_object.request_kwargs
        return self._make_request(super().delete, url, **kwargs)

    def bulk_get(self, request_list: list, loop: EventLoop = None, **kwargs):
        return self._bulk(self.get, request_list, loop, **kwargs)

    def bulk_put(self, request_list: list, loop: EventLoop = None, **kwargs):
        return self._bulk(self.put, request_list, loop, **kwargs)

    def bulk_patch(self, request_list: list, loop: EventLoop = None, **kwargs):
        return self._bulk(self.patch, request_list, loop, **kwargs)

    def bulk_post(self, request_list: list, loop: EventLoop = None, **kwargs):
        return self._bulk(self.post, request_list, loop, **kwargs)

    def bulk_delete(self, request_list: list, loop: EventLoop = None, **kwargs):
        return self._bulk(self.delete, request_list, loop, **kwargs)


class UserSession(GeneralSession):
    user: User  # Define a class that inherits from UserSession to set a default active user

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', self.user)
        super().__init__(*args, **kwargs)

    def refresh_auth(self):
        self.headers.update(self.user.authenticate())
