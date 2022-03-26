# notion-params
Helper to build Notion API params, parse markdown text into Notion API blocks

![](https://raw.githubusercontent.com/zhaowb/notion-params/main/screenshots/Demo-README.png)

```
import notion_client
from notion_params import NotionParams as NP


def demo():
    notion = notion_client.client.Client(auth=os.environ['NOTION_TOKEN'])
    page_id = '7458781ba20644e0b850452095000000'
    sub_page = notion.pages.create(**NP.create_page(
        page_id,
        title='title text',
        emoji='😀',
        text="""# H1 title
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
"""))
```


Change log
- 0.0.1 NotionParams and markdown parse
  - `create_page`
  - `update_page`
  - `append_markdown`
  - `table_df`, `table_df_rows`
  - `create_database`, `create_database_row`
  - `find_child`
- 0.0.2 add a simple client, change doc of NotionParams methods to match

