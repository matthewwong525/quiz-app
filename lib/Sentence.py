from lib.Word import Word
from lib.AsyncRequest import AsyncRequest
from nltk.tokenize import sent_tokenize
from copy import deepcopy
import re


class Sentence:
    __subject_carry_over = ['this', 'it', 'he', 'she', 'his', 'her']

    def __init__(self, entity_list, syntax_list):
        """
        Initializes the sentence Object

        Args:
            entiity_obj (obj): a json response object returned from NLP lib for the syntax of the sentence
            syntax_obj (obj): a json response object returned from NLP lib for the entity of the sentence
            sent (string): the string value of the text

        TODO:
            * What happens when NLP detects an entity across paragraphs??????
        """
        self.words = []
        self.subject = None
        del_idxs = []
        words_i = 0
        syntax_list = deepcopy(syntax_list)
        entity_list = deepcopy(entity_list)
        entity_cnt_list = []
        for i, (syntax, entity) in enumerate(zip(syntax_list, entity_list)):
            # one syntax can have more than one word
            for word in syntax:
                if entity:
                    entity_cnt_list.append(str(word))  
                    # deletes if not last entity OR current entity == next entity 
                    if i != len(entity_list) - 1 and entity == entity_list[i+1]:
                        del_idxs.append(words_i)
                    else:
                        entity_content = ' '.join(entity_cnt_list)
                        word.add_entity(entity['type'], entity['salience'], entity_content, entity['wiki'])
                        entity_cnt_list = []
                words_i += 1
                self.words.append(word)

        # group words together and delete extra words if they are of the same entity
        for del_idx in sorted(del_idxs, reverse=True):
            del self.words[del_idx]

    def __str__(self):
        return self.return_string()

    def return_string(self):
        """
        :return: sentence in string format
        """
        return ' '.join([word.content for word in self.words])


    @staticmethod
    def init_sentences(sentence_list):
        """
        Initializes a list of sentences and performs the NLP requests

        Args:
            sentence_list ([str]): A list of sentences in text

        Returns:
            sentence_obj_list (list): A list of Sentence objects from the sentence_list 
        """
        # asynchronous requests with entities and lists
        async_req = AsyncRequest()
        entity_list = async_req.analyze_entities(sentence_list)
        syntax_list = async_req.analyze_syntax(sentence_list)

        sentence_obj_list = [ Sentence(ent_obj, synt_obj, sent) for ent_obj, synt_obj, sent in zip(entity_list, syntax_list, sentence_list) ]
        return sentence_obj_list


    def is_title(self):
        pos_list = [word.part_of_speech for word in self.words]
        return 'VERB' not in pos_list

    @staticmethod
    def get_sentences_from_paragraph(word_list, entity_list, syntax_list):
        paragraph_text = ' '.join([word['text'].replace(' ', '') for word in word_list])
        sent_text_list = sent_tokenize(paragraph_text)
        sent_obj_list = []
        count = 0

        assert(len(word_list) == len(syntax_list))

        #print(sent_text_list)
        #print([entity['content'] if entity else None for entity in entity_list])
        #print(' '.join([str(word[0]) for word in syntax_list]))
        
        
        # Splits the word, entity and syntax list based on `sent_tokenize`
        for sent_text in sent_text_list:
            for i, char in enumerate(paragraph_text):
                sentence = paragraph_text[count:i+1].lstrip()
                if sent_text == sentence:
                    split_list_idx = len([w for w in sentence.split(' ') if w != ''])
                    sent_obj_list.append(Sentence(entity_list[:split_list_idx], syntax_list[:split_list_idx]))
                    '''
                    print(sent_text)
                    print([entity['content'] if entity else None for entity in entity_list[:split_list_idx]])
                    print(' '.join([''.join([str(word) for word in words]) for words in syntax_list[:split_list_idx]]))
                    print(str(Sentence(entity_list[:split_list_idx], syntax_list[:split_list_idx])))
                    print('')
                    '''
                    entity_list = entity_list[split_list_idx:]
                    syntax_list = syntax_list[split_list_idx:]
                    #print(paragraph_text[count:i+1])
                    count = i+1
                    #print(paragraph_text[count:])
                    #print('')
                    break

        assert(len(sent_text_list) == len(sent_obj_list))
        return sent_obj_list



if __name__ == "__main__":
    test = Sentence(u'the Golden Gate is in Bell High School')
