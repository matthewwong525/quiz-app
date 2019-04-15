from lib.Sentence import Sentence
from lib.Word import Word
from bs4 import BeautifulSoup
import requests


class Question:
    __key_words = ('is', 'was', 'because', 'in', 'during', 'between')

    def __init__(self, sentence):
        """
        Initializes the questions object

        Args:
            sentence (obj): Sentence object
            answer (str): the answer of the fill in the blank from the question
        """
        self.sentence = sentence
        self.answer = self.generate_blank()

    def generate_blank(self):
        """
        Generates a blank in the question based on the entity and returns
        a string representing the answer
        """
        # sorts the words by highest salience first
        words = sorted(self.sentence.words, key=lambda x: x.salience, reverse=True)
        # keep only the words that are entities
        words = [word for word in words if word.entity and len(str(word)) > 1]

        answer = words[0]
        # replace the word being used as answer with a blank
        for i, word in enumerate(self.sentence.words):
            if word == answer:
                self.sentence.words[i] = Word()
        return answer

    def export(self):
        return self.sentence.return_string(), self.answer.content

    @staticmethod
    def is_question(sentence):
        """
        Checks if the sentence is a question
        """
        # gets list of all entities in the sentence
        entities = [word for word in sentence.words if word.entity]
        pos_list = [word.part_of_speech for word in sentence.words]
        max_salience = max([word.salience for word in sentence.words])

        words = sorted(sentence.words, key=lambda x: x.salience, reverse=True)
        word_answers = [word for word in words if word.entity and len(str(word)) > 1]


        # gets all the words in the sentence as a list of strings
        words = sentence.return_string().split()
        if len(entities) == 0 or len(sentence.words) <= 1 or max_salience < 0.1 or ('VERB' not in pos_list) or not word_answers:
            return False

        return True

    @staticmethod
    def get_wiki_questions(sentence):
        """
        Creates a question wiki question based on the wiki page
        (Still in construction)
        """
        wiki_links = set([word.wiki for word in sentence.words if word.wiki and word.salience > 0.25])
        if len(wiki_links) == 0:
            return Question(sentence)
        soup = [BeautifulSoup(requests.get(link).text, "html.parser") for link in wiki_links]
        # either find the sentence using this soup object, or use the wikipedia api to get the first sentence
        wiki_sentences = Question(sentence)
        # replace sentence with a list of sentences from the wikis, plus the original sentence
        # the sentence from the wikipedia can be in the form of Entity: sentence, with the entity being blanked later on
        # make sure to convert the string sentence into a Sentence object
        return wiki_sentences


if __name__ == "__main__":
    tests = [Sentence(u'Elon Musk flew a car into space.'),
             Sentence(u'Elon Musk flew a car into space.'),
             Sentence(u'Socrates was a greek philosopher'),
             Sentence(u'he was a very important person')]
    Sentence.update_subject(tests)

    wiki = Question.get_wiki_questions(tests[2])
    questions = [Question(test) for test in tests if Question.is_question(test)]
    for question in questions:
        print(question.export())
