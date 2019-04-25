from google.cloud import vision
from lib.Word import Word
import re

class ParagraphHelper:
    def __init__(self, word_list=[], avg_symbol_width=0, avg_symbol_height=0, doc=None):
        """
        Class that helps produce paragraph lists in the format of (text, bounding box)

        Attributes:
            word_list (list): list of words
            avg_symbol_width (float): avg pixel width of symbol
            avg_symbol_height (float): avg pixel height of symbol 

        For Bounding Box (indices):
            0 -  top left
            1 - top right
            2 - bottom right
            3 - bottom left
        """
        if not doc:
            self.word_list = word_list
            self.avg_symbol_height = avg_symbol_width
            self.avg_symbol_width = avg_symbol_height
        else:
            # helper function which is an alternate way to initalize the ParagraphHelper Class
            self.seperate_to_words(doc)

        # Performing NLP here
        text = ' '.join([word['text'].replace(' ', '') for word in self.word_list])
        self.syntax_list = Word.analyze_text_syntax(text)
        self.entity_list = Word.analyze_text_entities(text)
        assert(len(self.word_list) == len(self.syntax_list))
        assert(len(self.word_list) == len(self.entity_list))

    @staticmethod
    def get_width_height(bounding_box):
        """
        Gets the width and the height of the bounding box
        """
        width = abs(bounding_box.vertices[1].x - bounding_box.vertices[0].x)
        height = abs(bounding_box.vertices[2].y - bounding_box.vertices[1].y)

        return width, height

    def get_paragraph_obj(self, paragraph_list):
        """
        Flattens a nested group of lines and words into a paragraph object which
        can be more easily interpreted

        Args:
            paragraph_list (list): A list of representing one paragraph from words and lines

        Returns:
            paragraph (obj): An object denoting the paragraph: { 'text':.. , 'bounding_box': ...}
        """

        # flattens all the lines into a list of word
        flattened_paragraph = [ word for line in paragraph_list for word in line ]

        # creates paragraph object
        width = 0
        most_left_word = min(flattened_paragraph, key=lambda x: x['word']['bounding_box'].vertices[0].x)
        if len(flattened_paragraph) == 1:
            scd_most_left = flattened_paragraph[0]['word']['bounding_box'].vertices[0].x
        else:
            # gets second most left word and adds width of first most left word so it can filter out the first bullet point extra spacing
            scd_left_word = min([word for word in flattened_paragraph if most_left_word != word], key=lambda x: x['word']['bounding_box'].vertices[0].x)
            scd_most_left = scd_left_word['word']['bounding_box'].vertices[0].x
            # makes sure that the left most word is not under to the second left most word
            # so it does not unnecessarily add a width
            if abs(most_left_word['word']['bounding_box'].vertices[0].x - scd_most_left) > self.avg_symbol_width * 2:
                width, height = ParagraphHelper.get_width_height(most_left_word['word']['bounding_box'])

        most_left = most_left_word['word']['bounding_box'].vertices[0].x
        most_right = max([word['word']['bounding_box'].vertices[2].x for word in flattened_paragraph])
        most_bot = max([word['word']['bounding_box'].vertices[2].y for word in flattened_paragraph])
        most_top = min([word['word']['bounding_box'].vertices[0].y for word in flattened_paragraph])
        

        paragraph = {
            'text' : ''.join([word['word']['text'] for word in flattened_paragraph]),
            'bounding_box': {
                "top_left": {'x': scd_most_left - width if len(most_left_word['word']['text']) <= 3 else most_left, 'y': most_top},
                "bot_right": {'x': most_right, 'y': most_bot}
            },
            'word_list': [ word['word'] for word in flattened_paragraph ],
            'entity_list': [ word['entity'] for word in flattened_paragraph ],
            'syntax_list': [ word['syntax'] for word in flattened_paragraph ]
        }

        return paragraph

    def check_paragraph_split(self, paragraph):
        """
        Checks if the paragraph should be split and returns a list of 
        paragraphs.

        """
        split_idxs = []
        prev_line = None
        for idx, line in enumerate(paragraph):
            if not prev_line:
                prev_line = line
                continue
            line_text = ' '.join([word['word']['text'] for word in line])
            first_word = line[0]['word']['text']
            # check if lines after first line have a point form character at the front
            is_next_paragraph = ( re.match(r'^(\s*(((\w{1,2}\s*(\.|\)))+?)|[^\w\ \(\$\'\"]|[^aAiI1-9](\s)+)(\s)*)', line_text) or   # checks if there is a bullet point
                (not re.match(r'\.\s*$', prev_line[-1]['word']['text']) and re.match(r'^\s*[A-Z]', first_word) and not line[0]['entity'])      # checks if prev_line has a . AND next line is capitalized
                and     
                (prev_line[-1]['word']['bounding_box'].vertices[2].x * self.avg_symbol_width * 15 > line[-1]['word']['bounding_box'].vertices[2].x) ) #checks if prev_line is much shorter than next line


            prev_line = line
            if not is_next_paragraph:
                continue
            split_idxs.append(idx)
            

        if split_idxs == []:
            return [ paragraph ]

        prev_idx = 0
        paragraphs = []
        # appends sections of the paragraph to paragraphs list
        for idx in split_idxs:
            paragraphs.append(paragraph[prev_idx:idx])
            prev_idx = idx

        # appends rest of list to paragraphs
        if paragraph[split_idxs[-1]:] != []:
            paragraphs.append(paragraph[split_idxs[-1]:])
        return paragraphs



    def is_adjacent_word(self, prev_word, curr_word):
        """
        Checks if the prev_word is adjacent to the currentw ord
        """

        lower_x_lim = (prev_word['bounding_box']).vertices[2].x - self.avg_symbol_height * 0.25
        upper_x_lim = (prev_word['bounding_box'].vertices[2].x + self.avg_symbol_width * 10)
        upper_y_lim = (prev_word['bounding_box'].vertices[2].y - self.avg_symbol_height * 1.5)
        lower_y_lim = (prev_word['bounding_box'].vertices[2].y - self.avg_symbol_height * 0.25)

        #print("%s %s %s %s" % (lower_x_lim, upper_x_lim, lower_y_lim, upper_y_lim) )
        #print(curr_word['bounding_box'].vertices[0])
        #print(curr_word['text'])
        #print('')
        if (lower_x_lim <= curr_word['bounding_box'].vertices[0].x <= upper_x_lim) and (upper_y_lim <= curr_word['bounding_box'].vertices[0].y <= lower_y_lim):
            return True
        return False

    def is_next_line(self, prev_line, line, temp_paragraph):
        """
        Checks if the current word is on the next line of the previous line
        """
        # create the bounds that can represent the next line
        # if its the first line, check for an indent

        prev_line = prev_line
        line = line
        temp_paragraph = [temp_line for temp_line in temp_paragraph]
        if len(prev_line) == 1:
            return False

        first_word = temp_paragraph[0][0]['word'] if len(temp_paragraph) > 1 and len(temp_paragraph[0]) > 1  else prev_line[0]['word']
        second_word = temp_paragraph[0][1]['word'] if len(temp_paragraph) > 1 and len(temp_paragraph[0]) > 1 else prev_line[1]['word']
        line_text = ' '.join([word['word']['text'] for word in prev_line])
        is_first_word_indent = re.match(r'^(\s*(((\w{1,2}\s*(\.|\)))+?)|[^\w\ \(\$\'\"]|[^aAiI1-9](\s)+)(\s)*)', line_text)

        next_word_x = second_word if is_first_word_indent else first_word
        next_word_y = prev_line[1]['word'] if is_first_word_indent else prev_line[0]['word']

        # previously handled indents not anymore. ON TODO list.
        # Not handled because if it falsely detects an indented point, it can ruin the paragraph formations
        lower_x_lim = next_word_x['bounding_box'].vertices[3].x - (self.avg_symbol_width * 2 if len(temp_paragraph) != 1 or is_first_word_indent else self.avg_symbol_width * 2)
        upper_x_lim = next_word_x['bounding_box'].vertices[3].x + self.avg_symbol_width * 5
        upper_y_lim = next_word_y['bounding_box'].vertices[3].y - self.avg_symbol_height
        lower_y_lim = next_word_y['bounding_box'].vertices[3].y + self.avg_symbol_height * 0.6

        """
        print("%s %s %s %s" % (lower_x_lim, upper_x_lim, lower_y_lim, upper_y_lim) )
        print(line[0]['bounding_box'].vertices[0])
        print(line[0]['text'])
        print((lower_x_lim <= line[0]['bounding_box'].vertices[0].x <= upper_x_lim) and (upper_y_lim <= line[0]['bounding_box'].vertices[0].y <= lower_y_lim))
        print('is first word indented: %s' % is_first_word_indent)
        print('')
        """
        
        if (lower_x_lim <= line[0]['word']['bounding_box'].vertices[0].x <= upper_x_lim) and (upper_y_lim <= line[0]['word']['bounding_box'].vertices[0].y <= lower_y_lim):
            return True
        return False
        


    def seperate_to_words(self, doc):
        """
        Seperates the words from the document from Google Vision API
        into a list of words and calculates the average width and height
        of a symbol.

        Args:
            doc (obj): document object form Google Vision API

        """
        breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType
        word_list = []
        avg_symbol_width_list = []
        avg_symbol_height_list = []

        for page in doc.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([
                            symbol.text + ' ' if symbol.property.detected_break.type in [breaks.SPACE, breaks.EOL_SURE_SPACE] else symbol.text for symbol in word.symbols
                        ])
                        temp_dict = {
                            'text': word_text,
                            'bounding_box': word.bounding_box
                        }
                        word_list.append(temp_dict)

                        for symbol in word.symbols:
                            width, height = ParagraphHelper.get_width_height(symbol.bounding_box)
                            avg_symbol_width_list.append(width)
                            avg_symbol_height_list.append(height)

        if len(avg_symbol_width_list) == 0 or len(avg_symbol_height_list) == 0:
            return None

        self.avg_symbol_width = sum(avg_symbol_width_list) / len(avg_symbol_width_list)
        self.avg_symbol_height = sum(avg_symbol_height_list) / len(avg_symbol_height_list)

        self.word_list = word_list

    def get_line_list(self):
        line_list = []
        line = []

        for idx, (word, entity, syntax) in enumerate(zip(self.word_list, self.entity_list, self.syntax_list)):
            word_obj = { 'word': word, 'entity': entity, 'syntax': syntax}
            if line == []:
                line.append(word_obj)
                continue

            # condition to check if curr word is part of the paragraph
            if self.is_adjacent_word(line[-1]['word'], word):
                line.append(word_obj)
            else:
                line_list.append(line)

                line = [word_obj]

            # checks if it is the last iteration
            if idx == len(self.word_list)-1:
                line_list.append(line)

        return line_list

    def get_paragraph_list(self):
        """
        Converts a word list into paragraphs list

        Returns:
            paragraph_list (list): list of paragraphs with { 'text':.. , 'bounding_box': ...}

        TODO: 
            * add a component that queries to find the next word if it is not an adjacent word because
              I am assuming the order of the words in the document work in a particular way
            * So I am assuming lines contains at least 2 words and that iS NOT the right assumption
        """
        paragraph_list = []
        line_list = self.get_line_list()
        temp_paragraph = []
        prev_line = None

        # grouping lines together into paragraphs
        for idx, line in enumerate(line_list):
            if not prev_line:
                temp_paragraph.append(line)
                prev_line = line
                continue
            if self.is_next_line(prev_line, line, temp_paragraph):
                temp_paragraph.append(line)
            else:
                # check if temp_paragraph should be split due to point forms
                temp_paragraphs = self.check_paragraph_split(temp_paragraph)
                # creates a paragraph object from paragraph
                paragraphs = [ self.get_paragraph_obj(paragraph) for paragraph in temp_paragraphs ]
                # converts paragraph into proper paragraph list format ('text', 'bounded_box')
                paragraph_list.extend(paragraphs)
                temp_paragraph = [line]

            # checks if it is the last iteration
            if idx == len(line_list)-1:
                temp_paragraphs = self.check_paragraph_split(temp_paragraph)
                paragraphs = [ self.get_paragraph_obj(paragraph) for paragraph in temp_paragraphs ]
                paragraph_list.extend(paragraphs)
            prev_line = line

        return paragraph_list
             

    def print(self):
        #print([word['text'] for word in self.word_list])
        print(self.avg_symbol_width)
        print(self.avg_symbol_height)
