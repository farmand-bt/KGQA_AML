from src.sparql_executor import execute_sparql

EXCLUDED_PREDICATES = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "http://www.w3.org/2002/07/owl#sameAs",
    "http://www.w3.org/2000/01/rdf-schema#label",
    "http://www.w3.org/2000/01/rdf-schema#comment",
    "http://dbpedia.org/ontology/abstract",
    "http://dbpedia.org/ontology/wikiPageWikiLink",
    "http://dbpedia.org/ontology/wikiPageExternalLink",
    "http://dbpedia.org/ontology/wikiPageRedirects",
    "http://dbpedia.org/ontology/wikiPageDisambiguates",
    "http://dbpedia.org/ontology/thumbnail",
    "http://dbpedia.org/ontology/wikiPageID",
    "http://dbpedia.org/ontology/wikiPageRevisionID",
    "http://dbpedia.org/ontology/wikiPageLength",
    "http://xmlns.com/foaf/0.1/isPrimaryTopicOf",
    "http://xmlns.com/foaf/0.1/depiction",
    "http://www.w3.org/ns/prov#wasDerivedFrom",
    "http://dbpedia.org/property/wikiPageUsesTemplate",
}

EXCLUDED_PREFIXES = (
    "http://dbpedia.org/ontology/wikiPage",
    "http://www.w3.org/2002/07/owl#",
    "http://www.w3.org/ns/prov#",
)


def _shorten_uri(uri):
    """Convert full URI to prefixed form for readability."""
    prefixes = {
        "http://dbpedia.org/ontology/": "dbo:",
        "http://dbpedia.org/property/": "dbp:",
        "http://dbpedia.org/resource/": "dbr:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://xmlns.com/foaf/0.1/": "foaf:",
    }
    for full, short in prefixes.items():
        if uri.startswith(full):
            return short + uri[len(full):]
    return uri


def _is_excluded(uri):
    if uri in EXCLUDED_PREDICATES:
        return True
    return any(uri.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def _fetch_relations_for_entity(uri, max_per_entity=50):
    """Fetch 1-hop predicates for a single entity. Returns list of predicate URIs."""
    relations = set()

    query_out = f"""
    SELECT DISTINCT ?p WHERE {{
        <{uri}> ?p ?o .
    }} LIMIT {max_per_entity}
    """
    result = execute_sparql(query_out)
    if result["success"]:
        for row in result["results"]:
            relations.add(row["p"])

    query_in = f"""
    SELECT DISTINCT ?p WHERE {{
        ?s ?p <{uri}> .
    }} LIMIT {max_per_entity}
    """
    result = execute_sparql(query_in)
    if result["success"]:
        for row in result["results"]:
            relations.add(row["p"])

    filtered = [r for r in relations if not _is_excluded(r)]
    filtered.sort(key=lambda r: (
        0 if "dbpedia.org/ontology" in r else
        1 if "dbpedia.org/property" in r else 2
    ))
    return filtered


def get_candidate_relations(entity_uris, max_per_entity=50):
    """
    Fetch 1-hop predicates (outgoing + incoming) for each entity.
    Returns dict mapping entity URI to its relations, plus a flat list.
    """
    per_entity = {}
    all_relations = set()

    for uri in entity_uris:
        rels = _fetch_relations_for_entity(uri, max_per_entity)
        short_name = _shorten_uri(uri)
        per_entity[short_name] = [{"uri": r, "short": _shorten_uri(r)} for r in rels]
        all_relations.update(rels)

    # Flat sorted list for backward compatibility
    flat = sorted(all_relations, key=lambda r: (
        0 if "dbpedia.org/ontology" in r else
        1 if "dbpedia.org/property" in r else 2
    ))
    flat_list = [{"uri": r, "short": _shorten_uri(r)} for r in flat]

    return {"per_entity": per_entity, "flat": flat_list}
