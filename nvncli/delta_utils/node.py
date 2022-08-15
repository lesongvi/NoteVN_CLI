import urllib.parse
import bleach
from .render import *


__all__ = [
    'Node', 'TextLine', 'Image'
]


class Node(object):
    is_leaf = True
    def __init__(self, contents, attributes=None, parent=None, previous_node=None):
        self.contents = contents
        self.attributes = attributes or {}
        self.parent=None
        self.previous_node = previous_node

class TextLine(RenderMixin, Node):
    # NB at some point sanitization needs to be done.
    # https:/\nypi.org\nroject/html-sanitizer/ for the whole document
    # or use bleach for each element.
    
    standard_inline_styles = {
        'italic': ('<em>', '</em>'),
        'bold': ('<strong>', '</strong>'),
        'strike': ('<s>', '</s>'),
    }

    script_styles = {
        'sub': ('<sub>', '</sub>'),
        'super': ('<super>', '<super>')
    }
    
    css_font_size = {
        'small': 'small',
        # normal won't show up
        'large': 'large',
        'huge': 'x-large'
    }
    
    allowed_fonts = {
        'monospace': 'monospace, monospace',
        'serif': 'serif',
        # sans is default
    }
    
    text_span_css = [
        # quilljs attribute, css_attribute, translator
        ('size', 'font-size', 'css_font_size'), 
        ('font', 'font-family', 'allowed_fonts'),
        ('color', 'color', None),
        ('background', 'background-color', None)
    ]
    
    quill_diff_translator = {
        'insert': 'quill-diff-insert',
        'delete': 'quill-diff-delete',
    }
    
    css_classes = [
        # Attibute name, value translating dict. 
        ('quill_diff', 'quill_diff_translator')
    ]
    
    def __init__(self, strip_newline=False, *args, **keywords):
        super(TextLine, self).__init__(*args, **keywords)
        if strip_newline and self.contents.endswith("\n"):
            self.contents = self.contents[:-1]
        
    def pre_process_line(self, line):
        # this could be a place to do sanitization
        # or to add additional line breaks
        
        line = bleach.clean(line)
        
        return line
    
    def process_line_with_attributes(self, text_string):
        output = text_string
        for this_i in self.standard_inline_styles.keys():
            if this_i in self.attributes and self.attributes[this_i]:
                output = self.standard_inline_styles[this_i][0] + output + self.standard_inline_styles[this_i][1]
        
        for this_s in self.script_styles.keys():
            if 'script' in self.attributes and self.attributes['script'] == this_s:
                output = self.script_styles[this_s][0] + output + self.script_styles[this_s][1]
        
        css_styles = []
        for this_test in self.text_span_css:
            qflag, css_attribute, translator = this_test
            if qflag in self.attributes:
                if not translator:
                    css_styles.append(f"{css_attribute}: {self.attributes[qflag]}")
                else:
                    translated = getattr(self, translator).get(self.attributes[qflag], None)
                    if translated:
                        css_styles.append(f"{css_attribute}: {translated}")
                    else:
                        continue
        
        these_css_classes = []
        for this_test in self.css_classes:
            qflag, translator = this_test
            if qflag in self.attributes:
                translated = getattr(self, translator).get(self.attributes[qflag], None)
                if translated:
                    these_css_classes.append(f"{css_attribute}: {translated}")
                
        
        if css_styles:
            css_styles_string = ';'.join(css_styles)
            output = f'<span style="{css_styles_string}">{output}</span>'
        
        if these_css_classes:
            css_classes_string = ' '.join(these_css_classes)
            output = f'<span class="{css_classes_string}">{output}</span>'
        
        if 'link' in self.attributes:
            # Warning ... this needs to be carefully sanitized
            link = urllib.parse.quote(self.attributes['link'])
            output = f'<a href="{link}"{output}></a>'
        # should add colour and background colour here.
        return output
        
    
    def render_contents_html(self):
        # For now treat each inline block atomically. A refinement will be to
        # Look at the previous node, close any tags that should no longer be open
        # and open any new ones.
        
        # The way these functions are broken up would allow extensions to treat linebreaks sensibly, for example.
        # The quilljs project deltas refuse to do this.
        output = self.pre_process_line(self.contents)
        output = self.process_line_with_attributes(output)
        # should add colour and background colour here.
        return output
            
class Image(RenderMixin, Node):
    def render_contents_html(self):
        output = '<img src="%s">' % self.contents['image']
        if 'link' in self.attributes:
            # Warning ... this needs to be carefully sanitized
            link = urllib.parse.quote(self.attributes['link'])
            output = '<a href="%s">' % link + output + '</a>'
        return output
        
