import nltk
import re, os, sys
import pandas as pd
from collections import defaultdict
# import camelot
import difflib as dl
import numpy as np
import spacy 
import openai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cur_model = os.path.join(BASE_DIR, 'static', 'ners', 'ner_model')
spacy.prefer_gpu()
nlp = spacy.load(cur_model)

openai.organization = ""
openai.api_key = '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'

def AE_annotation_chatGPT(prompt, message, n=1, temperature=0.1):
    if not prompt: return
    
    response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"system", "content": prompt},
                          {"role":"user", "content": message},],
                max_tokens=1024,
                n=n,
                stop=None,
                temperature=temperature,
            )
            
    return response