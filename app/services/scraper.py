from typing import Dict, Any
from firecrawl import Firecrawl
from app.config import FIRECRAWL_API_KEY

firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)


def scrape_content(state: Dict[str, Any]) -> Dict[str, Any]:
    url = state["input_url"]

    try:
        docs = firecrawl.crawl(url, limit=5)
        scraped_text = ""

        for document in docs.data:
            if document.markdown:
                scraped_text += document.markdown + "\n\n"
            elif document.raw_html:
                scraped_text += document.raw_html + "\n\n"
        return {"content": scraped_text.strip()}

    except Exception as e:
        # print(f"Scrape error: {e}")
        return {"content": "", "error": str(e)}
