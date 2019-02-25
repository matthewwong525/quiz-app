import requests
import json

class Quizlet:
    def __init__(self):
        self.auth_token = self.get_secrets()

    def create_set(self, title, set_questions):
        terms = [ question.sentence.return_string() for question in set_questions]
        definitions = [str(question.answer.content) for question in set_questions]
        headers = { 'Authorization': 'Bearer %s' % self.auth_token}
        
        payload = {
            'title' : title,
            'terms[]' : terms,
            'definitions[]' : definitions,
            'lang_terms' : 'en',
            'lang_definitions' : 'en'
        }

        r = requests.post('https://api.quizlet.com/2.0/sets', data=payload, headers=headers)

        return r.text

    def get_secrets(self):
        with open('credentials/secrets.json') as f:
            data = json.load(f)
        return data['QUIZLET_TOKEN']

if __name__ == "__main__":
    print(Quizlet().create_set("hello title", "test"))

