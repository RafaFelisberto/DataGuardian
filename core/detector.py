import re
import spacy
import json

class SensitiveDataDetector:
    def __init__(self):
        self.patterns = self._load_patterns()
        self.nlp = spacy.load("pt_core_news_sm")
    
    def _load_patterns(self):
        with open('models/pi_patterns.json') as f:
            return json.load(f)
    
    def detect_regex(self, text):
        """Detecta padrões usando regex"""
        matches = {}
        for name, pattern in self.patterns.items():
            if re.search(pattern, text):
                matches[name] = re.findall(pattern, text)
        return matches
    
    def detect_ner(self, text):
        """Detecção com NLP SpaCy"""
        doc = self.nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents 
               if ent.label_ in ['PERSON', 'PHONE', 'EMAIL']]