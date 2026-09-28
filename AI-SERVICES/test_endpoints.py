"""
Test newly created document and RAG diagnostic endpoints.
"""

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_endpoints():
    print("Testing /api/debug/rag/overview...")
    res = client.get("/api/debug/rag/overview")
    print(f"Status: {res.status_code}, Points: {res.json().get('total_indexed_points')}")
    assert res.status_code == 200

    doc_id = "6ab56d1c6b9454f4c23f88ef"
    print(f"\nTesting /api/debug/rag/document/{doc_id}...")
    res = client.get(f"/api/debug/rag/document/{doc_id}")
    debug_data = res.json()
    print(f"Status: {res.status_code}, Chunks in Qdrant: {debug_data.get('document_chunks_in_qdrant')}")
    assert res.status_code == 200
    assert debug_data.get("status") == "ok"
    assert debug_data.get("dimension_matches") is True

    print(f"\nTesting /api/documents/{doc_id}/chunks...")
    res = client.get(f"/api/documents/{doc_id}/chunks")
    chunks_data = res.json()
    print(f"Status: {res.status_code}, Chunks count: {chunks_data.get('chunks_count')}")
    assert res.status_code == 200
    assert chunks_data.get("chunks_count") > 0
    assert len(chunks_data.get("chunks")) > 0

    print(f"\nTesting /api/documents/{doc_id}/content...")
    res = client.get(f"/api/documents/{doc_id}/content")
    content_data = res.json()
    print(f"Status: {res.status_code}, Length: {content_data.get('content_length')}")
    assert res.status_code == 200
    assert content_data.get("content_length") > 0

    print("\nTesting POST /api/documents/retrieve...")
    res = client.post("/api/documents/retrieve", json={"query": "pressure P-102", "top_k": 3})
    ret_data = res.json()
    print(f"Status: {res.status_code}, Results returned: {ret_data.get('count')}")
    assert res.status_code == 200
    assert ret_data.get("count") > 0

    print("\n" + "=" * 60)
    print("ALL 5 NEW ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()
