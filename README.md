# Introduction of `notion-params`
This is a helper to build Notion API params, parse markdown text into Notion API blocks,
include a simple client support all APIs version '2022-02-22'.

Page can be created using markdown:
![](https://raw.githubusercontent.com/zhaowb/notion-params/main/screenshots/Demo-README.png)

Table:
![](https://raw.githubusercontent.com/zhaowb/notion-params/main/screenshots/Demo-README-table.png)

Database:
![](https://raw.githubusercontent.com/zhaowb/notion-params/main/screenshots/Demo-README-database.png)

See more demos in [sample.py](https://raw.githubusercontent.com/zhaowb/notion-params/main/samples/sample.py): `python sample.py {page_id}` where page_id is a notion page your token has permission to write. This sample code will create a sub page to show all the demos.


# Change log
- 0.0.1 NotionParams and markdown parse
  - `create_page`
  - `update_page`
  - `append_markdown`
  - `table_df`, `table_df_rows`
  - `create_database`, `create_database_row`
  - `find_child`
- 0.0.2 add a simple client, change doc of NotionParams methods to match
  - client.py support all APIs version 2022-02-22
  - add sample.py show demos in a sample page

