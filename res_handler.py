# response handler
from llm_handler import LlmHandler
from dialogflow_handler import Agent
import hashlib
import json
import os
import random

class ResponseHandler:
    def __init__(self, core):
        self.handler = LlmHandler(core)
        self.agent = Agent('key.json', 'blossom-jwv9')
        self.cache_file = "cache.json"
        self.cache = self.load_cache()

    def hash_query(self, query):
        return hashlib.sha256(query.encode()).hexdigest()

    def load_cache(self):
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w') as file:
                json.dump({}, file)
            return {}
        else:
            with open(self.cache_file, 'r') as file:
                return json.load(file)

    def save_cache(self):
        with open(self.cache_file, 'w') as file:
            json.dump(self.cache, file)

    def handle(self, query):
        query_hash = self.hash_query(query)
        agent_response = self.agent.get_response(query, 5)
        response = None

        # check for timeout
        if agent_response is not None:
            if query_hash in self.cache:
                detected_intent = self.cache[query_hash]['intent']
                cached_responses = self.cache[detected_intent]
                if cached_responses:
                    return f'{random.choice(cached_responses)}'
            response = self.handler.get_response(query)

        if not response:
            if 'web.search' in self.agent.detected_intent or 'Default Fallback Intent' in self.agent.detected_intent:
                response = self.handler.get_response(query)
            else:
                response = self.agent.fulfillment_text

        # cache responses
        detected_intent = self.agent.detected_intent
        if detected_intent not in self.cache:
            self.cache[detected_intent] = []

        if response not in self.cache[detected_intent]:
            self.cache[detected_intent].append(response)

        self.cache[query_hash] = {
            'intent': detected_intent
        }
        return response
