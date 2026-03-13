# KGQA_AML — Knowledge Graph Question Answering System

A hybrid pipeline that answers natural language questions using the [DBpedia](https://www.dbpedia.org/) Knowledge Graph. Built as a course project for **Advanced Machine Learning** (WS 2025/26) at the Leuphana University of Lüneburg.

**Author:** Farmand Bazdiditehrani

**Instructors:** Debayan Banerjee (Postdoc), Kai Moltzen (PhD student)

## Architecture

```
User Question (Natural Language)
        │
        ▼
┌─────────────────────┐
│  1. Question Analysis│  ← spaCy NLP preprocessing
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  2. Entity Linking   │  ← DBpedia Spotlight (spacy-dbpedia-spotlight)
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  3. Relation Linking │  ← Filter to 1-hop neighborhood, rank candidates
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  4. SPARQL Generation│  ← LLM (GWDG SAIA API) assembles query
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  5. Query Execution  │  ← SPARQLWrapper → DBpedia SPARQL endpoint
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  6. Answer Formatting│  ← LLM formats results into readable answer
└────────┬────────────┘
         ▼
    Streamlit Web UI
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Web UI | Streamlit |
| NLP | spaCy |
| Entity Linking | spacy-dbpedia-spotlight |
| SPARQL Queries | SPARQLWrapper |
| LLM API | GWDG SAIA (OpenAI-compatible) |
| HTTP | requests |

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/KGQA_AML.git
   cd KGQA_AML
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Linux / macOS
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GWDG SAIA API key
   ```

## Usage

```bash
streamlit run app.py
```

> **Note:** The application is currently under development.

## Project Structure

```
KGQA_AML/
├── app.py                  # Streamlit web interface (entry point)
├── src/
│   ├── __init__.py
│   ├── pipeline.py         # Main KGQA pipeline orchestrator
│   ├── entity_linker.py    # DBpedia Spotlight entity linking
│   ├── relation_linker.py  # Relation linking (1-hop filtering + ranking)
│   ├── sparql_generator.py # LLM-based SPARQL query generation
│   ├── sparql_executor.py  # Execute SPARQL against DBpedia
│   ├── answer_formatter.py # Format raw results into NL answers
│   └── llm_client.py       # GWDG SAIA API client wrapper
├── data/
│   ├── lcquad_filtered.json # Filtered LC-QuAD questions
│   └── questions.txt        # Working and non-working questions list
├── .env.example             # Template for API keys
├── requirements.txt
├── AUTHORS
├── LICENSE
└── README.md
```

## Dataset

This project uses the [LC-QuAD](https://github.com/AskNowQA/LC-QuAD) dataset for evaluation. Since not all LC-QuAD questions work against the live DBpedia SPARQL endpoint, the dataset is filtered to retain only questions that return valid results.

## Links

- [DBpedia SPARQL Endpoint](https://dbpedia.org/sparql)
- [DBpedia Spotlight API](https://api.dbpedia-spotlight.org/en/annotate)
- [GWDG SAIA Documentation](https://docs.hpc.gwdg.de/services/saia/index.html)
- [LC-QuAD Dataset](https://github.com/AskNowQA/LC-QuAD)

## License

See [LICENSE](LICENSE) for details.
