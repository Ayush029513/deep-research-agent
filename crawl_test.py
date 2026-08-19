from app.tools.crawl import crawl_url


url = "https://en.wikipedia.org/wiki/Generative_artificial_intelligence"

text = crawl_url(url)

print("=" * 80)
print("CRAWLED CONTENT")
print("=" * 80)

print(text[:5000])

print("\n")
print("Characters:", len(text))