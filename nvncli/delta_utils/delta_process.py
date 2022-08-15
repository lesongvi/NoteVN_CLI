from .document import *
from . import block 
from . import block as bks
from . import node

__all__ = ['TranslatorBase', 'TranslatorQuillJS']

class TranslatorBase(object):
    """This is a base class for Delta formats."""
    def __init__(self):
        self.block_registry = {
            # text blocks will be handled by default
        }
        
        self.node_registry = {
            #self.string_node_test: self.make_string_node, # we will make the string the default
        }
        
        self.settings = {
            'list_text_blocks_are_p': True
        }
    
    def translate_to_html(self, delta_ops):
        return self.ops_to_internal_representation(delta_ops).render_html()
    
    def ops_to_internal_representation(self, delta_ops):
        this_document = QDocument()
        previous_block = None
        for qblock in self.yield_blocks(delta_ops):
            # first do the block
            arguments = (qblock, this_document, previous_block)
            matched_tests = tuple(test for test in self.block_registry.keys() if test(*arguments))
            if len(matched_tests) == 1:
                this_block = self.block_registry[matched_tests[0]](*arguments)
            elif len(matched_tests) > 1:
                raise ValueError("More than one test matched")
            else:
                # assume it is a standard text block
                this_block = self.make_standard_text_block(*arguments)
            previous_block = this_block
            
            # now do the nodes
            for this_content in qblock['contents']:
                node_arguments = {'block': this_block, 'contents': this_content['insert'], 'attributes': this_content.get('attributes', {}).copy()}
                node_matched_tests = tuple(test for test in self.node_registry.keys() if test(**node_arguments))
                if len(node_matched_tests) == 1:
                    previous_node = self.node_registry[node_matched_tests[0]](**node_arguments)
                elif len(node_matched_tests) > 1:
                    raise ValueError("More than one test matched.")
                else:
                    if isinstance(this_content['insert'], str):
                        previous_node = self.make_string_node(**node_arguments)
                    else:
                        raise ValueError("I don't know how to add this node. Default string handler failed. Node contents is %s" % node_arguments['contents'])
                ## The following line allows custom node creators to split a block in two if necessary -- for example
                ## a custom node adding a horizonal rule might do so.
                this_block = previous_node.parent
        return this_document
      
    def is_block(self, insert_instruction):
        return False # For extension later. Currently assumed that blocks are only marked by \n
 
    
    def yield_blocks(self, delta_ops):
        """Yields each block-level chunk, though without nesting blocks, which will be the responsibility of another function.
        Has the effect of de-normalizing Quilljs's compact representation.
    
        Blocks are yielded as a dictionary, consisting of
        {'contents': [...] # a list of dictionaries containing the nodes for the block.
         'attributes': {}  # a dictionary containing the attributes for the block
        }
        """
        block_marker = '\n' # currently assumed that there is one, and one only type of block marker.
        raw_blocks = []
        temporary_nodes = [] # the block marker comes at the end of the block, so we may not have one yet.
        block_keys = ['attributes']
        limit = len(delta_ops)
        for counter, instruction in enumerate(delta_ops):
            if 'insert' not in instruction:
                raise ValueError("This parser can only deal with documents.")
            insert_instruction = instruction['insert']
            if isinstance(insert_instruction, str):
                if not 'attributes' in instruction:
                    instruction['attributes'] = {}
                block_attributes = instruction['attributes']
                #if insert_instruction.endswith(block_marker):
                #    # then we have complete blocks.  
                #    last_node_completes_block = True
                #else:
                #    last_node_completes_block = False
                if block_marker not in insert_instruction:
                    temporary_nodes.append(instruction)
                    # if (counter + 1) == limit:
                    #     yield_this = {'contents': temporary_nodes[:]}
                    #     temporary_nodes = []
                    #     for k in instruction.keys():
                    #         if k in block_keys:
                    #             yield_this[k] = instruction[k]
                    #     yield yield_this
                elif insert_instruction == block_marker:
                    # put the newline on the end of the last instruction, just in case we need it
                    if not 'attributes' in instruction:
                        instruction['attributes'] = {}
                    block_attributes = instruction['attributes']
                    temporary_nodes.append({"insert": "\n", "attributes": block_attributes.copy()})
                    yield_this =  {'contents': temporary_nodes[:],}
                    for k in instruction.keys():
                        if k in block_keys:
                            yield_this[k] = instruction[k]
                        temporary_nodes = []
                    yield yield_this
                else:
                    sub_blocks = insert_instruction.split(block_marker)
                    sub_blocks_len = len(sub_blocks)
                    if sub_blocks[-1] == '':
                        sub_blocks.pop()
                        last_node_completes_block = True
                    else:
                        last_node_completes_block = False
                    for this_c, contents in enumerate(sub_blocks):
                        if last_node_completes_block or this_c < sub_blocks_len-1:
                            temporary_nodes.append({'insert': contents})
                            for k in instruction.keys():
                                if k in block_keys:
                                    temporary_nodes[-1][k] = instruction[k]
                            yield_this = {'contents': temporary_nodes[:]}
                            temporary_nodes = []
                            for k in instruction.keys():
                                if k in block_keys:
                                    yield_this[k] = instruction[k]
                            yield yield_this
                        else:
                            # on the last part of an insert statement but not a complete block
                            temporary_nodes.append({'insert': contents})
                            for k in instruction.keys():
                                if k in block_keys:
                                    temporary_nodes[-1][k] = instruction[k]
            else:
                if not self.is_block(insert_instruction):
                    temporary_nodes.append(instruction)
                else:
                    yield(instruction)
    
    def make_standard_text_block(self, qblock, this_document, previous_block):
        this_block = this_document.add_block(
            block.TextBlockParagraph(parent=this_document, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy())
            )
        return this_block
    
    def make_string_node(self, block, contents, attributes):
        if isinstance(block, bks.TextBlockCode):
            return block.add_node(node.TextLine(contents=contents, attributes=attributes, strip_newline=False))
        else:
            return block.add_node(node.TextLine(contents=contents, attributes=attributes, strip_newline=True))
        
    
    
    
class TranslatorQuillJS(TranslatorBase):
    """This class converts structures found in the QuillJS flavour of Delta formats."""
    def __init__(self):
        super(TranslatorQuillJS, self).__init__()
        self.block_registry.update({
            self.header_test: self.make_header_block,
            self.list_test: self.make_list_block,
            self.better_table_test: self.make_better_table_blocks,
            self.table_cell_test: self.make_table_cell_block,
            self.code_block_test: self.make_code_block,
            # text blocks will be handled by default
        })
        
        self.node_registry.update({
            #self.string_node_test: self.make_string_node, # we will make the string the default
            self.image_node_test: self.make_image_node,
        })
        
        
    
    ##### Test functions and node/block creators follow #####
    
    def header_test(self, qblock, this_document, previous_block):
        if 'header' in qblock['attributes']:
            return True
        else:
            return False
        
    def list_test(self, qblock, this_document, previous_block):
        if 'list' in qblock['attributes']:
            return True
        else:
            return False
    
    def better_table_test(self, qblock, this_document, previous_block):
        if qblock['attributes']:
            if qblock['attributes'].get('table-col', False) or qblock['attributes'].get('table-cell-line', False):
                return True
            else:
                return False
        return False
    
    def table_cell_test(self, qblock, this_document, previous_block):
        if qblock['attributes']:
            return qblock['attributes'].get('table', False)
    
    def code_block_test(self, qblock, this_document, previous_block):
        if 'code-block' in qblock['attributes']:
            return True
        else:
            return False
    
    def make_header_block(self, qblock, this_document, previous_block):
        this_block = this_document.add_block(
            block.TextBlockHeading(
                parent=this_document, last_block=previous_block, attributes=qblock['attributes'].copy()
                )
        )
        return this_block
    
    def make_code_block(self, qblock, this_document, previous_block):
        # should we be adding the contents of this block to a previous
        # textblock if there is one?
        # if so, we probably just want to return the previous block, so that the text can be added into it.
        if isinstance(previous_block, block.TextBlockCode) and \
        previous_block.attributes == qblock['attributes']: # relying on standard python mapping comparison.
            return previous_block
        
        this_block = this_document.add_block(
            block.TextBlockCode(
                parent=this_document, last_block=previous_block, attributes=qblock['attributes'].copy()
            )
        )
        return this_block
    
    def make_standard_text_block(self, qblock, this_document, previous_block):
        this_block = this_document.add_block(
            block.TextBlockParagraph(parent=this_document, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy()
                )
            )
        return this_block
    
    def make_list_block(self, qblock, this_document, previous_block):
        container_block = None
        required_depth = qblock['attributes'].get('indent', 0)
        
        # see if the previous block was part of a list
        lb_parents = [p for p in list(previous_block.get_parents()) if isinstance(p, block.ListItemBlock)]
        if lb_parents and lb_parents[0].attributes.get('indent', 0) == required_depth:
            # prefect, we can use this
            container_block = previous_block.parent
        elif lb_parents and lb_parents[0].attributes.get('indent', 0) < required_depth:
            # we are part of a list, but it isn't deep enough
            container_block = lb_parents[0]
            while required_depth > container_block.attributes.get('indent', 0):
                current_depth = container_block.attributes.get('indent', 0)
                if isinstance(container_block, block.ListBlock):
                    container_block = container_block.add_block(
                        block.ListItemBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
                        )
                    container_block.attributes['indent'] = current_depth + 1
                container_block = container_block.add_block(
                    block.ListBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
                    )
                container_block.attributes['indent'] = current_depth + 1
        else:
            # see if there is a parent list item that we can latch on to.
            container_block = None
            for candidate_block in lb_parents:
                if candidate_block.attributes.get('indent', 0) == required_depth:
                    container_block = candidate_block
                    break
            else:
                # perhaps the previous paragraph has the depth we need - but don't use it for a depth of 0 -- use the root document instead.
                if required_depth > 0 and previous_block.attributes.get('indent', 0) == required_depth:
                    container_block = previous_block.add_block(
                        block.ListBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
                        )
                else:
                    # Bail out and put it on the root document, building up to the depth needed.
                    container_block = this_document.add_block(
                        block.ListBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
                        )
                    
                    while required_depth > container_block.attributes.get('indent', 0):
                        current_depth = container_block.attributes.get('indent', 0)
                        if isinstance(container_block, block.ListBlock):
                            container_block = container_block.add_block(
                                block.ListItemBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
                                )
                            container_block.attributes['indent'] = current_depth + 1
                        container_block = container_block.add_block(
                            block.ListBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
                            )
                        container_block.attributes['indent'] = current_depth + 1
                        
        # finally, we should have a list block to add our current block to:
        # It should be wrapped in a list item block:
        container_block = container_block.add_block(
            block.ListItemBlock(parent=container_block, last_block=container_block, attributes=qblock['attributes'].copy())
            )
        
        if self.settings['list_text_blocks_are_p']:
            this_block = container_block.add_block(
                block.TextBlockParagraph(
                parent=container_block, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy()
                )
            )
        else:
            this_block = container_block.add_block(
                block.TextBlockPlain(
                parent=container_block, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy()
                )
            )
        return this_block
    
    def make_table_cell_block(self, qblock, this_document, previous_block):
        
        # This can be exended easily to cover the 
        # https://codepen.io/soccerloway/pen/WWJowj
        # Better table plugin, that allows multi-line paragraphs in cells 
        # and multi-span cells.  The appraoch is the same -- except that the 
        # cells and rows both have an id, and the first check should be whether a block
        # is part of the previous cell. 
        # https://github.com/soccerloway/quill-better-table
        
        container_row = None
        container_table = None
        
        # best case scenario - we are in the same table row are the previous block
        if previous_block and previous_block.parent and previous_block.parent.parent and isinstance(previous_block.parent.parent, block.TableRowBlock) and \
        previous_block.parent.parent.row_id == qblock['attributes']['table']: # this would also be in attributes of previous block
            container_row = previous_block.parent.parent
            container_table = previous_block.parent.parent.parent
        # next best case scenario - we are still in a table, but we need a new row
        elif previous_block and previous_block.parent and previous_block.parent.parent and isinstance(previous_block.parent.parent, block.TableRowBlock):
            container_table = previous_block.parent.parent
            container_row = container_table.add_block(
                block.TableRowBlock(qblock['attributes']['table'],
                attributes=qblock['attributes'].copy()
                )
            )
        else:
            # worst case scenario, we need a table too.
            # remove the id from the attributes
            table_attributes = qblock['attributes'].copy()
            del table_attributes['table']
            
            container_table = this_document.add_block(
                block.TableBlock(
                    attributes=table_attributes,
                )
            )
            
            container_row = container_table.add_block(
                block.TableRowBlock(qblock['attributes']['table'],
                attributes=qblock['attributes'].copy()
                )
            )
        # now at last we can make the table Cell!
        this_cell = container_row.add_block(
            block.TableCellBlock(
                attributes=qblock['attributes'].copy()
            )
        )
        
        # now we can add the contents of the cell
        this_block = this_cell.add_block(
            block.TextBlockPlain(
            parent=container_row, 
            last_block=previous_block, 
            attributes=qblock['attributes'].copy()
            )
        )
        
        return this_block
    
    def make_better_table_blocks(self, block, contents, attributes):
        container_table = None
        container_row = None
        if 'table-col' in qblock['attributes']:
            # we need to make a table column.
            # this should be the first thing in the table, so we can check to see if one exists, and if not, we can make the table.
            pass
        elif 'table-cell-line' in qblock['attributes']:
            # we have a cell of the table.  
            pass
        
    def image_node_test(self, block, contents, attributes):
        if isinstance(contents, dict) and 'image' in contents:
            return True
        else:
            return False
            
    def make_image_node(self, block, contents, attributes):
        return block.add_node(node.Image(contents=contents, attributes=attributes))
        
    def make_string_node(self, block, contents, attributes):
        if isinstance(block, bks.TextBlockCode):
            return block.add_node(node.TextLine(contents=contents, attributes=attributes, strip_newline=False))
        else:
            return block.add_node(node.TextLine(contents=contents, attributes=attributes, strip_newline=True))
        
    
    
    
    
