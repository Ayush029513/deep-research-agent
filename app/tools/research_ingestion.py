from langchain_core.documents import Document

from app.tools.crawl import crawl_url
from app.tools.text_splitter import split_text
from app.tools.vector_search import store_documents


def ingest_search_results(results, max_pages=5):

    documents = []

    for result in results[:max_pages]:

        url = result.get("url")
        title = result.get("title", "")
        source = result.get("source", "")

        if not url:
            continue

        print(f"\nCrawling: {url}")

        try:
            text = crawl_url(url)

            if not text or len(text.strip()) < 200:
                print("Skipped: insufficient content")
                continue

            chunks = split_text(text)

            print(f"Created {len(chunks)} chunks")

            for chunk in chunks:

                # Handle either string chunks or Document chunks
                if isinstance(chunk, Document):
                    content = chunk.page_content
                else:
                    content = str(chunk)

                documents.append(
                    Document(
                        page_content=content,
                        metadata={
                            "title": title,
                            "url": url,
                            "source": source,
                        },
                    )
                )

        except Exception as e:
            print(f"Failed: {e}")

    if documents:
        store_documents(documents)
        print(f"\nStored {len(documents)} chunks in vector database.")

    return documents