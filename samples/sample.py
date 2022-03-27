import json
from itertools import islice

import pandas as pd
from notion_params import NotionParams as NP


def get_df():
    return pd.DataFrame(
        # data generated in https://www.convertcsv.com/generate-test-data.htm
        # keyword: digit(6), first, last, pick(python|javascript|),sentence
        # names: id, first, last, choice, note
        # format: json
        [
            {"id": 423919,   "first": "Anthony",   "last": "Lawson",   "choice": "",
                "note": "Somduna lobnitros kiigu nini isdev sicehfad inenitjom un ukelad kilhak ivukocgo jol wuivehe zidicwir febal odfo."},
            {"id": 640368,   "first": "Edwin",   "last": "McCormick",   "choice": "",
                "note": "Ravkolki kudka ohasi ivitinhut fez ujafu wousiluc jizenli nov ul iknek heozu neehgek mun vomlaug po ogihojdi wu."},
            {"id": 597709,   "first": "Roxie",   "last": "Burke",   "choice": "python",
                "note": "Nu amorozer ibdizu me co iswutfoj kewcacan epatosa os veg sunbarwu wuoku uludad kosze sarcuwsef zusu habofiw."},
            {"id": 833387,   "first": "Rachel",   "last": "Joseph",   "choice": "",
                "note": "Cuddij teacemuj neafadal mabit samsitna bo rujonzu tajda lomde cecacici pazcelso fieji be ruknuf wezegeg dubeof fudon fokha."},
            {"id": 755055,   "first": "Harriett",   "last": "Diaz",   "choice": "javascript",
                "note": "Eru ibi pokuge do abdi zuszieb seffetwa ce bag potulmog wuvmovice dit pojar izuda kez durvof or nulpe."},
            {"id": 893290,   "first": "Roy",   "last": "Hernandez",   "choice": "",
                "note": "Epekri bokhesheg kavew vegoado torno ebapico cuklarsu bezeru zimnejto daja wit buuvuif joitcil og le pefis."},
            {"id": 498363,   "first": "Mabel",   "last": "Baker",   "choice": "python",
                "note": "Kecsubi tiudtu si zaman kiruhfas hu zujso joje adfoju isateuko pibfiip guh mi hufam eviwo beco guhtej."}
        ]
    )


def jsonify(p):
    return json.dumps(p, indent=4)

def demo(page_id):
    notion = NP.get_client()
    # let notion_params client show exception when notion returns error
    # this can help investigate reason
    os.environ['NOTION_PARAMS_SHOW_LAST_EXC'] = 'yes'

    # the following code is repetitive for readers to easily understand

    sub_page = notion.create_page(**NP.create_page(
        page_id,
        title='notion_params sample page (creating)',
        emoji='🚧',
        text="""# Markdown demo
Text text text

> quote
>
>> sub quote
>> more text

!!callout
custom markdown syntax to write callout

- list item abc
- another list item

1. ordered list sample
1. second item

...

See more demos in [sample.py](https://raw.githubusercontent.com/zhaowb/notion-params/main/samples/sample.py)

"""))
    # print(f'create_page={jsonify(sub_page)}')

    df = get_df()

    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """# Table demo
Use API `append_block_children()`.
Use `NP.table_df()` help to create params describe the table.
Use `NP.table_df_rows()` help to create params for the rows.
"""
    ))
    response = notion.append_block_children(
        block_id=sub_page['id'],
        children=[NP.table_df(df)],  # default include 0 rows as table's children
    )
    table = response['results'][0]
    notion.append_block_children(
        block_id=table['id'],
        children=NP.table_df_rows(df),  # append all rows in df
    )
    # when table has many rows, may need to split into multiple append calls
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """
When table is small enough, it can be created in one call:
```
    response = notion.append_block_children(
        block_id=sub_page['id'],
        children=[NP.table_df(df, include_rows=len(df))],
    )
```
"""
    ))

    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """# Database demo
Use API `create_database()` create database.
Use API `create_page(**NP.create_database_row)` to add rows.
Use `NP.create_database()` and `NP.create_database_row()` help to create params.
"""
    ))
    db = notion.create_database(**NP.create_database(
        page_id=sub_page['id'],
        title='Random data abc',
        columns=df.columns,
    ))
    for _, row in df.iterrows():
        notion.create_page(**NP.create_database_row(
            db_id=db['id'],
            row=row,
        ))
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """database created.
Please note the column order is changed by notion. There seems no way to control it.

"""
    ))

    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """
Use API `update_database()` to update title.
This demo only updates database title because `notion_params` only supports `rich_text`
column type.
"""
    ))
    notion.update_database(database_id=db['id'], title=NP.md_line('Random data ABC'))
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """database title updated.

"""
    ))

    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """
Use API `retrieve_database()` to retrieve database object.
"""
    ))
    response = notion.retrieve_database(database_id=db['id'])
    notion.create_page(**NP.create_page(
        parent_page_id=sub_page['id'],
        title='Response of `retrieve_database()`',
        text=f"""Response
```json
{json.dumps(response, indent=4)}
```
"""
    ))

    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """
Use API `query_database()` to filter for `choice` contains `python`:
"""
    ))
    result = list(notion.query_database(
        database_id=db['id'],
        filter={
            "property": "choice",
            "rich_text": {
                "contains": "python",
            }
        }
    ))
    notion.create_page(**NP.create_page(
        parent_page_id=sub_page['id'],
        title='Response of `query_database()` (trimmed)',
        text=f"""Result
```json
{json.dumps(result, indent=4)[:1900]}
# notion limit text content length <= 2000
```
"""
    ))

    # Demo Client.retrieve_bot_user()
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """# Demo about users
Use API `retrieve_bot_user()`
"""
    ))
    response = notion.retrieve_bot_user()
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        f"""Response
```json
{json.dumps(response, indent=4)}
```
"""
    ))

    # Demo Client.list_users() & retrieve_user()
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """
Use API `list_users()` and `retrieve_user()`
"""
    ))
    results = list(islice(notion.list_users(), 3))
    response = notion.retrieve_user(user_id=results[0]['id'])
    notion.create_page(**NP.create_page(
        parent_page_id=sub_page['id'],
        title='Response of `list_users()` and `retrieve_user()`',
        text=f"""Result of `list_users()`
```json
{json.dumps(results, indent=4)[:1900]}
# notion limit text content lengthh <= 2000
```

Result of `retrieve_user()`
```json
{json.dumps(response, indent=4)}
```
"""
    ))

    # Demo Client.retrieve_block_children()
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """# Demo of block APIs
Use API `retrieve_block_children()`
"""
    ))
    results = list(notion.retrieve_block_children(block_id=sub_page['id']))
    db_found = [i for i in results if i['type'] == 'child_database']
    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        f"""Total {len(results)} results found, {len(db_found)} database items.
"""
    ))

    notion.append_block_children(sub_page['id'], **NP.append_markdown(
        """
---
End of sample page
"""
    ))
    # change title to indicate done
    notion.update_page(sub_page['id'], **NP.update_page(
        title='notion_params sample page (done)',
        emoji='😀',
    ))

if __name__ == '__main__':
    import os, sys
    assert os.environ.get('NOTION_TOKEN'), 'need NOTION_TOKEN in env'
    if len(sys.argv) == 1:
        print('need argument: page_id')
        sys.exit(-1)
    page_id = sys.argv[1] 
    demo(page_id)
