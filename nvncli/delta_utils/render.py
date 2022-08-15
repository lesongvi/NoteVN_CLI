import urllib.parse
__all__ = ['RenderMixin', 'RenderOpenCloseMixin']

class RenderMixin(object):
    def render_html(self):
        if hasattr(self, 'open_tag'):
            return self.open_tag() + self.render_contents_html() + self.close_tag()
        else:
            return self.render_contents_html()

    def render_contents_html(self):
        these_contents = []
        for c in self.contents:
            these_contents.append(c.render_html())
        return(''.join(these_contents))
    
    def render_contents_html_recursive(self):
        """A recursive render of the tree. This is DEPRECATED and will be removed."""
        these_contents = []
        for c in self.contents:
            these_contents.append(c.render_html())
        return(''.join(these_contents))
        
    def render_tree(self):
        """A non-recursive way to render the tree."""
        # The distinction we really on is the idea that NODES ( .is_leaf = True) have contents that needs rendering
        # while BLOCKS (.is_leaf = False) have children (contents is a list) that need visiting. 
        output = []
        stack = []
        already_visited = []
        stack.append(self)
        while stack:
            this_node = stack.pop()
            if this_node not in already_visited:
                # All blocks (but not leaf nodes) wll need visiting again.  But put everything here to be safe.
                already_visited.append(this_node)
                # we are seeing it for the first time.
                if this_node.is_leaf: # Then we are dealing with a node, not a block, and should render the contents
                                      # but not look for children.
                    output.append(this_node.render_contents_html())
                else:
                    # then we are dealing with a block and should open it
                    if hasattr(this_node, 'open_tag'):
                        output.append(this_node.open_tag())
                    if hasattr(this_node, 'close_tag'):
                        # we will want to come back to this and close the tag, but only after visiting the contents
                        stack.append(this_node)
                    # we want to visit the contents of each block. But put them onto the stack in reverse order so
                    # that we visit the first one first.
                    for c in reversed(this_node.contents):
                        stack.append(c)
            else:
                if this_node.is_leaf:
                    # we have met this before, and it is a node ... we should never actually end here.
                    # this test is just here to be explicit about what is going on.
                    pass
                else:
                    # visiting for the second time, and we need to close it.
                    if hasattr(this_node, 'close_tag'):
                        output.append(this_node.close_tag())
        return ''.join(output)

class RenderOpenCloseMixin(RenderMixin):
    def open_tag(self):
        return('')
    
    def close_tag(self):
        return('')
        
    