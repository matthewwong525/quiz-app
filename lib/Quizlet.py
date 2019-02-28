import requests
import json

class Quizlet:
    def __init__(self, terms, definitions):
        self.auth_token = self.get_secrets()
        self.terms = terms
        self.definitions = definitions

    def create_set(self, title):
        if self.terms == [] or self.definitions == []:
            return "Document does not have enough info"
            
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
        with open('credentials/secrets.json') as f:
            data = json.load(f)
        return data['QUIZLET_TOKEN']

    def add_questions(self, terms, definitions):
        self.terms.extend(terms)
        self.definitions.extend(definitions)

if __name__ == "__main__":
    print(Quizlet().create_set("hello title", "test"))

