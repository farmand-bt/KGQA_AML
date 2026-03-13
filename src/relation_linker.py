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
}


def get_candidate_relations(entity_uris, max_per_entity=50):
    all_relations = set()

    for uri in entity_uris:
        query_out = f"""
        SELECT DISTINCT ?p WHERE {{
            <{uri}> ?p ?o .
        }} LIMIT {max_per_entity}
        """
        result = execute_sparql(query_out)
        if result["success"]:
            for row in result["results"]:
                all_relations.add(row["p"])

        query_in = f"""
        SELECT DISTINCT ?p WHERE {{
            ?s ?p <{uri}> .
        }} LIMIT {max_per_entity}
        """
        result = execute_sparql(query_in)
        if result["success"]:
            for row in result["results"]:
                all_relations.add(row["p"])

    filtered = [r for r in all_relations if r not in EXCLUDED_PREDICATES]
    filtered.sort(key=lambda r: (
        0 if "dbpedia.org/ontology" in r else
        1 if "dbpedia.org/property" in r else 2
    ))
    return filtered
