import re
from src.llm_client import chat_completion

MAX_CANDIDATE_RELATIONS = 30

SYSTEM_PROMPT = """You are a SPARQL query generator for the DBpedia knowledge graph.

You receive:
- A natural language question
- Linked DBpedia entity URIs (from entity linking)
- Candidate relation URIs grouped by entity (these are REAL predicates that exist in DBpedia for each entity)

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
1. Use the provided entity URIs directly (do not invent URIs).
2. ONLY use predicates from the candidate relations list — they are verified to exist. Do NOT guess predicates.
3. Pay attention to which predicates belong to which entity. Use the predicate on the correct entity.
4. Prefer dbo: predicates over dbp: when both seem applicable.
5. For list questions, use SELECT DISTINCT and LIMIT 20.
6. For yes/no questions, use ASK WHERE.
7. For "how many" questions, use SELECT (COUNT(DISTINCT ...) AS ?count).
8. For superlative questions (biggest, oldest, etc.), use ORDER BY and LIMIT 1.
9. When retrieving names/labels, add: ?x rdfs:label ?label . FILTER(lang(?label) = "en")
10. Return ONLY the SPARQL query. No explanation, no markdown fences.

## Multi-hop questions
For questions like "When was the architect of X born?", chain the relationships:
  X --predicate1--> ?intermediate --predicate2--> ?answer

## Examples

Question: What is the capital of Germany?
Entities: dbr:Germany
Relations for dbr:Germany: dbo:capital, dbo:leader, dbo:populationTotal, ...
Query:
SELECT ?capital WHERE {
  dbr:Germany dbo:capital ?capital .
} LIMIT 20

Question: Who wrote Romeo and Juliet?
Entities: dbr:Romeo_and_Juliet
Relations for dbr:Romeo_and_Juliet: dbo:author, dbo:literaryGenre, ...
Query:
SELECT ?author WHERE {
  dbr:Romeo_and_Juliet dbo:author ?author .
} LIMIT 20

Question: Is Berlin the capital of Germany?
Entities: dbr:Berlin, dbr:Germany
Relations for dbr:Germany: dbo:capital, ...
Query:
ASK WHERE {
  dbr:Germany dbo:capital dbr:Berlin .
}

Question: When was the architect of the Eiffel Tower born?
Entities: dbr:Eiffel_Tower
Relations for dbr:Eiffel_Tower: dbo:architect, dbo:location, dbp:openingDate, ...
Query:
SELECT ?birthDate WHERE {
  dbr:Eiffel_Tower dbo:architect ?architect .
  ?architect dbo:birthDate ?birthDate .
} LIMIT 20

Question: Which movies were directed by the spouse of Will Smith?
Entities: dbr:Will_Smith
Relations for dbr:Will_Smith: dbo:spouse, dbo:birthDate, dbo:occupation, ...
Query:
SELECT ?movie WHERE {
  dbr:Will_Smith dbo:spouse ?spouse .
  ?movie dbo:director ?spouse .
} LIMIT 20

Question: Who is the current leader of a country or organization?
Entities: dbr:Some_Entity
Relations for dbr:Some_Entity: dbp:incumbent, dbp:leader, dbo:leader, ...
Query:
SELECT ?leader WHERE {
  dbr:Some_Entity dbp:incumbent ?leader .
} LIMIT 20"""


def generate_sparql(question, entities, candidate_relations, error_feedback=None):
    """
    Use LLM to generate a SPARQL query.
    candidate_relations has {"per_entity": {entity: [rels]}, "flat": [rels]}
    """
    entity_lines = "\n".join(
        f"- {e['text']}: <{e['uri']}>" for e in entities
    )

    # Show relations grouped by entity
    per_entity = candidate_relations.get("per_entity", {})
    relation_sections = []
    for entity_short, rels in per_entity.items():
        rel_names = [r["short"] for r in rels[:MAX_CANDIDATE_RELATIONS]]
        relation_sections.append(f"Relations for {entity_short}: {', '.join(rel_names)}")
    relation_text = "\n".join(relation_sections)

    user_msg = f"Question: {question}\n\nLinked Entities:\n{entity_lines}\n\n{relation_text}"

    if error_feedback:
        user_msg += f"\n\nPrevious attempt failed: {error_feedback}\nTry a different approach. Look carefully at the candidate relations list and pick different predicates. If dbo: didn't work, try dbp: (or vice versa). For multi-hop questions, chain relationships through intermediate variables."

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
