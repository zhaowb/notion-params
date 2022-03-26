import json

from notion_params import NotionParams as NP


def jsonify(p):
    return json.dumps(p, indent=4)

def demo():
    client = NP.get_client()
    response = client.retrieve_bot_user()
    print(f'retrieve_bot_user={jsonify(response)}')


if __name__ == '__main__':
    import os
    assert os.environ.get('NOTION_TOKEN'), 'need NOTION_TOKEN in env'
    demo()
