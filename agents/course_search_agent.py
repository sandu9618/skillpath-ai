"""
Course search agent: discovers courses via Google Search (ADK), optionally
fetches candidate pages, then ranks them with ``rank_courses``.
"""

from google.adk import Agent
from google.adk.tools.google_search_tool import GoogleSearchTool

from tools.tool_rank_courses import rank_courses
from tools.tool_web_fetch import web_fetch

# Use bypass so this built-in can coexist with ``web_fetch`` and ``rank_courses``.
web_search = GoogleSearchTool(bypass_multi_tools_limit=True)

_COURSE_SEARCH_INSTRUCTION = """
You are a course discovery specialist for software engineering learners.

Workflow:
1. For each skill (and its target level, e.g. beginner | intermediate | advanced), run
   focused **web search** queries. Prefer patterns like:
   - ``learn {skill} online course {level}``
   - ``best {skill} course site:udemy.com OR site:coursera.org``
2. From search results, build a list of **course candidate dicts** with keys such as:
   title, url, snippet/description, provider (if known), rating, level, estimated_hours, price.
3. Optionally call **web_fetch** on 1–3 promising URLs to enrich description or hours
   (respect rate limits; skip paywalls or blocked pages).
4. Call **rank_courses** with:
   - ``courses``: your candidate list (dicts)
   - ``skill``: the skill name
   - ``target_level``: the learner level string (lowercase enum style)
5. Present **3–5** top courses per skill: title, provider, URL, level, price, rating,
   estimated hours when available. Mix **free** and **paid** when possible.

Rules:
- Prefer reputable platforms (Udemy, Coursera, edX, freeCodeCamp, YouTube, official docs).
- Do not fabricate URLs or ratings; only use what search / fetch provides, then ranking.
- If search returns little, say so and suggest broader queries or official documentation.
""".strip()


course_search_agent = Agent(
    name="course_search_agent",
    model="gemini-2.0-flash",
    description="Finds and ranks online courses per skill using web search, fetch, and rank_courses.",
    instruction=_COURSE_SEARCH_INSTRUCTION,
    tools=[web_search, web_fetch, rank_courses],
)
