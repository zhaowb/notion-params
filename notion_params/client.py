import json
import os
from typing import Any, Iterator
from urllib.parse import urljoin

import backoff
import requests

# https://developers.notion.com/reference/intro#conventions
NOTION_BASE_URL = 'https://api.notion.com'

# https://developers.notion.com/reference/versioning
NOTION_VERSION = '2022-02-22'


def make_params(vars):
    """quick hacky way to build body params
    vars is locals() passed from each api endpoint, eg query_database().
    This function copies every var if
        - it's not 'self' or 'kw'
        - not start with '_':
            in case any api endpoint code need local var, it should start with _
        - not end with '_id':
            all url params are also defined in api endpoint functions
            they all like '*_id', eg page_id, block_id etc
    The goal is to minimize api endpoint code, easier to read and match to official document.
    This is less hacky than using inspect :D and still kind of readable/maintainable
        and api endpoint code is minimal enough.
    """
    params = {
        name: vars[name]
        for name in vars
        if name not in ('self', 'kw')  # skip self and kw
        and name[0] != '_'   # skip possible local use vars
        and not name.endswith('_id')  # skip url params
        if vars.get(name) is not None
    }
    if 'kw' in vars:
        # copy everything under 'kw'
        params.update(vars['kw'])
    return params


class Client:
    """A simple direct translation of offical API reference https://developers.notion.com/reference/intro into api endpoints,
    NotionParams should have a helper for each api to fill-in options, so they can be used as
    ```
    client.append_block_children(block_id, **NP.append_markdown('markdown text'))
    ```
    """

    def __init__(self, token: str = None) -> None:
        if token is None:
            token = os.environ.get('NOTION_TOKEN')
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        self._last_exc = None

    @backoff.on_exception(
        # retry 429 until succ or other error
        backoff.expo,
        requests.exceptions.HTTPError,
        giveup=lambda exc: exc.response is not None and exc.response.status_code != 429,
        max_value=10,
        jitter=None,
    )
    @backoff.on_exception(
        # retry 502 3 times
        backoff.constant,
        requests.exceptions.HTTPError,
        giveup=lambda exc: exc.response is not None and exc.response.status_code != 502,
        max_tries=3,
        interval=2,  # 2 seconds
        jitter=None,
    )
    def _request_core(self, url, **kw):
        r = self._session.request(url=urljoin(NOTION_BASE_URL, url), **kw)
        r.raise_for_status()
        return r.json()

    def _request(self, url, **kw):
        """save exception for diagnostic"""
        try:
            return self._request_core(url, **kw)
        except requests.exceptions.HTTPError as exc:
            self._last_exc = exc
            if str(os.environ.get('NOTION_PARAMS_SHOW_LAST_EXC') or '').lower() in ('yes', 'y', 'true', 't', '1'):
                self._show_last_exc()
            raise
    
    def _show_last_exc(self):
        exc = self._last_exc
        if not exc:
            return
        if exc.response is not None:
            print('Response', exc.response.status_code, exc.response.text)
        if exc.request is not None:
            print('Request body', exc.request.body)

    def _api(self, method, url, vars=None):
        params = make_params(vars) if vars else None
        return self._request(url=url, method=method, json=params)

    def _paginate(self, method, url, vars) -> Iterator[Any]:
        # https://developers.notion.com/reference/pagination
        """kw['json'] can have start_cursor, page_size, see sample query_database()"""
        params = make_params(vars)
        while True:
            response = self._request(url=url, method=method, json=params)
            yield from response.get('results') or []
            next_cursor = response.get('next_cursor')
            if not next_cursor:
                break
            params['start_cursor'] = next_cursor

    # the following 'api' endpoints are simple mirror of https://developers.notion.com/reference/intro
    # in the same order and naming conventions for easier jump to official documents

    def query_database(self, database_id, *, filter=None, sorts=None, start_cursor=None, page_size=None) -> Iterator[Any]:
        """https://developers.notion.com/reference/post-database-query"""
        yield from self._paginate('post', f'/v1/databases/{database_id}/query', locals())

    def create_database(self, *, parent, properties, title=None, icon=None, cover=None) -> dict:
        """https://developers.notion.com/reference/create-a-database"""
        # Note: 'icon' and 'cover' are not listed in document but showed in sample
        return self._api('post', '/v1/databases', locals())

    def update_database(self, database_id, *, title=None, properties=None):
        """https://developers.notion.com/reference/update-a-database"""
        return self._api('patch', f'/v1/databases/{database_id}', locals())

    def retrieve_database(self, database_id, ):
        """https://developers.notion.com/reference/retrieve-a-database"""
        return self._api('get', f'/v1/databases/{database_id}')

    def retrieve_page(self, page_id):
        """https://developers.notion.com/reference/retrieve-a-page"""
        return self._api('get', f'/v1/pages/{page_id}')

    def create_page(self, *, parent, properties, children=None, icon=None, cover=None):
        """https://developers.notion.com/reference/post-page"""
        return self._api('post', '/v1/pages', locals())

    def update_page(self, page_id, *, properties=None, archived=None, icon=None, cover=None):
        """https://developers.notion.com/reference/patch-page"""
        return self._api('patch', f'/v1/pages/{page_id}', locals())

    def retrieve_page_property_item(self, page_id, property_id, *, start_cursor=None, page_size=None):
        """https://developers.notion.com/reference/retrieve-a-page-property"""
        yield from self._paginate('get', f'/v1/pages/{page_id}/properties/{property_id}', locals())

    def retrieve_block(self, block_id):
        """https://developers.notion.com/reference/retrieve-a-block"""
        return self._api('get', f'/v1/blocks/{block_id}')

    def update_block(self, block_id, *, archived=None, **kw):
        """https://developers.notion.com/reference/update-a-block
        (kw is) the block object type value with the properties to be updated. Currently only text (for supported block types) and checked (for to_do blocks) fields can be updated.
        """
        return self._api('patch', f'/v1/blocks/{block_id}', {**locals(), **kw})

    def retrieve_block_children(self, block_id, *, start_cursor=None, page_size=None):
        """https://developers.notion.com/reference/get-block-children"""
        yield from self._paginate('get', f'/v1/blocks/{block_id}/children', locals())

    def append_block_children(self, block_id, *, children):
        """https://developers.notion.com/reference/patch-block-children"""
        return self._api('patch', f'/v1/blocks/{block_id}/children', locals())

    def delete_block(self, block_id):
        """https://developers.notion.com/reference/delete-a-block"""
        return self._api('delete', f'/v1/blocks/{block_id}')

    def retrieve_user(self, user_id):
        """https://developers.notion.com/reference/get-user"""
        return self._api('get', f'/v1/users/{user_id}')

    def list_users(self, *, start_cursor=None, page_size=None):
        """https://developers.notion.com/reference/get-users"""
        yield from self._paginate('get', f'/v1/users', locals())

    def retrieve_bot_user(self):
        """https://developers.notion.com/reference/get-self"""
        return self._api('get', '/v1/users/me')

    def search(self, *, query=None, sort=None, filter=None, start_cursor=None, page_size=None):
        """https://developers.notion.com/reference/post-search"""
        yield from self._paginate('post', '/v1/search', locals())
