from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import six
class Word:
    def __init__(self, token=None, text=None):
        """
        Initializes word object based on token or text

        Args:
            token (obj): token object from NLP lib (syntax)
            text (str): the string of the word
        """
        if text:
            self.content = text
            self.part_of_speech = 'UNKNOWN'
        elif token:
            pos_tag = (
            'UNKNOWN', 'ADJ', 'ADP', 'ADV', 'CONJ', 'DET', 'NOUN', 'NUM', 'PRON', 'PRT', 'PUNCT', 'VERB', 'X', 'AFFIX')
            self.content = token.text.content
            self.part_of_speech = token.part_of_speech.tag
        else:
            self.content = "____"
            self.part_of_speech = None
        self.entity = None
        self.salience = 0
        self.wiki = None

    def add_entity(self, entity, salience, content, wiki):
        """
        Adds the entitiy to the word object

        Args:
            entity (obj): entity object from NLP lib
        """
        entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                       'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER', 'PHONE_NUMBER', 'ADDRESS', 'DATE', 'NUMBER', 'PRICE')

        self.entity = entity_type[entity] if entity < len(entity_type) else entity_type[0]
        self.salience = salience
        self.content = content
        self.wiki = wiki

    def print_word(self):
        print({"content": self.content, "part_of_speech": self.part_of_speech, "entity": self.entity,
               "salience": self.salience})

    @staticmethod
    def analyze_text_syntax(text):
        if isinstance(text, six.binary_type):
            text = text.decode('utf-8')
        client = language.LanguageServiceClient()

        # Instantiates a plain text document.
        document = types.Document(
            content=text,
            type=enums.Document.Type.PLAIN_TEXT)

        # Detects tokens in the document.
        tokens = client.analyze_syntax(document).tokens

        text_list = text.split(' ')
        word_obj_list = []
        count = 0

        # creates a list of [Word] to match syntax with Word
        for i, word in enumerate(text_list):
            token = tokens[count]
            token_text = token.text.content.replace(' ', '')
            is_same_word = token_text == text_list[i]
            if is_same_word:
                word_obj_list.append([Word(token=token)])
                count += (1 if count < len(tokens) - 1 else 0)

            # multiple tokens per word
            elif token_text in text_list[i]:
                remaining_word = text_list[i].replace(token_text, '', 1)
                temp_list = []
                temp_list.append(Word(token=token))
                while remaining_word != '':
                    count += 1
                    token = tokens[count]
                    token_text = token.text.content.replace(' ', '')
                    if token_text in remaining_word:
                        temp_list.append(Word(token=token))
                        remaining_word = remaining_word.replace(token_text, '', 1)
                    else:
                        print(token_text)
                        print(remaining_word)
                        print([str(word) for word in temp_list])
                        print('Internal NLP Error')
                        count -= 1
                        break
                word_obj_list.append(temp_list)
                count += 1

            # multiple words per token
            elif text_list[i] in token_text:
                word_obj_list.append([Word(token=token)])
                if token_text[-len(text_list[i]):] == text_list[i]:
                    count += 1
            else:
                word_obj_list.append([Word(text=word)])

        return word_obj_list


    @staticmethod
    def analyze_text_entities(text):
        if isinstance(text, six.binary_type):
            text = text.decode('utf-8')
        client = language.LanguageServiceClient()

        # Instantiates a plain text document.
        document = types.Document(
            content=text,
            type=enums.Document.Type.PLAIN_TEXT)

        entities = client.analyze_entities(document, encoding_type='UTF8').entities
        ent_obj_list = [None] * len(text.split(' '))

        consumed_ent_idx = []
        for entity in entities:
            for mention in entity.mentions:
                if entity.name != mention.text.content:
                    continue

                ent_location = mention.text.begin_offset
                words = text.encode('utf-8')[:ent_location].decode('utf-8').split(' ')
                ent_idx = len([w for w in words if w != ''])

                for i, word in enumerate(entity.name.split(' ')): 
                    if i+ent_idx >= len(ent_obj_list) or i+ent_idx in consumed_ent_idx:
                        break
                    consumed_ent_idx.append(i+ent_idx)
                    ent_type = entity.type
                    ent_salience = entity.salience
                    ent_content = entity.name
                    ent_wiki = entity.metadata.wikipedia_url if hasattr(entity, 'metadata') and hasattr(entity.metadata, 'wikipedia_url') else None
                    ent_obj_list[ent_idx+i] = {
                        'type': ent_type,
                        'salience': ent_salience,
                        'content': ent_content,
                        'wiki': ent_wiki
                    }
        return ent_obj_list


    def __str__(self):
        return self.content

if __name__ == "__main__":
    a = Word.analyze_text_syntax("• I cannot couldn't • wouldn't eat food")
    #print([entity['content'] if entity else None for entity in a])
    print([''.join([str(word) for word in words]) for words in a])

