import spacy

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.blank("en")
        _nlp.add_pipe("dbpedia_spotlight")
    return _nlp


def link_entities(question):
    try:
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
    except Exception:
        return []
