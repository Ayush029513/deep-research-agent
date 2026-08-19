import hashlib

import chromadb

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import CHROMA_DB_PATH


# =====================================================
# Configuration
# =====================================================

COLLECTION_NAME = "research_documents"

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# =====================================================
# Embeddings
# =====================================================

print(
    f"[VectorDB] Loading embedding model: "
    f"{EMBEDDING_MODEL}"
)

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)


# =====================================================
# Chroma Client
# =====================================================

client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH
)


# =====================================================
# Create / Get Vector Database
# =====================================================

def get_vector_db():

    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )


# Global database object
db = get_vector_db()


# =====================================================
# Generate Deterministic Document ID
# =====================================================

def generate_document_id(document):

    """
    Generate a stable ID from the source URL
    and document content.

    This prevents the same chunk from being
    inserted repeatedly.
    """

    source = document.metadata.get(
        "source",
        ""
    )

    content = document.page_content or ""

    raw = (
        source
        + "\n"
        + content
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()


# =====================================================
# Reset Database
# =====================================================

def reset_database():

    global db

    print(
        "\n========== RESET VECTOR DATABASE =========="
    )

    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

        print(
            "[VectorDB] Old collection deleted."
        )

    except Exception as e:

        print(
            f"[VectorDB] No existing collection "
            f"to delete: {e}"
        )

    # Recreate LangChain Chroma object
    db = get_vector_db()

    print(
        "[VectorDB] New collection ready."
    )


# =====================================================
# Store Documents
# =====================================================

def store_documents(documents):

    global db

    print(
        "\n========== STORE DOCUMENTS =========="
    )

    if not documents:

        print(
            "[VectorDB] No documents available."
        )

        return 0

    # -------------------------------------------------
    # Remove duplicate chunks within this batch
    # -------------------------------------------------

    unique_documents = []
    seen_ids = set()

    for document in documents:

        if not document.page_content:
            continue

        document_id = generate_document_id(
            document
        )

        if document_id in seen_ids:
            continue

        seen_ids.add(
            document_id
        )

        unique_documents.append(
            (
                document_id,
                document
            )
        )

    print(
        f"[VectorDB] Input chunks: "
        f"{len(documents)}"
    )

    print(
        f"[VectorDB] Unique chunks: "
        f"{len(unique_documents)}"
    )

    if not unique_documents:

        print(
            "[VectorDB] Nothing to store."
        )

        return 0

    # -------------------------------------------------
    # Check existing IDs
    # -------------------------------------------------

    ids = [
        item[0]
        for item in unique_documents
    ]

    try:

        existing = client.get_collection(
            COLLECTION_NAME
        )

        existing_data = existing.get(
            ids=ids
        )

        existing_ids = set(
            existing_data.get(
                "ids",
                []
            )
        )

    except Exception:

        existing_ids = set()

    # -------------------------------------------------
    # Remove already stored documents
    # -------------------------------------------------

    documents_to_add = []
    ids_to_add = []

    for document_id, document in unique_documents:

        if document_id in existing_ids:

            continue

        documents_to_add.append(
            document
        )

        ids_to_add.append(
            document_id
        )

    print(
        f"[VectorDB] Already stored: "
        f"{len(existing_ids)}"
    )

    print(
        f"[VectorDB] New chunks: "
        f"{len(documents_to_add)}"
    )

    if not documents_to_add:

        print(
            "[VectorDB] All chunks already exist."
        )

        return 0

    # -------------------------------------------------
    # Store documents
    # -------------------------------------------------

    try:

        db.add_documents(
            documents=documents_to_add,
            ids=ids_to_add
        )

    except Exception as e:

        print(
            f"[VectorDB] Storage error: {e}"
        )

        return 0

    print(
        f"[VectorDB] Successfully stored "
        f"{len(documents_to_add)} chunks."
    )

    return len(
        documents_to_add
    )


# =====================================================
# Search Documents
# =====================================================

def search_documents(
    query,
    k=5
):

    global db

    print(
        "\n========== VECTOR SEARCH =========="
    )

    if not query:

        print(
            "[VectorDB] Empty query."
        )

        return []

    try:

        # Retrieve more candidates first.
        # This gives us room to remove duplicate
        # sources before returning final results.

        candidate_k = max(
            k * 3,
            10
        )

        results = db.similarity_search(
            query,
            k=candidate_k
        )

        print(
            f"[VectorDB] Retrieved candidates: "
            f"{len(results)}"
        )

        # -------------------------------------------------
        # Remove duplicate chunks from same URL
        # -------------------------------------------------

        final_results = []

        seen = set()

        for document in results:

            source = document.metadata.get(
                "source",
                ""
            )

            content = (
                document.page_content
                or ""
            )

            # Prefer source + first part of content
            # as the duplicate key.
            key = (
                source,
                content[:300]
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            final_results.append(
                document
            )

            if len(final_results) >= k:
                break

        print(
            f"[VectorDB] Final results: "
            f"{len(final_results)}"
        )

        # -------------------------------------------------
        # Debug result metadata
        # -------------------------------------------------

        for i, document in enumerate(
            final_results,
            start=1
        ):

            print(
                f"\n[Result {i}]"
            )

            print(
                f"Title: "
                f"{document.metadata.get('title', '')}"
            )

            print(
                f"Source: "
                f"{document.metadata.get('source', '')}"
            )

            print(
                f"Query: "
                f"{document.metadata.get('query', '')}"
            )

            print(
                f"Preview: "
                f"{document.page_content[:200]}"
            )

        return final_results

    except Exception as e:

        print(
            f"[VectorDB] Search error: {e}"
        )

        return []


# =====================================================
# Similarity Search With Scores
# =====================================================

def search_documents_with_scores(
    query,
    k=5
):

    global db

    if not query:

        return []

    try:

        results = db.similarity_search_with_score(
            query,
            k=k
        )

        print(
            "\n========== SEARCH SCORES =========="
        )

        for i, (document, score) in enumerate(
            results,
            start=1
        ):

            print(
                f"{i}. "
                f"Score: {score:.4f}"
            )

            print(
                f"   Title: "
                f"{document.metadata.get('title', '')}"
            )

            print(
                f"   Source: "
                f"{document.metadata.get('source', '')}"
            )

        return results

    except Exception as e:

        print(
            f"[VectorDB] Scored search error: {e}"
        )

        return []


# =====================================================
# Count Documents
# =====================================================

def count_documents():

    try:

        collection = client.get_collection(
            name=COLLECTION_NAME
        )

        count = collection.count()

        return count

    except Exception as e:

        print(
            f"[VectorDB] Count error: {e}"
        )

        return 0


# =====================================================
# Get Collection Information
# =====================================================

def get_collection_info():

    try:

        collection = client.get_collection(
            name=COLLECTION_NAME
        )

        count = collection.count()

        return {
            "name": COLLECTION_NAME,
            "count": count,
            "path": CHROMA_DB_PATH,
            "embedding_model": EMBEDDING_MODEL,
        }

    except Exception as e:

        return {
            "name": COLLECTION_NAME,
            "count": 0,
            "path": CHROMA_DB_PATH,
            "embedding_model": EMBEDDING_MODEL,
            "error": str(e),
        }


# =====================================================
# Debug Vector Database
# =====================================================

def debug_database():

    print(
        "\n"
        + "=" * 70
    )

    print(
        "VECTOR DATABASE STATUS"
    )

    print(
        "=" * 70
    )

    info = get_collection_info()

    print(
        f"Collection: "
        f"{info['name']}"
    )

    print(
        f"Documents: "
        f"{info['count']}"
    )

    print(
        f"Embedding Model: "
        f"{info['embedding_model']}"
    )

    print(
        f"Database Path: "
        f"{info['path']}"
    )

    print(
        "=" * 70
    )