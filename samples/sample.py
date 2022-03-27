import json

from notion_params import NotionParams as NP


def jsonify(p):
    return json.dumps(p, indent=4)

def demo():
    notion = NP.get_client()
    response = notion.retrieve_bot_user()
    print(f'retrieve_bot_user={jsonify(response)}')

    page_id = '7458781ba20644e0b85045209554ff3d'
    sub_page = notion.create_page(**NP.create_page(
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
    print(f'create_page={jsonify(sub_page)}')

# TODO: more sample, to show every api

if __name__ == '__main__':
    import os
    assert os.environ.get('NOTION_TOKEN'), 'need NOTION_TOKEN in env'
    demo()
