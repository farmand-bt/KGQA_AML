import requests
import spacy

SPOTLIGHT_URL = "https://api.dbpedia-spotlight.org/en/annotate"
SPOTLIGHT_CONFIDENCE = 0.35
SPOTLIGHT_CONFIDENCE_FALLBACK = 0.2

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.blank("en")
        _nlp.add_pipe("dbpedia_spotlight", config={
            "confidence": SPOTLIGHT_CONFIDENCE,
        })
    return _nlp


def _spotlight_via_spacy(question):
    """Primary: use spacy-dbpedia-spotlight pipeline."""
    nlp = get_nlp()
    doc = nlp(question)
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "uri": ent.kb_id_,
            "similarity": float(ent._.dbpedia_raw_result.get("@similarityScore", 0)),
        })
    return entities


def _spotlight_via_api(question, confidence):
    """Fallback: call DBpedia Spotlight REST API directly with lower confidence."""
    response = requests.get(
        SPOTLIGHT_URL,
        params={"text": question, "confidence": confidence},
        headers={"Accept": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    entities = []
    for resource in data.get("Resources", []):
        entities.append({
            "text": resource.get("@surfaceForm", ""),
            "uri": resource.get("@URI", ""),
            "similarity": float(resource.get("@similarityScore", 0)),
        })
    return entities


def link_entities(question):
    """
    Link entities in the question to DBpedia URIs.
    Cascading strategy:
      1. spaCy pipeline with default confidence (0.4)
      2. Direct API call with lower confidence (0.25)
    """
    # Attempt 1: spaCy pipeline
    try:
        entities = _spotlight_via_spacy(question)
        if entities:
            return entities
    except Exception:
        pass

    # Attempt 2: Direct API with lower confidence
    try:
        entities = _spotlight_via_api(question, SPOTLIGHT_CONFIDENCE_FALLBACK)
        if entities:
            return entities
    except Exception:
        pass

    return []
