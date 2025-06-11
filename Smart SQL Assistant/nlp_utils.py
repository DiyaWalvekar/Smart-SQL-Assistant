import nltk

# Download WordNet only if not already downloaded
try:
    from nltk.corpus import wordnet
    wordnet.synsets('test')  # Try accessing to confirm it's available
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load embedding model once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Intent templates
intent_templates = {
    "select": ["show all records", "fetch data", "get values", "display table"],
    "insert": ["add new record", "insert entry", "create row"],
    "update": ["modify value", "update data", "change record"],
    "delete": ["remove row", "delete entry", "drop record"]
}


def match_intent(user_query):
    """
    Match user query to predefined intent using embeddings.
    """
    user_vec = model.encode([user_query])
    best_intent = None
    best_score = 0.0

    for intent, phrases in intent_templates.items():
        intent_vecs = model.encode(phrases)
        scores = cosine_similarity(user_vec, intent_vecs)
        score = float(np.max(scores))  # Ensure it's JSON-serializable
        if score > best_score:
            best_score = score
            best_intent = intent

    return best_intent, best_score


def expand_query(query):
    """
    Expand words with up to 2 synonyms using WordNet.
    If unavailable, returns the original word.
    """
    expanded = []
    for word in query.split():
        try:
            syns = wordnet.synsets(word)
            lemmas = {lemma.name().replace('_', ' ') for syn in syns for lemma in syn.lemmas()}
            expanded.append(list(lemmas)[:2] or [word])
        except Exception as e:
            # Handle any unexpected issues
            expanded.append([word])
    return expanded
