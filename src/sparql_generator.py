import re
from src.llm_client import chat_completion

MAX_CANDIDATE_RELATIONS = 30

SYSTEM_PROMPT = """You are a SPARQL query generator for the DBpedia knowledge graph.

You receive:
- A natural language question
- Linked DBpedia entity URIs (from entity linking)
- Candidate relation URIs from the 1-hop neighborhood of those entities

Your task: write a SPARQL SELECT or ASK query that answers the question.

## Prefixes you may use
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

## Rules
1. Use the provided entity URIs directly (do not guess different URIs).
2. Prefer candidate relations from the provided list — they are real predicates that exist for these entities.
3. Prefer dbo: predicates over dbp: when both seem applicable.
4. For list questions, use SELECT DISTINCT and LIMIT 20.
5. For yes/no questions, use ASK WHERE.
6. For "how many" questions, use SELECT (COUNT(DISTINCT ...) AS ?count).
7. For superlative questions (biggest, oldest, etc.), use ORDER BY and LIMIT 1.
8. When retrieving names/labels, add: ?x rdfs:label ?label . FILTER(lang(?label) = "en")
9. Return ONLY the SPARQL query. No explanation, no markdown fences.

## Examples

Question: What is the capital of Germany?
Entities: dbr:Germany
Relations: dbo:capital, dbo:leader, ...
Query:
SELECT ?capital WHERE {
  dbr:Germany dbo:capital ?capital .
} LIMIT 20

Question: Who wrote Romeo and Juliet?
Entities: dbr:Romeo_and_Juliet
Relations: dbo:author, dbo:literaryGenre, ...
Query:
SELECT ?author WHERE {
  dbr:Romeo_and_Juliet dbo:author ?author .
} LIMIT 20

Question: How many people live in Tokyo?
Entities: dbr:Tokyo
Relations: dbo:populationTotal, dbo:area, ...
Query:
SELECT ?population WHERE {
  dbr:Tokyo dbo:populationTotal ?population .
} LIMIT 20

Question: Is Berlin the capital of Germany?
Entities: dbr:Berlin, dbr:Germany
Relations: dbo:capital, ...
Query:
ASK WHERE {
  dbr:Germany dbo:capital dbr:Berlin .
}

Question: Which countries have more than 100 million people?
Entities: (none specific)
Relations: dbo:populationTotal, rdf:type, ...
Query:
SELECT DISTINCT ?country WHERE {
  ?country rdf:type dbo:Country .
  ?country dbo:populationTotal ?pop .
  FILTER(?pop > 100000000)
} LIMIT 20"""


def generate_sparql(question, entities, candidate_relations, error_feedback=None):
    """
    Use LLM to generate a SPARQL query.
    If error_feedback is provided, include it so the LLM can self-correct.
    """
    entity_lines = "\n".join(
        f"- {e['text']}: <{e['uri']}>" for e in entities
    )
    relation_lines = "\n".join(
        f"- {r['short']} ({r['uri']})" for r in candidate_relations[:MAX_CANDIDATE_RELATIONS]
    )

    user_msg = f"Question: {question}\n\nLinked Entities:\n{entity_lines}\n\nCandidate Relations:\n{relation_lines}"

    if error_feedback:
        user_msg += f"\n\nPrevious attempt failed with: {error_feedback}\nPlease try a different approach. Consider using alternative predicates from the candidate list, or try dbp: instead of dbo: (or vice versa)."

    user_msg += "\n\nWrite the SPARQL query:"

    try:
        response = chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ])
        query = extract_sparql(response)
        return {"success": True, "query": query}
    except Exception as e:
        return {"success": False, "query": None, "error": str(e)}


def extract_sparql(text):
    """Extract SPARQL query from LLM response, handling markdown fences."""
    match = re.search(r"```(?:sparql)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
