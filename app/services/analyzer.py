from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from app.config import LLM_MODEL, LLM_TEMPERATURE

ANALYSIS_PROMPT = """
You are a web intelligence analyst specialized in extracting descriptive and actionable insights from websites to power support agents. Your goal is to deeply understand the site's structure, content, and user-facing elements to enable accurate question-answering.

Analyze the provided website content (scraped via Firecrawl) and return a STRICTLY VALID JSON object. Do NOT add extra text, explanations, or markdown. Output only the JSON.

If information cannot be inferred or is absent, use null for strings/objects or an empty list [] for arrays. Be concise yet descriptive in string fields—aim for 1-3 sentences where appropriate. Base all extractions on the content provided; do not assume external knowledge.

Schema:
{
  "website_type": "string (e.g., 'e-commerce store', 'blog', 'corporate landing page', 'SaaS dashboard', null)",
  "primary_purpose": "string (e.g., 'selling fitness apparel', 'providing tech news', 'offering online courses', null)",
  "summary": "string (a 2-4 sentence overview of the site's main content, layout, and value proposition)",
  "key_topics_or_features": ["string (bullet-point style phrases, e.g., 'User authentication via OAuth', 'Product search with filters', 'Blog on sustainable fashion')"],
  "target_audience": ["string (e.g., 'Fitness enthusiasts aged 18-35', 'Small business owners', 'Tech developers')"],
  "important_entities": ["string (key people, brands, products, or locations mentioned, e.g., 'Founder: Jane Doe', 'Product: FitTrack App', 'HQ: San Francisco')"],
  "notable_links_or_actions": ["string (user actions or internal/external links, e.g., 'Sign up button leads to /register', 'Contact form at footer', 'Link to privacy policy')"],
  "support_and_faq_info": {
    "common_questions": ["string (inferred FAQs or support topics, e.g., 'How to reset password?', 'Shipping policy details')"],
    "contact_methods": ["string (e.g., 'Email: support@example.com', 'Live chat widget', 'Phone: 1-800-123-4567')"],
    "troubleshooting_guides": ["string (any mentioned help articles or steps, e.g., 'Guide: Fixing login issues')"]
  },
  "business_model_or_intent": "string or null (e.g., 'Subscription-based SaaS', 'Affiliate marketing', 'Non-profit education')",
  "tech_or_tools_mentioned": ["string (e.g., 'Built with React', 'Integrates Stripe for payments', 'Uses Google Analytics')"],
  "potential_user_queries": ["string (5-10 example questions a support agent might handle, e.g., 'What are the pricing tiers?', 'How do I cancel my subscription?')"],
  "confidence": "number between 0 and 1 (your overall certainty in the analysis based on content completeness)"
}
"""

llm = ChatOllama(model=LLM_MODEL, temperature=LLM_TEMPERATURE)


def analyze_content(content: str) -> Dict[str, Any]:
    if not content:
        return {"llm_output": "No content to analyze."}

    messages = [
        SystemMessage(content=ANALYSIS_PROMPT),
        HumanMessage(content=f"Content to analyze:\n\n{content}"),
    ]

    response = llm.invoke(messages)
    analysis_json = response.content
    # print(analysis_json) 
    return {"llm_output": analysis_json}
