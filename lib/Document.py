from anytree import Node, RenderTree, PreOrderIter
from anytree.exporter import DotExporter
from lib.Sentence import Sentence
from lib.Question import Question
from lib.Quizlet import Quizlet
import re

class Document:
    def __init__(self, paragraph_list, symbol_width, symbol_height):
        """
        Creates a tree structure that outlines the nested structure of the document

        Args:
            paragraph_list (list): list of paragraphs with { 'text':.. , 'bounding_box': ...}
            symbol_width (float): avg pixel width of symbol
            symbol_height (float): avg pixel height of symbol 

        Attributes:
            root_node (Node): the root node of the tree structure
            annotation_list (list): the extra paragraphs that don't fit within the tree structure
            symbol_width (float): avg pixel width of symbol
            symbol_height (float): avg pixel height of symbol 

        TODO:
            * Rotate image so that the text can be aligned before sending it to the vision api
            * Deal with differen columns on the same page
            * Deal with multiple pages and combining pages together
        """
        self.root_node = Node('root')
        self.annotation_list = []
        self.symbol_width = symbol_width
        self.symbol_height = symbol_height

        # Removes paragraphs that does not contain letters or numbers
        paragraph_list = [paragraph for paragraph in paragraph_list if re.search('\w', paragraph['text'])]
        layer_num = 1
        parent_nodes = [self.root_node]
        prev_layer_list = []
        prev_top_left_x_val = 0

        # loops through layers until there are no more 
        while paragraph_list:
            top_left_idx = Document.find_top_left(paragraph_list)
            top_left_x_val = paragraph_list[top_left_idx]['bounding_box']['top_left']['x']

            # If next top left value is extremely far away from the previous top left value, 
            # break loop and set remaining values as annotations
            if prev_top_left_x_val != 0 and top_left_x_val > prev_top_left_x_val + (20*self.symbol_width):
                self.annotation_list.extend(paragraph_list)
                break

            # Add child nodes to the previous layer
            if parent_nodes != []:
                layer_list = self.find_nodes_in_same_layer(paragraph_list, top_left_x_val)
                parent_node_idx_list = self.determine_parent_node(layer_list, prev_layer_list)
                new_parent_nodes = []
                for i, paragraph in enumerate(layer_list):
                    # TODO: seperate this section to init questions section
                    child_node = Node("layer: %s, child_num: %s" % (layer_num, i), parent=parent_nodes[parent_node_idx_list[i]], text=paragraph['text'])
                    new_parent_nodes.append(child_node)

                # Update parent nodes list:
                parent_nodes = new_parent_nodes
                prev_layer_list = layer_list
                prev_top_left_x_val = top_left_x_val
                layer_num += 1
            else:
                self.annotation_list.extend(paragraph_list)
                break

    @staticmethod
    def find_top_left(paragraph_list):
        """
        Top left node is defined as the left most paragraph within the first 5
        paragraphs

        Args:
            paragraph_list (list): list of paragraphs with { 'text':.. , 'bounding_box': ...}

        Returns:
            idx (int): the index within the paragraph list

        TODO:
            * Think of a way to make this better because might have to distinguish
              between a diagram and text files.
        """
        x_val_list = [ paragraph['bounding_box']['top_left']['x'] for paragraph in paragraph_list[:5]]
        min_x = min(x_val_list)
        return x_val_list.index(min_x)

    def find_nodes_in_same_layer(self, paragraph_list, top_left_x_val):
        """
        Finds nodes in the same layer based on the x_value of the paragraph of the
        bounded box

        Args:
            paragraph_list (list): list of paragraphs with { 'text':.. , 'bounding_box': ...}
            top_left_x_val (int): the pixel x value of the top left paragraph

        Returns:
            top_layer_list (list): list of paragraphs that belong in the same layer in the tree structure 
        """
        top_layer_list = [] 
        remove_idx_list = []
        avg_x = top_left_x_val
        #print(avg_x)
        #print(4.5 * self.symbol_width)
        for idx, paragraph in enumerate(paragraph_list):
            x_val = paragraph['bounding_box']['top_left']['x']
            next_layer_tol = 4.5 * self.symbol_width
            if avg_x - next_layer_tol <= x_val <= avg_x + next_layer_tol:
                avg_x = (x_val + avg_x) / 2
                #print(paragraph_list[idx])
                top_layer_list.append(paragraph_list[idx])
                remove_idx_list.append(idx)
        # Removing indices that are added to layer list
        for index in sorted(remove_idx_list, reverse=True):
            del paragraph_list[index]
        #print('')
        return top_layer_list

    def determine_parent_node(self, layer_list, prev_layer_list):
        """
        Returns indices that match this current layer to the previous layer
        Essentially matches the children nodes to the parent nodes

        Args:
            layer_list (list): the current layer list in tree structure
            prev_layer_list (list): the previous layer list in tree structure

        Returns:
            parent_node_idx_list (list): list of indices of the parent nodes

        """
        parent_node_idx_list = []

        if prev_layer_list == []:
            return [0 for i in layer_list]

        prev_layer_y_list = [ paragraph['bounding_box']['top_left']['y'] for paragraph in prev_layer_list ]
        layer_y_list = [ paragraph['bounding_box']['top_left']['y'] for paragraph in layer_list ]

        remove_idx_list = []
        for idx, y in enumerate(layer_y_list):
            # Finds first index of parent node
            parent_idx = [i for i, val in enumerate(prev_layer_y_list) if (val - self.symbol_height*0.5) <= y]

            # If there exists a node below a parent node, add the index to the list
            # otherwise, pop the index from the layer_list
            if parent_idx != []:
                parent_node_idx_list.append(parent_idx[-1])
            else:
                self.annotation_list.append(layer_list[idx])
                remove_idx_list.append(idx)
        
        # Removing extra indices that can't be matched with a parent node
        for index in sorted(remove_idx_list, reverse=True):
            del layer_list[index]

        return parent_node_idx_list

    def create_questions(self):
        """
        Gathers the tree structure and annotation list and generates questions.
        Afterwards, it gathers the questions and sends the questions to Quizlet and
        returns the response from Quizlet

        Returns:
            resp (obj): the json response from Quizlet
        """
        prev_node = self.root_node
        node_iter = PreOrderIter(prev_node)
        question_list = []

        terms = []
        definitions = []

        sentence_list = []

        for node in node_iter:
            # check if question is empty in node

            if node == self.root_node:
                continue

            question_starter = ''
            if len(node.ancestors) > 1:
                question_starter = 'For:\n%s ;\n\n' % ' ;\n'.join([ parent.text[:25] + ('...' if len(parent.text) > 25 else '') for parent in node.ancestors if parent != self.root_node])
                # checks if prev node is not a sibling 
                # Creates a property question based on subtopic here
                if prev_node is node.parent:
                    node_layer = [sibling for sibling in node.siblings]
                    node_layer.append(node)

                    # if there is only one property, skip question
                    if len(node_layer) <= 1:
                        continue

                    temp_term = "%sWhat are the %s properties?" % (question_starter, len(node_layer))
                    temp_definition = '\n'.join([ "%s. " % (i+1) + sibling.text for i, sibling in enumerate(node_layer) ])
                    terms.append(temp_term)
                    definitions.append(temp_definition)

            prev_node = node
            
            # Appends 
            temp_sentence_list =re.split('\.', node.text)
            sentence_list.extend(temp_sentence_list)

        for annotation in self.annotation_list:
            temp_sentence_list = re.split('\.', annotation['text'])
            sentence_list.extend(temp_sentence_list)


        questions = Document.questions_from_sentlist(sentence_list)

        temp_terms = [ question_starter + question.sentence.return_string() for question in questions]
        temp_definitions = [str(question.answer.content) for question in questions]

        # extend the question list
        terms.extend(temp_terms)
        definitions.extend(temp_definitions)

        print('Created terms and definitions')

        if not (terms and definitions):
            return None

        print('Now sending response to quizlet')

        quizlet_client = Quizlet(terms, definitions)
        resp = quizlet_client.create_set("Test Set")

        print('Received response from quizlet')
        return resp

    def questions_from_sentlist(sentence_list):
        """
        Creates questions from a list of sentences

        Args:
            sentence_list (list): a list of strings denoting the sentences

        Returns:
            questions ([Question]): list of question objects
        """
        sentenceObjList = Sentence.init_sentences(sentence_list)
        sentenceObjList = Sentence.update_subject(sentenceObjList)
        questions = [Question(sent) for sent in sentenceObjList if Question.is_question(sent)]

        return questions


    def print(self):
        """
        Prints the tree as well as the annotation list
        """
        print(RenderTree(self.root_node).by_attr("text"))
        for paragraph in self.annotation_list:
            print(paragraph['text'])

