"""
tests/data_quality/test_cortex_search.py
Validation of Snowflake Cortex Search service over TECHNICAL_DOCUMENTS.
"""
import os
import pytest
import snowflake.connector
from snowflake.core import Root

@pytest.fixture(scope="module")
def sf_conn():
    token_path = os.path.expanduser('~/.snowflake/token.jwt')
    conn = snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE',
        schema='KNOWLEDGE'
    )
    yield conn
    conn.close()

def test_technical_documents_loaded(sf_conn):
    """Ensure synthetic documents exist and contain proper disclaimers."""
    cur = sf_conn.cursor()
    cur.execute("SELECT doc_id, title, content FROM AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS")
    rows = cur.fetchall()
    assert len(rows) >= 10, "At least 10 technical documents must be loaded"
    
    for doc_id, title, content in rows:
        assert "SYNTHETIC TRAINING / DEMONSTRATION MATERIAL" in content, (
            f"Document {doc_id} must include the synthetic training disclaimer"
        )

def test_cortex_search_service_active(sf_conn):
    """Ensure Cortex Search service exists and returns semantic search results."""
    root = Root(sf_conn)
    search_svc = root.databases['AERORESOLVE'].schemas['KNOWLEDGE'].cortex_search_services['AERO_TECH_MANUALS_SEARCH']
    assert search_svc is not None

    query = "connector X42 micro-fretting pin 4"
    resp = search_svc.search(
        query=query,
        columns=["doc_id", "title", "ata_chapter"],
        limit=3
    )
    assert len(resp.results) > 0, "Cortex Search should return relevant documents"
    
    returned_doc_ids = [r["doc_id"] for r in resp.results]
    # WIG or TSM or EAD should be in top results
    assert any(doc_id in ["DOC-WIG-24-3804", "DOC-TSM-21-2601", "DOC-EAD-2026-2109"] for doc_id in returned_doc_ids), (
        f"Expected top results to include ATA 21/24 micro-fretting documents, got {returned_doc_ids}"
    )
