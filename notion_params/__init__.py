from typing import Any, List, Mapping

from .markdown import md, md_line
from .client import Client


class NotionParams:
    """
    Notion API reference https://developers.notion.com/reference/intro
    Find emoji https://emojipedia.org/people/

    ```
    from notion_params import NotionParams as NP
    notion = NP.get_client(token)  # or set token in env NOTION_TOKEN
    page_id = '7458781ba20644e0b85045209554ff3d'
    page = notion.retrieve_page(page_id=page_id)

    # create sub page, with markdown text
    sub_page = notion.create_page(**NP.create_page(
        page['id'], title='...', emoji='😆',
        text="markdown content", 
    )
    ```
    """

    md = md
    md_line = md_line

    @staticmethod
    def get_client(token=None):
        return Client(token=token)

    @staticmethod
    def create_page(parent_page_id: str, *, title: str, text: str = None, emoji: str = None):
        """
        ```
        sub_page = notion.pages.create(
            **NotionParams.create_page(
                page['id'],
                title='title string',
                emoji='👷',
                text="markdown...this will be the content",
            )
        )
        ```
        """
        params = {
            # parent https://developers.notion.com/reference/page#page-parent
            'parent': {
                'type': 'page_id',
                'page_id': parent_page_id,
            },
            'properties': {
                # properties https://developers.notion.com/reference/page#all-pages
                # when parent.type is "page_id", only valid is title
                # title can have markdown but displayed as normal text
                # here use md_line only to format notion text param
                'title': md_line(title),
            },
        }
        if text:
            data = md(text)
            # print('markdown', json.dumps(data, indent=4))
            params['children'] = data
        if emoji:
            params['icon'] = {'emoji': emoji}
        return params

    @staticmethod
    def update_page(*, title: str, emoji: str = None, archived=None):
        """
        ```
        notion.pages.update(
            sub_page['id'],
            **NotionParams.update_page(
                title='new title text',
                emoji='😃',
            )
        )
        ```
        """
        params = {
            'properties': {
                'title': md_line(title),
            },
        }
        if emoji:
            params['icon'] = {'emoji': emoji}
        if archived in (True, False):
            params['archived'] = archived
        return params

    @staticmethod
    def append_markdown(text: str):
        """options in https://developers.notion.com/reference/patch-block-children
        Usage: `client.append_block_children(block_id, **NP.append_markdown('markdown text'))`
        """
        return {
            'children': md(text),
        }

    @staticmethod
    def table_df(df, include_rows=0):
        """convert DataFrame to one table block
        :param include_rows: number of rows to include, default only include header
            too many rows may cause result too large
        ```
        result = notion.blocks.children.append(
            block_id=sub_page['id'],
            children=[NotionParams.table_df(df)],
        )
        # table = next((i for i in result['results'] if i['type'] == 'table'))  # assume only one table is created
        table = result['results'][0]  # or simpler because we know only one block is created
        for i in range(0, len(df), 100):
            rows = notion.blocks.children.append(
                block_id=table['id'],
                children=df[i:i+100]
            )
        ```
        """
        # https://developers.notion.com/reference/block#table-blocks
        return {
            'type': 'table',
            'table': {
                "table_width": len(df.columns),
                "has_column_header": True,
                "has_row_header": True,
                "children": [
                    {
                        "type": "table_row",
                        "table_row": {
                            "cells": [
                                [{
                                    "text": {"content": col}
                                }]
                                for col in df.columns
                            ]
                        }
                    }
                ] + NotionParams.table_df_rows(df[:include_rows])
            }
        }

    @staticmethod
    def table_df_rows(df):
        """convert all rows to list of blocks, pass in slice if DataFrame too large
        sample
        ```
        notion.blocks.children.append(
            block_id=table_block_id,
            children=NotionParams.table_df_rows(df[100:200]),
        )
        ```
        """
        return df.apply(
            lambda row: {
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{
                            "text": {"content": str(row[col])}
                        }]
                        for col in df.columns
                    ]
                }
            } if len(row) else {},
            # NOTE: if df length is 0, lambda is invoked once with empty row
            # in this case if reference row[col] will cause confusing error
            # 'DataFrame' object has no attribute 'tolist'
            axis=1,
        ).tolist()

    @staticmethod
    def create_database(page_id, *, title: str, columns: List[str], column_types: Mapping[str, str] = None, emoji: str = None):
        # https://developers.notion.com/reference/create-a-database
        """
        :param column_types: custom column type for each column, if not defined, default is 'rich_text'

        demo:
        ```
        df = pd.DataFrame(...)
        db = notion.databases.create(
            **NotionParams.create_database(
                page['id'],
                title=db_name,
                columns=df.columns,
                emoji='😀',
            ),
        )
        print('created db', json.dumps(db, indent=4))
        for _idx, row in db.iterrows():
            notion.pages.create(**NotionParams.create_database_row(db['id'], row=row))
        # or
        # df.apply(
        #     lambda row: notion.pages.create(
        #         **NotionParams.create_database_row(
        #             db['id'],
        #             row=row,
        #             # emoji='😀',
        #         ),
        #     ),
        #     axis=1,  ### REMEMBER THIS ! to loop lines
        # )
        ```
        """
        column_types = {
            column: (column_types and column_types.get(
                column) or 'rich_text') if idx else 'title'
            for idx, column in enumerate(columns)
        }
        params = {
            'parent': {
                'type': 'page_id',
                'page_id': page_id,
            },
            'title': md_line(title),
            'properties': {
                column: {column_types[column]: {}}
                for column in columns
            },
        }
        if emoji:
            params['icon'] = {'emoji': emoji}
        # print(json.dumps(params, indent=4))
        return params

    @staticmethod
    def create_database_row(db_id: str, *, row: Mapping[str, Any], columns: List[str] = None, column_types: Mapping[str, str] = None, emoji: str = None):
        """
        ```
        for _idx, row in db.iterrows():
            notion.pages.create(**NotionParams.create_database_row(db['id'], row=row))
        ```
        """
        if columns is None:
            columns = row.keys()
        column_types = {
            column: (column_types and column_types.get(
                column) or 'rich_text') if idx else 'title'
            for idx, column in enumerate(columns)
        }
        params = {
            'parent': {
                'type': 'database_id',
                'database_id': db_id
            },
            'properties': {
                column: {
                    'type': column_types[column],
                    column_types[column]: row[column] if column_types[column] not in ('title', 'rich_text') else [{
                        # special value format for title, must be array
                        'text': {'content': str(row[column])},
                    }],
                }
                for column in columns
            },
            # every database row is a page, here it can have children list of blocks
            # 'children': [{block},...]
        }
        if emoji:
            params['icon'] = {'emoji': emoji}
        # print('create_database_row', json.dumps(params, indent=4))
        return params

    @staticmethod
    def find_child(response, *, type_: str, title: str = None):
        """find child in list children response or block append response"""
        if isinstance(response, list):
            # user can pass results array directly, ie NotionParams.find_child(response['results'], ...)
            children = response
        elif isinstance(response, dict):
            # should be normal response
            children = response.get('results') or []
        else:
            raise ValueError('unexpected response type')
        return next((
            i
            for i in children
            if i['type'] == type_
            if title is None or title == i[type_].get('title')
        ), None)
