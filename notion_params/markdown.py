import json
import warnings

import marko
import pydash
from marko.ext.gfm.elements import Strikethrough

# see https://developers.notion.com/reference/rich-text#annotations
NOTION_COLOR_NAMES = "gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink", "red"

def decode_style(code):
    """simple <span style> decoder
    :param code: inline html code, eg "<span style='color:blue'>" or "</span>" or any other inline html code
    :returns: 
        if style match, return notion color code, "red", "blue" etc, see NOTION_COLOR_NAMES
        if /span return '/'
        otherwise return ''
    """
    if not code:
        return ''
    code = code.lower().strip('<>')
    if code == '/span':
        return '/'
    if not code.startswith('span '):
        return ''
    # faster coding than regex :D
    while ' =' in code:
        code = code.replace(' =', '=')
    while '= ' in code:
        code = code.replace('= ', '=')
    style = next((i for i in code.split() if i.startswith('style=')), None)
    if not style:
        return ''
    style = style.split('=', 1)[-1].strip('"\'').split(':', 1)  # (color, blue)
    # possible values https://developers.notion.com/reference/rich-text#annotations
    if style[0] == 'color':
        color, is_background = style[1], False
    elif style[0] == 'background-color':
        color, is_background = style[1], True
    else:
        return ''
    if color not in NOTION_COLOR_NAMES:
        color = "blue"  # show color is working but not the desired one
    return color if not is_background else f'{color}_background'


class MarkoNotionRenderer(marko.Renderer):
    # mostly followed https://github.com/frostming/marko/blob/master/marko/md_renderer.py
    # there are a few known issues, see cmd_markdown_demo
    # so far, simple format works, avoid nesting blocks, ie, sub-list, sub-quote etc

    def render_children(self, element):
        # copy from Renderer.render_childern
        if isinstance(element, str):
            return [{'text': {'content': element}}]
        if isinstance(element.children, str):
            return [{'text': {'content': element.children}}]
        return [self.render(child) for child in element.children]

    def _render_as(self, type_, element, **kw):
        result = {
            "type": type_,
            type_: {} if element is None else {'rich_text': self.render_children(element), **kw}
        }

        # fix custom block type
        if type_ == 'paragraph' and result[type_].get('rich_text'):
            # scan for !!callout etc for custom paragraph
            text_list = result[type_].get('rich_text')
            line0 = pydash.get(text_list, '0.text.content')
            line1 = pydash.get(text_list, '1.text.content')
            if line0 and line0.startswith('!!') and line1 == '\n':
                custom_type, *args = line0[2:].split()
                args = {
                    k.strip(): v.strip()
                    for i in args
                    for k, v in [i.split('=', 1)]
                }
                # print('='*80, 'CUSTOM??', custom_type, args)
                # print(repr(line0))
                # print(repr(line1))
                if custom_type in ('callout', 'todo', 'to_do', 'toggle'):
                    if custom_type == 'todo':
                        custom_type = 'to_do'
                    result['type'] = custom_type
                    result[custom_type] = result.pop(type_)
                    result[custom_type]['rich_text'] = text_list[2:]
                    if args.get('emoji'):
                        pydash.set_(result[custom_type], 'icon.emoji', args['emoji'])
                    if args.get('color'):
                        pydash.set_(result[custom_type], 'color', args['color'])
                    type_ = custom_type

        # move 2nd level nested paragraph to rich_text array
        # move 2nd level other block type to children
        if result[type_] and type_ != 'paragraph':
            text_list = result[type_].get('rich_text')
            if text_list:
                children = [
                    i
                    for i in text_list
                    if i.get('type') and i.get('type') != 'paragraph'
                ]
                def copy_inner_paragraph():
                    for item in text_list:
                        if 'type' not in item:
                            yield item
                        elif item.get('type') == 'paragraph':
                            yield from item['paragraph']['rich_text']
                result[type_]['rich_text'] = list(copy_inner_paragraph())
                if children:
                    if type_ in ('quote',):
                        # types that allow children
                        result[type_]['children'] = children
                    else:
                        warnings.warn(f'Lost of inner blocks {[i["type"] for i in children]}')

        # fix color
        if type_ == 'paragraph' and result[type_].get('rich_text'):
            # scan for <span style='color|background-color:<color>'> and </span>
            text_list = result[type_].get('rich_text')
            # {"text": {"content": "<span style='color:blue'>"}, "annotations": {"code": true}},
            # {"text": {"content": "blue text"}},  <<< can be many in between
            # {"text": {"content": "</span>"}, "annotations": {"code": true}},  <<< don't consider nesting style
            def fix_color(text_list):
                colors = []
                for item in text_list:
                    if pydash.get(item, 'annotations.code'):
                        style = decode_style(pydash.get(item, 'text.content'))
                        if style == '/':
                            if colors:
                                colors.pop(-1)  # remove last
                                continue
                        elif style:
                            colors.append(style)  # support nesting color
                            continue
                        # otherwise pass through to be rendered as inline html
                    if colors:
                        pydash.set_(item, 'annotations.color', colors[-1])
                    yield item
            result[type_]['rich_text'] = list(fix_color(text_list))

        return result

    def render_paragraph(self, element):
        # https://developers.notion.com/reference/block#paragraph-blocks
        return self._render_as("paragraph", element)

    def _text(self, element, bold=False, italic=False, strikethrough=False, underline=False, code=False, color: str = 'default', url=None):
        """
        :param code: True for inline code
        :param color: see full list https://developers.notion.com/reference/rich-text#annotations
        """
        # https://developers.notion.com/reference/rich-text#annotations
        annotations = {}
        if bold:
            annotations['bold'] = True
        if italic:
            annotations['italic'] = True
        if strikethrough:
            annotations['strikethrough'] = True
        if underline:
            annotations['underline'] = True
        if code:
            annotations['code'] = True
        if color and color != 'default':
            annotations['color'] = color
        text = self.render_children(element)
        if isinstance(text, list):
            # test.content should be string, flatten nesting children here
            # don't consider complex nesting for now
            # print('text <- ', json.dumps(text, indent=4))
            text = ' '.join([i['text']['content'] for i in text])
            # print('text -> ', json.dumps(text, indent=4))
        result = {
            'text': {
                'content': text,
            }
        }
        if url:
            # https://developers.notion.com/reference/rich-text#link-objects
            pydash.set_(result, 'text.link.url', url)
        if annotations:
            result['annotations'] = annotations
        return result

    def render_strikethrough(self, element):
        return self._text(element, strikethrough=True)

    def render_list(self, element):
        # https://developers.notion.com/reference/block#numbered-list-item-blocks
        # https://developers.notion.com/reference/block#bulleted-list-item-blocks
        result = self.render_children(element)
        assert isinstance(result, list)
        type_ = 'numbered_list_item' if element.ordered else 'bulleted_list_item'
        # print('render_list', type_, json.dumps(result, indent=4))
        for item in result:
            t, item['type'] = item['type'], type_
            item[type_] = item.pop(t)
        # print('render_list patched to', json.dumps(result, indent=4))
        return result
        # return self._render_as(type_, element)

    def render_list_item(self, element):
        result = self.render_children(element)
        if not isinstance(result, list) and len(result) == 1:
            warnings.warn(f'unexpect list item longer than 1 {json.dumps(result, indent=4)}')
            raise NotImplementedError
        return result[0]

    def render_quote(self, element):
        # https://developers.notion.com/reference/block#quote-blocks
        return self._render_as('quote', element)

    def render_fenced_code(self, element):
        # code block that starts and ends with ```
        lang = element.lang or ''
        lang = lang.lower()
        if lang not in (
            "abap", "arduino",
            "bash", "basic",
            "c", "clojure", "coffeescript", "c++", "c#", "css",
            "dart", "diff", "docker",
            "elixir", "elm", "erlang",
            "flow", "fortran", "f#",
            "gherkin", "glsl", "go", "graphql", "groovy",
            "haskell", "html",
            "java", "javascript", "json", "julia",
            "kotlin",
            "latex", "less", "lisp", "livescript", "lua",
            "makefile", "markdown", "markup", "matlab", "mermaid",
            "nix",
            "objective-c", "ocaml",
            "pascal", "perl", "php", "plain text", "powershell", "prolog", "protobuf", "python",
            "r", "reason", "ruby", "rust",
            "sass", "scala", "scheme", "scss", "shell", "solidity", "sql", "swift",
            "typescript",
            "vb.net", "verilog", "vhdl", "visual basic",
            "webassembly",
            "xml",
            "yaml",
            "java/c/c++/c#",
        ):
            lang = {'js': 'javascript'}.get(lang) or ''
        lang = lang or 'plain text'  # set default
        return self._render_as('code', element, language=lang)

    def render_code_block(self, element):
        # https://developers.notion.com/reference/block#code-blocks
        return self.render_fenced_code(element)

    def render_html_block(self, element):
        # https://developers.notion.com/reference/block#code-blocks
        return self._render_as('code', element, language='html')

    def render_thematic_break(self, element):
        # https://developers.notion.com/reference/block#divider-blocks
        return self._render_as('divider', None)

    def render_heading(self, element):
        # https://developers.notion.com/reference/block#heading-one-blocks
        if element.level <= 3:
            return self._render_as(f'heading_{element.level}', element)
        raise NotImplementedError

    def render_setext_heading(self, element):
        return self.render_heading(element)

    def render_blank_line(self, element):
        return self._render_as("paragraph", '')

    def render_link_ref_def(self, element):
        # TODO: quick bypass
        return self._render_as("paragraph", '')
        # raise NotImplementedError

    def render_emphasis(self, element):
        return self._text(element, italic=True)

    def render_strong_emphasis(self, element):
        return self._text(element, bold=True)

    def render_inline_html(self, element):
        return self._text(element, code=True)

    def render_link(self, element):
        # https://developers.notion.com/reference/rich-text#text-objects
        return self._text(element, url=element.dest)

    def render_auto_link(self, element):
        # https://developers.notion.com/reference/rich-text#link-objects
        return self._text(element.dest, url=element.dest)

    def render_image(self, element):
        # https://developers.notion.com/reference/block#image-blocks
        return {
            'type': 'image',
            'image': {
                'type': 'external',
                'external': element.dest
            }
        }
        # 'value': self.render_children(element),
        # 'title': element.title,

    def render_literal(self, element):
        return self._text(element)

    def render_raw_text(self, element):
        return self._text(element)

    def render_line_break(self, element):
        return self._text('\n')
        # return {
        #     'type': 'br',
        #     'soft': element.soft,
        # }

    def render_code_span(self, element):
        # code span is inline code
        return self._text(element, code=True)


class MarkoNotionExt:
    # see https://github.com/frostming/marko/blob/master/marko/ext/gfm/__init__.py#L79
    elements = [Strikethrough]


_md = marko.Markdown(marko.Parser, MarkoNotionRenderer)
_md.use(MarkoNotionExt)

def md(text):
    result = _md(text)
    # flattn first level list, for list items inside a list block
    def iteritems():
        for idx, item in enumerate(result):
            if isinstance(item, list):
                yield from item
                continue
            if not isinstance(item, dict):
                print(f'invalid format {idx}/{len(result)}', json.dumps(result, indent=4))
                raise ValueError('format')
            yield item
    return list(iteritems())

def md_line(text):
    """for title"""
    return pydash.get(md(text), '0.paragraph.rich_text') or text
