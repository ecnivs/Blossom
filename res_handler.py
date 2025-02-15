# Response Handler
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from llm_handler import LlmHandler
from settings import *
import hashlib
import random

class ResponseHandler:
    def __init__(self, core):
        self.core = core
        self.llm = LlmHandler()
        self.cache = self.load_cache()
        self.stemmer = PorterStemmer()

    @staticmethod
    def hash_query(query):
        return hashlib.sha256(query.encode()).hexdigest()

    @staticmethod
    def load_cache():
        if not os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'w') as file:
                json.dump({}, file)
            return {}

        with open(CACHE_FILE, 'r') as file:
            return json.load(file)

    def save_cache(self):
        with open(CACHE_FILE, 'w') as file:
            json.dump(self.cache, file)

    def extract_key_phrases(self, query):
        stop_words = set(stopwords.words('english'))
        words = re.sub(r'[^a-zA-Z\s]', '', query.lower()).split()
        word_counts = Counter([self.stemmer.stem(word) for word in words if word not in stop_words])
        result = list(word_counts.keys())
        if not result:
            return query.split()
        if result and result[0] in EXCLUDED_PREFIXES:
            result.pop(0)
        return result

    def add_response(self, query, query_hash, intent):
        response = "".join(self.llm.get_response(query))
        if response not in self.cache[intent]:
            self.cache[intent].append(response)
        self.cache[query_hash] = {
            'intent': intent
        }

    def handle(self, query, nocache = False):
        query_hash = self.hash_query(query.lower())

        if query_hash in self.cache and not nocache:
            detected_intent = self.cache[query_hash]['intent']
            cached_responses = self.cache[detected_intent]
            if len(cached_responses) > 2:
                threading.Thread(target=self.add_response, args=(query, query_hash, detected_intent)).start()
                sentences = re.split(r'(?<=[.!?])\s+', f'{random.choice(cached_responses)}')
                for sentence in sentences:
                    self.core.speech_queue.put(sentence)
                return

        response = []
        for chunk in self.llm.get_response(query):
            if chunk.strip():
                self.core.speech_queue.put(chunk)
                response.append(chunk)

        response = ' '.join(response)
        intent_name = '.'.join(self.extract_key_phrases(query))

        if 'repeat' not in intent_name:
            if intent_name not in self.cache:
                self.cache[intent_name] = []
            if response not in self.cache[intent_name]:
                self.cache[intent_name].append(response)
            self.cache[query_hash] = {
                'intent': intent_name
            }
