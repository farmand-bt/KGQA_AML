from SPARQLWrapper import SPARQLWrapper, JSON

DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"


def execute_sparql(query, timeout=30):
    try:
        sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(timeout)
        response = sparql.query().convert()

        # Handle ASK queries (return boolean)
        if "boolean" in response:
            return {"success": True, "results": [{"answer": str(response["boolean"])}]}

        bindings = response.get("results", {}).get("bindings", [])
        results = []
        for row in bindings:
            results.append({var: row[var]["value"] for var in row})
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}
