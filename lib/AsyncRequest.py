from google.oauth2 import service_account
from google.auth.transport import requests

import aiohttp
import asyncio
import os

class AsyncRequest:
    def __init__(self):
        """
        Initializes the AsyncRequest Class which prepares async requests

        Attributes:
            credentials (obj): the credentials object from Google which gives the access_token for requests
            nlp_headers (obj): the headers for the NLP libraries

        """
        SCOPES = ['https://www.googleapis.com/auth/cloud-language']

        self.credentials = service_account.Credentials.from_service_account_file(os.environ['GOOGLE_APPLICATION_CREDENTIALS'], scopes=SCOPES)
        self.credentials.refresh(requests.Request())

        self.nlp_headers = {
            "content-type": "application/json",
            "Authorization": "Bearer " + self.credentials.token
        }

    async def post_req(self, session,url, payload, headers):
        """
        Performs asynchronous post request

        Returns:
            json_resp: the json response of the post request
        """
        async with session.post(url, json=payload, headers=headers) as resp:
            json_resp = await resp.json()
            return json_resp

    async def nlp_req(self, url, text_list):
        """
        Starts an asynchronous session and makes a post request based on the list of text to
        the NLP libraries

        Args:
            url (str): url to make the NLP request to
            text_list (list): list of strings to be analyzed

        Returns:
            nlp_list (list): a list of the responses from the NLP libraries

        """
        async with aiohttp.ClientSession() as session:
            req_list = []
            for sentence in text_list:
                req_list.append(self.post_req(session, 
                    url, 
                    {
                      "encodingType": "UTF8",
                      "document": {
                        "type": "PLAIN_TEXT",
                        "content": sentence
                      }
                    }, 
                    self.nlp_headers))
            nlp_list = await asyncio.gather(*req_list)
        return nlp_list

    def analyze_syntax(self, text_list):
        """
        Analyzes the syntax of text_list making asynchronous requests to nlp lib

        Returns:
            syntax_list (list): list of the syntax responses from lib
        """
        url = 'https://language.googleapis.com/v1/documents:analyzeSyntax'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        syntax_list = loop.run_until_complete(self.nlp_req(url, text_list))
        loop.close()
        return syntax_list

    def analyze_entities(self, text_list):
        """
        Analyzes the entities of the text_list making asynchronous request to nlp lib

        Returns:
            entites_list (list): list of entity responses from lib
        """
        url = 'https://language.googleapis.com/v1/documents:analyzeEntities'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        entities_list = loop.run_until_complete(self.nlp_req(url, text_list))
        loop.close()
        return entities_list
