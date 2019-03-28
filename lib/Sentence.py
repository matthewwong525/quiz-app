from lib.Word import Word
from lib.AsyncRequest import AsyncRequest

from copy import deepcopy
import re


class Sentence:
    __subject_carry_over = ['this', 'it', 'he', 'she', 'his', 'her']

    def __init__(self, entity_obj, syntax_obj, sent):
        """
        TODO:
            * Make it only request NLP one time rather than one time for every sentence.
        """
        self.subject = None

        if 'error' in entity_obj or 'error' in syntax_obj:
            print('Entity Obj: %s' % entity_obj)
            print('Syntax Obj: %s' % syntax_obj)
            self.words = [ Word(text=sent)]
            return None

        entities = entity_obj['entities']
        tokens = syntax_obj['tokens']
 
        self.words = []
        entity_list = []

        # words_content_list makes it easier to group words later on
        # basically the string content of the words
        words_content_list = []

        # add word objects to Word list
        # add string content into words_content_list
        for token in tokens:
            self.words.append(Word(token))
            words_content_list.append(token['text']['content'])

        # includes all mentions in the entity_list
        for entity in entities:
            for mention in entity['mentions']:
                copy = deepcopy(entity)
                copy['name'] = mention['text']['content']
                entity_list.append(copy)

        entity_list.sort(key=lambda item: (-len(item['name']), item['name']))

        del_idxs = []

        # replace the words with entities if possible
        # group together words appearing in the same entity
        for entityContent in entity_list:
            entity_content_arr = entityContent['name'].split(' ')
            # loops through all the words within the sentence
            for i in range(len(words_content_list)):
                # prevents array out of bounds
                if i >= len(self.words):
                    break
                # checks if word is equal to the first word of the entity and if words after the first word are the same
                if words_content_list[i] == entity_content_arr[0] \
                        and words_content_list[i:i + len(entity_content_arr)] == entity_content_arr:
                    # adds words to index to be changed into entities
                    del_idxs.append({'range': (i + 1,i + len(entity_content_arr)), 'entityContent': entityContent})
                    words_content_list[i] = entityContent['name']
                    # sets the word_content_list to 0 so it doesn't match with another entity
                    for j in range(i + 1, i + len(entity_content_arr)):
                        words_content_list[j] = 0
                        # words.insert(i, entityContent)
                        #  replace this with actually creating a word object that has the appropriate attributes
                        # provided by entity (this means modifying the word object to be able to init a entity word)

        # converts the words into entities
        for del_obj in sorted(del_idxs, reverse=True, key=lambda k: k['range'][0]):
            del self.words[del_obj['range'][0]:del_obj['range'][1]]
            self.words[del_obj['range'][0]-1].add_entity(del_obj['entityContent'])


    def __str__(self):
        return self.return_string()

    def return_string(self):
        """
        :return: sentence in string format
        """
        return ' '.join([word.content for word in self.words])

    @staticmethod
    def update_subject(sentence_list):
        previous_subject = None
        for sentence in sentence_list:
            nouns = [word for word in sentence.words if word.part_of_speech == 'NOUN' or word.part_of_speech == 'PRON']
            if not nouns:
                sentence_list.remove(sentence)
                continue
            if nouns[0].content.lower() in Sentence.__subject_carry_over:
                sentence.subject = previous_subject
                if previous_subject:
                    nouns[0].content = sentence.subject.content
                else:
                    sentence_list.remove(sentence)
            else:
                entities = [noun for noun in nouns if noun.entity]
                if not entities:
                    sentence_list.remove(sentence)
                    continue
                sentence.subject = entities[0]
                previous_subject = sentence.subject
        return sentence_list

    @staticmethod
    def init_sentences(sentence_list):
        # asynchronous requests with entities and lists
        async_req = AsyncRequest()
        entity_list = async_req.analyze_entities(sentence_list)
        syntax_list = async_req.analyze_syntax(sentence_list)

        print('Performed async request to library')

        sentence_obj_list = [ Sentence(ent_obj, synt_obj, sent) for ent_obj, synt_obj, sent in zip(entity_list, syntax_list, sentence_list) ]
        print('Created Sentence obj list')
        return sentence_obj_list



if __name__ == "__main__":
    test = Sentence(u'the Golden Gate is in Bell High School')
