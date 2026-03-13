import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="KGQA - DBpedia Question Answering", page_icon="🔍")
st.title("Knowledge Graph Question Answering")
st.markdown("Ask a question and get an answer from [DBpedia](https://www.dbpedia.org/).")

# Check API key
api_key_set = bool(os.getenv("GWDG_API_KEY"))
if not api_key_set:
    st.warning("GWDG API key not configured. Set GWDG_API_KEY in your .env file.")

# Input
question = st.text_input("Your question:", placeholder="Who is the president of France?")
ask = st.button("Ask", disabled=not api_key_set or not question)

if ask and question:
    from src.pipeline import run_pipeline

    with st.spinner("Processing your question..."):
        result = run_pipeline(question)

    # Answer
    if result["answer"]:
        st.subheader("Answer")
        st.write(result["answer"])

    if result["error"]:
        st.error(result["error"])

    # Debug details
    with st.expander("Show details"):
        st.markdown("**Linked Entities:**")
        if result["entities"]:
            for e in result["entities"]:
                st.markdown(
                    f"- `{e['text']}` → [{e['uri']}]({e['uri']}) "
                    f"(score: {e['similarity']:.2f})"
                )
        else:
            st.write("None found.")

        st.markdown(f"**Candidate Relations:** {len(result['relations'])} found")
        if result["relations"]:
            st.code("\n".join(result["relations"][:15]), language=None)

        if result["sparql"] and result["sparql"].get("query"):
            st.markdown("**Generated SPARQL:**")
            st.code(result["sparql"]["query"], language="sparql")

        if result["results"] and result["results"].get("results"):
            st.markdown(f"**Raw Results:** ({len(result['results']['results'])} rows)")
            st.json(result["results"]["results"][:10])
