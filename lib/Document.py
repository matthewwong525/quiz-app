from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from lib.Sentence import Sentence

class Document:
    PIXEL_TOL_RANGE = 30
    def __init__(self, paragraph_list):
        self.root_node = Node('root')
        self.annotation_list = []

        # Removes paragraphs that only contain 1 character
        paragraph_list = [paragraph for paragraph in paragraph_list if len(paragraph[0]) > 1]
        layer_num = 1
        parent_nodes = [self.root_node]
        prev_layer_list = []
        prev_top_left_x_val = 0

        while paragraph_list:
            top_left_idx = Document.find_top_left(paragraph_list)
            top_left_x_val = paragraph_list[top_left_idx][1].vertices[0].x 

            # If next top left value is extremely far away from the previous top left value, 
            # break loop and set remaining values as annotations
            if top_left_x_val > prev_top_left_x_val + (Document.PIXEL_TOL_RANGE*5):
                self.annotation_list = paragraph_list
                break

            layer_list = Document.find_nodes_in_same_layer(paragraph_list, top_left_x_val)
            parent_node_idx_list = self.determine_parent_node(layer_list, prev_layer_list)

            # Add to child nodes to the previous layer
            if parent_nodes != []:
                new_parent_nodes = []
                for i, paragraph in enumerate(layer_list):

                    child_node = Node("layer: %s, child_num: %s" % (layer_num, i), parent=parent_nodes[parent_node_idx_list[i]], sentence=Sentence.seperate_sentences(layer_list[i][0]))
                    new_parent_nodes.append(child_node)

                # Update parent nodes list:
                parent_nodes = new_parent_nodes
                prev_layer_list = layer_list
                prev_top_left_x_val = top_left_x_val
                layer_num += 1
            else:
                paragraph_list = []

    @staticmethod
    def find_top_left(paragraph_list):
        """
        Top left node is defined as the left most paragraph within the first 5
        paragraphs
        """
        x_val_list = [paragraph_list[0][1].vertices[0].x for paragraph in paragraph_list[:5]]
        min_x = min(x_val_list)
        return x_val_list.index(min_x)

    @staticmethod
    def find_nodes_in_same_layer(paragraph_list, top_left_x_val):
        """
        Finds nodes in the same layer based on the x_value of the paragraph of the
        bounded box
        """
        top_layer_list = [] 
        remove_idx_list = []
        for idx, paragraph in enumerate(paragraph_list):
            x_val = paragraph[1].vertices[0].x
            if top_left_x_val - Document.PIXEL_TOL_RANGE <= x_val <= top_left_x_val + Document.PIXEL_TOL_RANGE:
                top_layer_list.append(paragraph_list[idx])
                remove_idx_list.append(idx)
        # Removing extra indices that are added to layer list
        for index in sorted(remove_idx_list, reverse=True):
            del paragraph_list[index]
        return top_layer_list

    def determine_parent_node(self, layer_list, prev_layer_list):
        """
        Returns indices of the layer on top of the current layer
        """
        parent_node_idx_list = []

        if prev_layer_list == []:
            return [0 for i in layer_list]

        prev_layer_y_list = [ paragraph[1].vertices[0].y for paragraph in prev_layer_list ]
        layer_y_list = [ paragraph[1].vertices[0].y for paragraph in layer_list ]

        remove_idx_list = []
        for idx, y in enumerate(layer_y_list):
            # Finds first index of parent node
            parent_idx = [i for i, val in enumerate(prev_layer_y_list) if y > val]

            # If there exists a node below a parent node, add the index to the list
            # otherwise, pop the index from the layer_list
            if parent_idx != []:
                parent_node_idx_list.append(parent_idx[-1])
            else:
                remove_idx_list.append(idx)
        
        # Removing extra indices that can't be matched with a parent node
        for index in sorted(remove_idx_list, reverse=True):
            del layer_list[index]

        return parent_node_idx_list

    def print(self):
        DotExporter(self.root_node).to_picture("test.png")
        print(RenderTree(self.root_node))






