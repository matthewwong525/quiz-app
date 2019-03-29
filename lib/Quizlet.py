import requests
import json

class Quizlet:
    def __init__(self, terms, definitions):
        """
        Initializes the Quizlet object
        """
        self.auth_token = self.get_secrets()
        self.terms = terms
        self.definitions = definitions

    def create_set(self, title):
        """
        Creates question sets based on the input title and terms/definitions
        """
        if len(self.terms) <= 1 or len(self.definitions) <= 1:
            return None
            
        headers = { 'Authorization': 'Bearer %s' % self.auth_token}
        
        payload = {
            'title' : title,
            'terms[]' : self.terms,
            'definitions[]' : self.definitions,
            'lang_terms' : 'en',
            'lang_definitions' : 'en'
        }

        r = requests.post('https://api.quizlet.com/2.0/sets', data=payload, headers=headers)

        return r

    def get_secrets(self):
        """
        Gets bearer token from the secrets.json file to make requests to quizlet
        """

        with open('credentials/secrets.json') as f:
            data = json.load(f)
        return data['QUIZLET_TOKEN']

    def add_questions(self, terms, definitions):
        """
        Adds questions
        """
        self.terms.extend(terms)
        self.definitions.extend(definitions)

if __name__ == "__main__":
    print(Quizlet().create_set("hello title", "test"))

