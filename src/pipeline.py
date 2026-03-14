import time
from src.entity_linker import link_entities
from src.relation_linker import get_candidate_relations
from src.sparql_generator import generate_sparql
from src.sparql_executor import execute_sparql
from src.answer_formatter import format_answer

MAX_SPARQL_RETRIES = 2


def run_pipeline(question):
    start_time = time.time()

    result = {
        "question": question,
        "entities": [],
        "relations": {},
        "sparql": None,
        "results": None,
        "answer": None,
        "error": None,
        "attempts": 0,
        "time_s": 0,
    }

    # Step 1: Entity Linking
    entities = link_entities(question)
    result["entities"] = entities
    if not entities:
        result["error"] = "No entities found in the question."
        result["answer"] = "I could not identify any entities in your question."
        result["time_s"] = round(time.time() - start_time, 2)
        return result

    # Step 2: Relation Linking
    entity_uris = [e["uri"] for e in entities]
    relations = get_candidate_relations(entity_uris)
    result["relations"] = relations

    # Step 3 & 4: SPARQL Generation + Execution (with retry)
    error_feedback = None
    for attempt in range(1 + MAX_SPARQL_RETRIES):
        result["attempts"] = attempt + 1

        sparql_result = generate_sparql(question, entities, relations, error_feedback)
        result["sparql"] = sparql_result
        if not sparql_result["success"]:
            error_feedback = sparql_result.get("error", "Generation failed")
            continue

        exec_result = execute_sparql(sparql_result["query"])
        result["results"] = exec_result

        if not exec_result["success"]:
            error_feedback = f"Query execution error: {exec_result['error']}"
            continue

        # Check for empty results (likely wrong query)
        if not exec_result["results"]:
            error_feedback = (
                f"The query returned 0 results:\n{sparql_result['query']}\n"
                "This predicate does not work. Try DIFFERENT predicates from the candidate list. "
                "If you used dbo: predicates, try dbp: ones instead (e.g., dbp:incumbent, dbp:leader)."
            )
            continue

        # Success — break out of retry loop
        error_feedback = None
        break

    # If all attempts failed
    if error_feedback:
        result["error"] = f"Failed after {result['attempts']} attempt(s): {error_feedback}"
        if not result["answer"]:
            result["answer"] = "I could not find an answer to your question after multiple attempts."
        result["time_s"] = round(time.time() - start_time, 2)
        return result

    # Step 5: Answer Formatting
    answer = format_answer(question, exec_result["results"], sparql_result.get("query"))
    result["answer"] = answer
    result["time_s"] = round(time.time() - start_time, 2)

    return result
