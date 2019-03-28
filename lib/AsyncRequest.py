from google.oauth2 import service_account
from google.auth.transport import requests

import aiohttp
import asyncio
import os

class AsyncRequest:
    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/cloud-language']

        self.credentials = service_account.Credentials.from_service_account_file(os.environ['GOOGLE_APPLICATION_CREDENTIALS'], scopes=SCOPES)
        self.credentials.refresh(requests.Request())

        self.nlp_headers = {
            "content-type": "application/json",
            "Authorization": "Bearer " + self.credentials.token
        }

    async def post_req(self, session,url, payload, headers):
        async with session.post(url, json=payload, headers=headers) as resp:
            json_resp = await resp.json()
            return json_resp

    async def nlp_req(self, url, text_list):
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
        url = 'https://language.googleapis.com/v1/documents:analyzeSyntax'
        syntax_list = asyncio.run(self.nlp_req(url, text_list))
        return syntax_list

    def analyze_entities(self, text_list):
        url = 'https://language.googleapis.com/v1/documents:analyzeEntities'
        entities_list = asyncio.run(self.nlp_req(url, text_list))
        return entities_list
