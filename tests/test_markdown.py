import json

import pytest
from notion_params import NotionParams as NP
import notion_params.markdown
import pydash

md = NP.md

def test_decode_style():
    decode_style = notion_params.markdown.decode_style
    assert decode_style(None) == ''
    assert decode_style('') == ''
    assert decode_style('</span>') == '/'
    assert decode_style('<p>') == ''
    assert decode_style("""<span>""") == ''
    assert decode_style("""<span arg=1234>""") == ''
    # if not color or background-color
    # don't consider multi params, this is simple hack not full support
    assert decode_style("""<span style='font-size:16'>""") == ''
    # should trim space around =
    assert decode_style("""<span style  =  'color:blue'>""") == 'blue'
    assert decode_style("""<span style='color:blue'>""") == 'blue'
    assert decode_style("""<span style='background-color:blue'>""") == 'blue_background'
    assert decode_style("""<span style='color:pink'>""") == 'pink'
    assert decode_style("""<span style='color:cyanic'>""") == 'blue'  # unsupported color


def test_basic():
    result = md("""# h1 text\nfirst line\n\n\nmore text""")
    # print(json.dumps(result, indent=4))
    assert isinstance(result, list) and len(result) == 4
    assert [i['type'] for i in result] == ['heading_1', 'paragraph', 'paragraph', 'paragraph']
    assert pydash.get(result, '0.heading_1.rich_text.0.text.content') == 'h1 text'
    assert pydash.get(result, '1.paragraph.rich_text.0.text.content') == 'first line'
    assert pydash.get(result, '2.paragraph.rich_text.0.text.content') == ''
    assert pydash.get(result, '3.paragraph.rich_text.0.text.content') == 'more text'

    assert md("""_italic_""") == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "italic"},
                "annotations": {"italic": True}
            }]
        }
    }]

    assert md("""**bold**""") == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "bold"},
                "annotations": {"bold": True}
            }]
        }
    }]

    assert md("""~~cross~~""") == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "cross"},
                "annotations": {"strikethrough": True}
            }]
        }
    }]

    assert md("""`code here`""") == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "code here"},
                "annotations": {"code": True}
            }]
        }
    }]

    assert md('---') == [{
        "type": "divider",
        "divider": {}
    }]

    result = md("[title text](http://website.com)")
    assert result == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {
                    "content": "title text",
                    "link": {"url": "http://website.com"}
                }
            }]
        }
    }]

def test_quote():
    # simple quote
    result = md("""> first line""")
    # print(json.dumps(result, indent=4))
    assert result == [{
        "type": "quote",
        "quote": {
            "rich_text": [{
                "text": {"content": "first line"},
            }]
        }
    }]

    # nested quote
    result = md(\
"""> first line
>
>> inner quote
""")
    # print(json.dumps(result, indent=4))
    assert result == [{
        "type": "quote",
        "quote": {
            "rich_text": [
                {"text": {"content": "first line"}},
                {"text": {"content": ""}}
            ],
            "children": [{
                "type": "quote",
                "quote": {
                    "rich_text": [
                        {"text": {"content": "inner quote"}}
                    ]
                }
            }]
        }
    }]


def test_color():
    # basic color
    result = md(
        "color <span style='color:blue'>blue text</span>,"
    )
    # print(json.dumps(result, indent=4))
    assert result == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "color "}
            }, {
                "text": {"content": "blue text"},
                "annotations": {"color": "blue"}
            }, {
                "text": {"content": ","}
            }]
        }
    }]

    # nested color
    result = md(
        "color <span style='color:yellow'>nested "
        "<span style='background-color:green'>text</span> example</span>."
    )
    print(json.dumps(result, indent=4))
    assert result == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "color "}
            }, {
                "text": {"content": "nested "},
                "annotations": {"color": "yellow"}
            }, {
                "text": {"content": "text"},
                "annotations": {"color": "green_background"}
            }, {
                "text": {"content": " example"},
                "annotations": {"color": "yellow"}
            }, {
                "text": {"content": "."}
            }]
        }
    }]

    # unsupported color
    result = md(
        "Unsupported color will <span style='color:aqua'>use blue</span>."
    )
    # print(json.dumps(result, indent=4))
    assert result == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": "Unsupported color will "}
            }, {
                "text": {"content": "use blue"},
                "annotations": {"color": "blue"}
            }, {
                "text": {"content": "."}
            }]
        }
    }]


def test_customer_callout():
    # simple
    result = md("""!!callout emoji='X'
text abcde
""")
    # print(json.dumps(result, indent=4))
    assert result == [{
        "type": "callout",
        "callout": {
            "rich_text": [{
                "text": {"content": "text abcde"}
            }],
            "icon": {"emoji": "'X'"}
        }
    }]

    # TODO: complex nested children


def test_list():
    # simple
    result = md("""- item 1
- item 2""")
    # print(json.dumps(result, indent=4))
    assert result == [{
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "text": {"content": "item 1"}
            }]
        }
    }, {
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "text": {"content": "item 2"}
            }]
        }
    }]


def test_code():
    # simple
    result = md("""```
test 123
```""")
    # print(json.dumps(result, indent=4))
    # default use 'plain text' format
    assert result == [{
        "type": "code",
        "code": {
            "rich_text": [{
                "text": {"content": "test 123\n"}
            }],
            "language": "plain text"
        }
    }]

    # simple 2
    result = md("""
    test 123
""")
    print(json.dumps(result, indent=4))
    # default use 'plain text' format
    assert result == [{
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": ""}
            }]
        }
    }, {
        "type": "code",
        "code": {
            "rich_text": [{
                "text": {"content": "test 123\n"}
            }],
            "language": "plain text"
        }
    }]


def test_unsupport_heading_more_than_3():
    with pytest.raises(NotImplementedError):
        md('#### heading 4 will fail')
