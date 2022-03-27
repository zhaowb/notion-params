import json
import unittest.mock
from copy import deepcopy
from uuid import uuid4

import pytest


def copy_call_args(mock):
    # https://docs.python.org/3/library/unittest.mock-examples.html#coping-with-mutable-arguments
    # because client._paginate() reuses internal var params for requests, without
    # deepcopy, checking call_args_list can only see the last version of called params.
    new_mock = unittest.mock.Mock()

    def side_effect(*args, **kwargs):
        print('called', args, kwargs)
        args = deepcopy(args)
        kwargs = deepcopy(kwargs)
        new_mock(*args, **kwargs)
        return unittest.mock.DEFAULT
    mock.side_effect = side_effect
    return new_mock


# to copy json from official doc and paste as code
true, false, null = True, False, None


@pytest.fixture(autouse=True)
def app(mocker):
    mocker.patch('requests.Session')

    from notion_params import NotionParams as NP
    client = NP.get_client()
    yield client
    # cleanup here


def test_api_query_database():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    database_id = str(uuid4())
    sample = {
        # https://developers.notion.com/reference/post-database-query
        "filter": {
            "or": [{
                "property": "In stock",
                "checkbox": {"equals": true}
            }, {
                "property": "Cost of next trip",
                "number": {"greater_than_or_equal_to": 2}
            }]
        },
        "sorts": [{
            "property": "Last ordered",
            "direction": "ascending"
        }]
    }
    client._session.request.return_value.json.side_effect = [
        # return value of the 1st call
        {
            # copied from official doc
            "object": "list",
            'results': [{
                "object": "page",
                # ignore more details, see official doc for sample
            }, {
                "object": "2nd",  # not real, just to test response data
            }],
            "next_cursor": "cursor-value",  # not real, test 2nd call
            "has_more": false,
            "type": "page",
            "page": {}
        },
        # return value of the 2nd call
        {
            "results": [{
                "object": "3rd",  # not real
            }]
        },
    ]
    # see comment in copy_call_args(). this is to solve params being reused in _paginate()
    mock_copy = copy_call_args(client._session.request)
    # run app
    result = list(
        client.query_database(database_id=database_id, **sample)
    )
    # check
    # all results in 2 pages are listed
    assert result == [{"object": "page"}, {"object": "2nd"}, {"object": "3rd"}]
    # due to paginate reuses internal params, here should check mocked_request_copy
    assert len(mock_copy.call_args_list) == 2
    _args, kw = mock_copy.call_args_list[0]
    assert kw == {
        'url': f"https://api.notion.com/v1/databases/{database_id}/query",
        'method': 'post',
        'json': sample,
    }
    _args, kw = mock_copy.call_args_list[1]
    assert kw == {
        'url': f"https://api.notion.com/v1/databases/{database_id}/query",
        'method': 'post',
        'json': {
            **sample,
            'start_cursor': 'cursor-value',  # 2nd request has start_cursor
        },
    }


def test_api_create_database():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # copy sample from https://developers.notion.com/reference/create-a-database
    sample = {
        "parent": {
            "type": "page_id",
            "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
        },
        "icon": {
            "type": "emoji",
            "emoji": "🎉"
        },
        "cover": {
            "type": "external",
            "external": {
                "url": "https://website.domain/images/image.png"
            }
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "Grocery List",
                    "link": null
                }
            }
        ],
        "properties": {
            "Name": {
                "title": {}
            },
            "Description": {
                "rich_text": {}
            },
            "In stock": {
                "checkbox": {}
            },
            "Food group": {
                "select": {
                    "options": [
                        {
                            "name": "🥦Vegetable",
                            "color": "green"
                        },
                        {
                            "name": "🍎Fruit",
                            "color": "red"
                        },
                        {
                            "name": "💪Protein",
                            "color": "yellow"
                        }
                    ]
                }
            },
            "Price": {
                "number": {
                    "format": "dollar"
                }
            },
            "Last ordered": {
                "date": {}
            },
            "Meals": {
                "relation": {
                    "database_id": "668d797c-76fa-4934-9b05-ad288df2d136",
                }
            },
            "Number of meals": {
                "rollup": {
                    "rollup_property_name": "Name",
                    "relation_property_name": "Meals",
                    "function": "count"
                }
            },
            "Store availability": {
                "type": "multi_select",
                "multi_select": {
                    "options": [
                        {
                            "name": "Duc Loi Market",
                            "color": "blue"
                        },
                        {
                            "name": "Rainbow Grocery",
                            "color": "gray"
                        },
                        {
                            "name": "Nijiya Market",
                            "color": "purple"
                        },
                        {
                            "name": "Gus'\''s Community Market",
                            "color": "yellow"
                        }
                    ]
                }
            },
            "+1": {
                "people": {}
            },
            "Photo": {
                "files": {}
            }
        }
    }
    # run app
    client.create_database(**sample)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': 'https://api.notion.com/v1/databases',
        'method': 'post',
        'json': sample,
    }


def test_api_update_database():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # copy from https://developers.notion.com/reference/update-a-database
    database_id = '668d797c-76fa-4934-9b05-ad288df2d136'
    sample = {
        "title": [
            {
                "text": {
                    "content": "Today'\''s grocery list"
                }
            }
        ],
        "properties": {
            "+1": null,
            "Photo": {
                "url": {}
            },
            "Store availability": {
                "multi_select": {
                    "options": [
                        {
                            "name": "Duc Loi Market"
                        },
                        {
                            "name": "Rainbow Grocery"
                        },
                        {
                            "name": "Gus'\''s Community Market"
                        },
                        {
                            "name": "The Good Life Grocery",
                            "color": "orange"
                        }
                    ]
                }
            }
        }
    }
    # run app
    client.update_database(database_id, **sample)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': 'https://api.notion.com/v1/databases/668d797c-76fa-4934-9b05-ad288df2d136',
        'method': 'patch',
        'json': sample,
    }


def test_api_retrieve_database():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # https://developers.notion.com/reference/retrieve-a-database
    database_id = str(uuid4())
    sample = None
    # run
    client.retrieve_database(database_id)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/databases/{database_id}',
        'method': 'get',
        'json': sample,
    }


def test_api_retrieve_page():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # https://developers.notion.com/reference/retrieve-a-page
    page_id = str(uuid4())
    sample = None
    # run
    client.retrieve_page(page_id)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/pages/{page_id}',
        'method': 'get',
        'json': sample
    }


def test_api_create_page():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # https://developers.notion.com/reference/post-page
    sample = {
        "parent": {"database_id": "d9824bdc84454327be8b5b47500af6ce"},
        "icon": {
            "emoji": "🥬"
        },
        "cover": {
            "external": {
                "url": "https://upload.wikimedia.org/wikipedia/commons/6/62/Tuscankale.jpg"
            }
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": "Tuscan Kale"
                        }
                    }
                ]
            },
            "Description": {
                "rich_text": [
                    {
                        "text": {
                            "content": "A dark green leafy vegetable"
                        }
                    }
                ]
            },
            "Food group": {
                "select": {
                    "name": "Vegetable"
                }
            },
            "Price": {"number": 2.5}
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Lacinato kale"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Lacinato kale is a variety of kale with a long tradition in Italian cuisine, especially that of Tuscany. It is also known as Tuscan kale, Italian kale, dinosaur kale, kale, flat back kale, palm tree kale, or black Tuscan palm.",
                                "link": {"url": "https://en.wikipedia.org/wiki/Lacinato_kale"}
                            }
                        }
                    ]
                }
            }
        ]
    }
    # run
    client.create_page(**sample)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': 'https://api.notion.com/v1/pages',
        'method': 'post',
        'json': sample
    }


def test_api_update_page():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see sample https://developers.notion.com/reference/patch-page
    page_id = str(uuid4())
    sample = {
        "properties": {
            "In stock": {"checkbox": true}
        }
    }
    # run app
    client.update_page(page_id, **sample)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/pages/{page_id}',
        'method': 'patch',
        'json': sample,
    }


def test_api_retrieve_page_property_item():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/retrieve-a-page-property
    page_id = 'b55c9c91-384d-452b-81db-d1ef79372b75'
    property_id = 'some-property-id'
    client._session.request.return_value.json.side_effect = [
        {},  # return json for first page
    ]
    # run app
    list(
        client.retrieve_page_property_item(page_id, property_id)
    )
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/pages/{page_id}/properties/{property_id}',
        'method': 'get',
        'json': {},  # both {} or None should work
    }


def test_api_retrieve_block():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/retrieve-a-block
    block_id = '0c940186-ab70-4351-bb34-2d16f0635d49'
    # run app
    client.retrieve_block(block_id)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/blocks/{block_id}',
        'method': 'get',
        'json': None,
    }


def test_api_update_block():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/update-a-block
    block_id = '9bc30ad4-9373-46a5-84ab-0a7845ee52e6'
    sample = {
        "to_do": {
            "rich_text": [{
                "text": {"content": "Lacinato kale"}
            }],
            "checked": false
        }
    }
    # run app
    client.update_block(block_id, **sample)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/blocks/{block_id}',
        'method': 'patch',
        'json': sample,
    }


def test_api_retrieve_block_children():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/get-block-children
    block_id = 'b55c9c91-384d-452b-81db-d1ef79372b75'
    client._session.request.return_value.json.side_effect = [
        {},  # first page
    ]
    # run app
    list(
        client.retrieve_block_children(block_id)
    )
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/blocks/{block_id}/children',
        'method': 'get',
        'json': {}
    }


def test_api_append_block_children():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/patch-block-children
    block_id = 'b55c9c91-384d-452b-81db-d1ef79372b75'
    sample = {
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Lacinato kale"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Lacinato kale is a variety of kale with a long tradition in Italian cuisine, especially that of Tuscany. It is also known as Tuscan kale, Italian kale, dinosaur kale, kale, flat back kale, palm tree kale, or black Tuscan palm.",
                                "link": {"url": "https://en.wikipedia.org/wiki/Lacinato_kale"}
                            }
                        }
                    ]
                }
            }
        ]
    }
    # run app
    client.append_block_children(block_id, **sample)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/blocks/{block_id}/children',
        'method': 'patch',
        'json': sample
    }


def test_api_delete_block():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/delete-a-block
    block_id = '9bc30ad4-9373-46a5-84ab-0a7845ee52e6'
    # run app
    client.delete_block(block_id)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/blocks/{block_id}',
        'method': 'delete',
        'json': None
    }


def test_api_retrieve_user():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/get-user
    user_id = 'd40e767c-d7af-4b18-a86d-55c61f1e39a4'
    # run app
    client.retrieve_user(user_id)
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': f'https://api.notion.com/v1/users/{user_id}',
        'method': 'get',
        'json': None,
    }


def test_api_list_users():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/get-users
    client._session.request.return_value.json.side_effect = [
        {},  # first page
    ]
    # run app
    list(
        client.list_users()
    )
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': 'https://api.notion.com/v1/users',
        'method': 'get',
        'json': {}
    }


def test_api_retrieve_bot_user():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/get-self
    # run app
    client.retrieve_bot_user()
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': 'https://api.notion.com/v1/users/me',
        'method': 'get',
        'json': None,
    }


def test_api_search():
    from notion_params import NotionParams as NP
    client = NP.get_client()
    # setup
    # see https://developers.notion.com/reference/post-search
    sample = {
        "query": "External tasks",
        "sort": {
            "direction": "ascending",
            "timestamp": "last_edited_time"
        }
    }
    client._session.request.return_value.json.side_effect = [
        {},  # first page
    ]
    # run app
    list(
        client.search(**sample)
    )
    # check
    assert len(client._session.request.call_args_list) == 1
    _args, kw = client._session.request.call_args_list[0]
    assert kw == {
        'url': 'https://api.notion.com/v1/search',
        'method': 'post',
        'json': sample,
    }
