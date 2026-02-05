from typing import Dict, Any
import pymupdf


def load_pdf_content(state: Dict[str, Any]) -> Dict[str, Any]:
    pdf_path = state["pdf_path"]

    try:
        doc = pymupdf.open(pdf_path)
        all_text = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                all_text.append(f"\n--- Page {page_num + 1} ---\n{text}")
        doc.close()

        return {"content": "\n".join(all_text).strip()}

    except Exception as e:
        # print(f"PDF error: {e}")  
        return {"content": "", "error": str(e)}
