from google.cloud import vision
import re

class ParagraphHelper:
    def __init__(self, word_list=[], avg_symbol_width=0, avg_symbol_height=0, doc=None):
        """
        Class that helps produce paragraph lists in the format of (text, bounding box)

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
            self.seperate_to_words(doc)

    @staticmethod
    def get_width_height(bounding_box):
        width = abs(bounding_box.vertices[1].x - bounding_box.vertices[0].x)
        height = abs(bounding_box.vertices[2].y - bounding_box.vertices[1].y)

        return width, height

    @staticmethod
    def get_paragraph_obj(paragraph_list):
        # flattens all the lines into a list of word
        flattened_paragraph = [ word for line in paragraph_list for word in line ]

        # creates paragraph object
        most_left = min([word['bounding_box'].vertices[0].x for word in flattened_paragraph])
        most_right = max([word['bounding_box'].vertices[2].x for word in flattened_paragraph])
        most_bot = max([word['bounding_box'].vertices[2].y for word in flattened_paragraph])
        most_top = min([word['bounding_box'].vertices[0].y for word in flattened_paragraph])

        paragraph = {
            'text' : ''.join([word['text'] for word in flattened_paragraph]),
            'bounding_box': {
                "top_left": {'x': most_left, 'y': most_top},
                "bot_right": {'x': most_right, 'y': most_bot}
            }
        }

        return paragraph

    @staticmethod
    def check_paragraph_split(paragraph):
        """
        Checks if the paragraph should be split and returns a list of 
        paragraphs.

        """
        split_idxs = []
        for idx, line in enumerate(paragraph):
            first_word = line[0]['text']
            # check if lines after first line have a point form character at the front
            if idx is 0 or not re.match('(^((\w{1,2}(\.|\)))+?)|^-|^•|^→|^o|^·)(\s|)+$', first_word):
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
        lower_x_lim = (prev_word['bounding_box']).vertices[2].x - self.avg_symbol_height * 0.25
        upper_x_lim = (prev_word['bounding_box'].vertices[2].x + self.avg_symbol_width * 6)
        upper_y_lim = (prev_word['bounding_box'].vertices[2].y - self.avg_symbol_height * 1.5)
        lower_y_lim = (prev_word['bounding_box'].vertices[2].y - self.avg_symbol_height * 0.25)

        #print("%s %s %s %s" % (lower_x_lim, upper_x_lim, lower_y_lim, upper_y_lim) )
        #print(curr_word['bounding_box'].vertices[0])
        #print(curr_word['text'])
        #print('')
        if (lower_x_lim <= curr_word['bounding_box'].vertices[0].x <= upper_x_lim) and (upper_y_lim <= curr_word['bounding_box'].vertices[0].y <= lower_y_lim):
            return True
        return False

    def is_next_line(self, line, curr_word, temp_paragraph):
        # create the bounds that can represent the next line
        # if its the first line, check for an indent

        # may not always work fix later.
        if len(line) == 1:
            return False    
        first_word = temp_paragraph[0][0] if len(temp_paragraph) > 1 and len(temp_paragraph[0]) > 1  else line[0]
        second_word = temp_paragraph[0][1] if len(temp_paragraph) > 1 and len(temp_paragraph[0]) > 1 else line[1]
        is_first_word_indent = re.match('(^((\w{1,2}(\.|\)))+?)|^-|^•|^→|^o|^·)(\s|)+$', first_word['text'])

        next_word_x = second_word if is_first_word_indent else first_word
        next_word_y = line[1] if is_first_word_indent else line[0]

        # extra if statement here deals with indents
        lower_x_lim = next_word_x['bounding_box'].vertices[3].x - (self.avg_symbol_width * 3 if len(temp_paragraph) != 1 or is_first_word_indent else self.avg_symbol_width * 12)
        upper_x_lim = next_word_x['bounding_box'].vertices[3].x + self.avg_symbol_width * 3
        upper_y_lim = next_word_y['bounding_box'].vertices[3].y 
        lower_y_lim = next_word_y['bounding_box'].vertices[3].y + self.avg_symbol_height * 0.5

        """
        print("%s %s %s %s" % (lower_x_lim, upper_x_lim, lower_y_lim, upper_y_lim) )
        print(curr_word['bounding_box'].vertices[0])
        print(curr_word['text'])
        print((lower_x_lim <= curr_word['bounding_box'].vertices[0].x <= upper_x_lim) and (upper_y_lim <= curr_word['bounding_box'].vertices[0].y <= lower_y_lim))
        print('')
        """
        
        if (lower_x_lim <= curr_word['bounding_box'].vertices[0].x <= upper_x_lim) and (upper_y_lim <= curr_word['bounding_box'].vertices[0].y <= lower_y_lim):
            return True
        return False
        


    def seperate_to_words(self, doc):
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

        self.avg_symbol_width = sum(avg_symbol_width_list) / len(avg_symbol_width_list)
        self.avg_symbol_height = sum(avg_symbol_height_list) / len(avg_symbol_width_list)

        self.word_list = word_list


    def get_paragraph_list(self):
        """
        Converts a word list into paragraphs list

        TODO: 
            * add a component that queries to find the next word if it is not an adjacent word because
              I am assuming the order of the words in the document work in a particular way
            * So I am assuming lines contains at least 2 words and that iS NOT the right assumption
        """
        temp_word_list = list(self.word_list)
        paragraph_list = []
        line = []
        temp_paragraph = []

        for idx, word in enumerate(temp_word_list):
            # checks if first word has been reset
            if line == []:
                line.append(word)
                continue

            # condition to check if curr word is part of the paragraph
            if self.is_adjacent_word(line[-1], word):
                line.append(word)
            
            # elif condition to check if the next line is part of the same word
            # also takes into account of indents
            # TODO: COULD PRODUCE ERROR HERE BECAUSE OF THE LIST CUTTING
            elif self.is_next_line(line, word, temp_paragraph):
                line[-1]['text'] += ' '
                temp_paragraph.append(line)
                line = [word]
            else:
                temp_paragraph.append(line)
                # check if temp_paragraph should be split due to point forms
                temp_paragraphs = ParagraphHelper.check_paragraph_split(temp_paragraph)
                # creates a paragraph object from paragraph
                paragraphs = [ ParagraphHelper.get_paragraph_obj(paragraph) for paragraph in temp_paragraphs ]

                # converts paragraph into proper paragraph list format ('text', 'bounded_box')
                paragraph_list.extend(paragraphs)
                line = [word]
                temp_paragraph = []

            # checks if it is the last iteration
            if idx == len(temp_word_list)-1:
                temp_paragraph.append(line)

                paragraph = ParagraphHelper.get_paragraph_obj(temp_paragraph)
                paragraph_list.append(paragraph)

        return paragraph_list
             

    def print(self):
        #print([word['text'] for word in self.word_list])
        print(self.avg_symbol_width)
        print(self.avg_symbol_height)
