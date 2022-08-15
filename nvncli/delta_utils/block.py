from .render import *
from .document import *

__all__ = [
    'Block',
    'TextBlockPlain',
    'TextBlockParagraph',
    'TextBlockHeading',
    'TextBlockCode',
    'ListBlock',
    'ListItemBlock',
    'TableBlock',
    'TableRow',
    'TableCell',
]



def text_paragraph_style_inline(block):
    """Pass in an attribute list and get a string suitable for use as an inline style in html"""
    styles=[]
    if 'align' in block.attributes:
        if block.attributes['align'] in ('center', 'left', 'right', 'justify'):
            styles.append('text-align: %s' % block.attributes['align'])
    
    if hasattr(block.parent, 'depth') and 'indent' in block.attributes and block.attributes['indent']:
        parent_depth = block.parent.depth
        #block_depth = block.depth # could also read from attributes
        attr_depth = block.attributes['indent']
        if attr_depth > block.depth:
            styles.append('margin-left: %spx' % ((attr_depth-parent_depth)*30))
    
    if not styles:
        return None
    else:
        return ';'.join(styles)



class Block(object):
    is_leaf = False
    """The contents of Block should be a list of nodes or other blocks."""
    def __init__(self, parent=None, contents=None, attributes=None, last_block=None):
        if contents:
            for content in contents:
                self.add_node(content)
        else:
            self.contents = []
        self.attributes = attributes or {}
        self.parent=parent
        self.last_block=last_block
    
    def add_node(self, this_node):
        if this_node in self.contents:
            raise ValueError("I can't contain a node twice!")
        if self.contents:
            this_node.previous_node = self.contents[-1]
        self.contents.append(this_node)
        this_node.parent = self
        return this_node
    
    def add_block(self, block):
        return self.add_node(block)
    
    def get_parents(self):
        working_block = self
        while hasattr(working_block, 'parent') and working_block.parent:
            working_block = working_block.parent
            yield working_block
    
    @property
    def depth(self):
        if not self.parent:
            raise ValueError
        else:
            depth = 0
            working_object = self.parent
            while True:
                if isinstance(working_object, QDocument):
                    break
                else:
                    if not working_object.parent:
                        raise ValueError
                    else:
                        working_object = working_object.parent
                        depth += 1
        return depth
                
        
        
class TextBlockPlain(RenderMixin, Block):
    def render_contents_html(self):
        output = []
        for c in self.contents:
            output.append(c.render_html())
        # the following code results in duplicated indents with the TextBlockParagraph at the moment.
        #inline_style = text_paragraph_style_inline(self)
        #if inline_style:
        #    output.insert(0, '<span style=%s>' % inline_style)
        #    output.append('</span>')
        return ''.join(output)

class TextBlockParagraph(RenderOpenCloseMixin, TextBlockPlain):
    def get_paragraph_tag(self):
        if 'blockquote' in self.attributes and self.attributes['blockquote']:
            return 'blockquote'
        else:
            return 'p'

    def open_tag(self):
        inline_style = text_paragraph_style_inline(self)
        open_tag = self.get_paragraph_tag()
        if inline_style:
            return '<%s style=%s>' % (open_tag, inline_style)
        else:
            return '<%s>' % self.get_paragraph_tag()
    
    def close_tag(self):
        return '</%s>' % self.get_paragraph_tag()

class TextBlockCode(RenderOpenCloseMixin, TextBlockPlain):
    def open_tag(self):
        inline_style = text_paragraph_style_inline(self)
        if inline_style:
            return f'<code style={inline_style}><pre>'
        else:
            return '<code><pre>'
        
    def close_tag(self):
        return '</code></pre>'
    

class TextBlockHeading(RenderOpenCloseMixin, Block):
    def get_header_tag(self):
        if not 'header' in self.attributes:
            raise ValueError
        
        if str(self.attributes['header']) not in '123456789' or not len(str(self.attributes['header'])) == 1:
            raise ValueError("Header must be a value between 1 and 9, got %s" % self.attributes['header'])
        
        header_tag = 'h' + str(self.attributes['header'])
        return header_tag
    
    def open_tag(self):
        header_tag = self.get_header_tag()
        inline_style = text_paragraph_style_inline(self)
        if inline_style:
            return '<%s style=%s>' % (header_tag, inline_style)
        else:
            return '<%s>' % self.get_header_tag()
    
    def close_tag(self):
        return '</%s>' % self.get_header_tag()


class ListBlock(RenderOpenCloseMixin, Block):
    _tags_list_type = {
        'bullet': ('<ul>', '</ul>'),
        'ordered': ('<ol>', '</ol>')
    }
    def __init__(self, list_type=None, *args, **keywords):
        super(ListBlock, self).__init__(*args, **keywords)
        self.attributes['list'] = list_type or keywords.get('list', 'ordered')
    
    def open_tag(self):
        return self._tags_list_type[self.attributes['list']][0]
    
    def close_tag(self):
        return self._tags_list_type[self.attributes['list']][1]
                
class ListItemBlock(RenderOpenCloseMixin, Block):
    def open_tag(self):
        return '<li>'
    
    def close_tag(self):
        return '</li>'
        
class TableBlock(RenderOpenCloseMixin, Block):
    def open_tag(self):
        return '<table>'
    
    def close_tag(self):
        return '</table>'
        
class TableRowBlock(RenderOpenCloseMixin, Block):
    def __init__(self, row_id, *args, **keywords):
        super(TableRowBlock, self).__init__(*args, **keywords)
        self.row_id = row_id
    
    def get_tag(self):
        if self.attributes.get('header', False):
            return 'hr'
        else:
            return 'tr'
    
    def open_tag(self):
        return '<%s>' % self.get_tag()
    
    def close_tag(self):
        return '</%s>' % self.get_tag()
    
class TableCellBlock(RenderOpenCloseMixin, Block):
    def open_tag(self):
        return '<td>'
        
    def close_tag(self):
        return '</td>'

class TableColumnDescriptor(RenderOpenCloseMixin, Block):
    def open_tag(self):
        if 'width' in self.attributes:
            w = self.attributes['width']
            return f'<col style="width: {w}">'
        else:
            return '<col>'
    
    def close_tag(self):
        return '</col>'
    