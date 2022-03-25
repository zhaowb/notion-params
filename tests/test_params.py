import json

import pandas as pd
import pytest
from notion_params import NotionParams as NP


@pytest.fixture
def df():
    return pd.DataFrame([
        {'k': 1, 'v1': 'a', 'v2': 10},
        {'k': 2, 'v1': 'b', 'v2': 11},
    ])

def test_create_page():
    result = NP.create_page(
        parent_page_id='abcde',
        title='Title text',
        emoji='X',
        text='# header\n\ntext text text',
    )
    # print(json.dumps(result, indent=4))
    assert result == {
        "parent": {
            "type": "page_id",
            "page_id": "abcde"
        },
        "properties": {
            "title": [{"text": {"content": "Title text"}}]
        },
        "children": [{
            "type": "heading_1",
            "heading_1": {"rich_text": [{"text": {"content": "header"}}]}
        }, {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": ""}}]}
        }, {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "text text text"}}]}
        }
        ],
        "icon": {"emoji": "X"}
    }


def test_update_page():
    result = NP.update_page(
        title='New Title',
        emoji='Y',
    )
    print(json.dumps(result, indent=4))
    assert result == {
        "properties": {
            "title": [{"text": {"content": "New Title"}}]
        },
        "icon": {"emoji": "Y"}
    }


def test_append_markdown():
    # use case notion.blocks.children.append(page['id'], **NP.append_markdown('...'))
    result = NP.append_markdown('blabla')
    print(json.dumps(result, indent=4))
    assert result == {
        "children": [{
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "blabla"}}]
            }
        }]
    }


def test_table_df(df):
    result = NP.table_df(df)
    print(json.dumps(result, indent=4))
    assert result == {
        "type": "table",
        "table": {
            "table_width": 3,
            "has_column_header": True,
            "has_row_header": True,
            "children": [{
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"text": {"content": "k"}}],
                        [{"text": {"content": "v1"}}],
                        [{"text": {"content": "v2"}}]
                    ]
                }
            }]
        }
    }


def test_table_df_rows(df):
    result = NP.table_df_rows(df[0:1])
    print(json.dumps(result, indent=4))
    assert result == [{
        "type": "table_row",
        "table_row": {
            "cells": [
                [{"text": {"content": "1"}}],
                [{"text": {"content": "a"}}],
                [{"text": {"content": "10"}}]
            ]
        }
    }]


def test_create_database(df):
    result = NP.create_database(
        page_id='abc',
        title='title text',
        columns=df.columns,
        emoji='X',
    )
    print(json.dumps(result, indent=4))
    assert result == {
        "parent": {
            "type": "page_id",
            "page_id": "abc"
        },
        "title": [{"text": {"content": "title text"}}],
        "properties": {
            "k": {"title": {}},
            "v1": {"rich_text": {}},
            "v2": {"rich_text": {}}
        },
        "icon": {"emoji": "X"}
    }


def test_create_database_row(df):
    for _, row in df[0:1].iterrows():
        result = NP.create_database_row(
            db_id='abc',
            row=row,
            emoji='X',
        )
        print(json.dumps(result, indent=4))
        assert result == {
            "parent": {
                "type": "database_id",
                "database_id": "abc"
            },
            "properties": {
                "k": {
                    "type": "title",
                    "title": [{"text": {"content": "1"}}]
                },
                "v1": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": "a"}}]
                },
                "v2": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": "10"}}]
                }
            },
            "icon": {"emoji": "X"}
        }


def test_find_child():
    response = {}
    result = NP.find_child(
        response,
        type_='child_database',
        title='db name',
    )
