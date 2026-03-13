from src.entity_linker import link_entities
from src.relation_linker import get_candidate_relations
from src.sparql_generator import generate_sparql
from src.sparql_executor import execute_sparql
from src.answer_formatter import format_answer


def run_pipeline(question):
    result = {
        "question": question,
        "entities": [],
        "relations": [],
        "sparql": None,
        "results": None,
        "answer": None,
        "error": None,
    }

    # Step 1: Entity Linking
    entities = link_entities(question)
    result["entities"] = entities
    if not entities:
        result["error"] = "No entities found in the question."
        result["answer"] = "I could not identify any entities in your question."
        return result

    # Step 2: Relation Linking
    entity_uris = [e["uri"] for e in entities]
    relations = get_candidate_relations(entity_uris)
    result["relations"] = relations

    # Step 3: SPARQL Generation
    sparql_result = generate_sparql(question, entities, relations)
    result["sparql"] = sparql_result
    if not sparql_result["success"]:
        result["error"] = f"SPARQL generation failed: {sparql_result['error']}"
        result["answer"] = "I could not generate a query for your question."
        return result

    # Step 4: Query Execution
    exec_result = execute_sparql(sparql_result["query"])
    result["results"] = exec_result
    if not exec_result["success"]:
        result["error"] = f"Query execution failed: {exec_result['error']}"
        result["answer"] = "The generated query could not be executed."
        return result

    # Step 5: Answer Formatting
    answer = format_answer(question, exec_result["results"])
    result["answer"] = answer

    return result
