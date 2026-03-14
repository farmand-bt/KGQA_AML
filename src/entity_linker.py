import requests
import spacy
from src.sparql_executor import execute_sparql

SPOTLIGHT_URL = "https://api.dbpedia-spotlight.org/en/annotate"
SPOTLIGHT_CONFIDENCE = 0.35
SPOTLIGHT_CONFIDENCE_FALLBACK = 0.2

# Generic concept types — entities of these types are likely not what the user meant
GENERIC_TYPES = {
    "http://www.w3.org/2002/07/owl#Class",
    "http://dbpedia.org/ontology/TopicalConcept",
    "http://www.w3.org/2004/02/skos/core#Concept",
}

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


def _is_generic_concept(uri):
    """Check if an entity is a generic concept (like 'Architect', 'Country') rather than a specific thing."""
    query = f"""
    ASK WHERE {{
        <{uri}> a ?type .
        FILTER(?type IN (
            <http://www.w3.org/2002/07/owl#Class>,
            <http://dbpedia.org/ontology/TopicalConcept>,
            <http://www.w3.org/2004/02/skos/core#Concept>,
            <http://dbpedia.org/ontology/Profession>,
            <http://dbpedia.org/ontology/PersonFunction>
        ))
    }}
    """
    result = execute_sparql(query, timeout=10)
    if result["success"] and result["results"]:
        return result["results"][0].get("answer") == "True"
    return False


def _filter_generic_entities(entities):
    """Remove generic concept entities when specific ones are present."""
    if len(entities) <= 1:
        return entities

    filtered = []
    for e in entities:
        if _is_generic_concept(e["uri"]):
            continue
        filtered.append(e)

    # If filtering removed everything, return originals
    return filtered if filtered else entities


def link_entities(question):
    """
    Link entities in the question to DBpedia URIs.
    Cascading strategy:
      1. spaCy pipeline with default confidence (0.35)
      2. Direct API call with lower confidence (0.2)
    Then filter out generic concepts if specific entities are also present.
    """
    entities = []

    # Attempt 1: spaCy pipeline
    try:
        entities = _spotlight_via_spacy(question)
    except Exception:
        pass

    # Attempt 2: Direct API with lower confidence
    if not entities:
        try:
            entities = _spotlight_via_api(question, SPOTLIGHT_CONFIDENCE_FALLBACK)
        except Exception:
            pass

    if not entities:
        return []

    # Filter generic concepts
    return _filter_generic_entities(entities)
