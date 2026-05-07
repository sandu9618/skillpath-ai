"""
Skill gap analysis agent: extracts the user's skills and target role, then calls
catalog tools to produce a prioritized ``SkillGapAnalysis``.
"""

from google.adk import Agent

from tools.tool_calculate_skill_gaps import calculate_skill_gaps
from tools.tool_get_role_requirements import get_role_requirements

_SKILL_GAP_INSTRUCTION = """
You are a career assessment specialist for software engineers.

Goals:
1. Read the user's message and infer **current_skills**: a map of skill name -> level.
2. Infer **target_role**: the job title or track they want (e.g. "Full Stack Developer").
3. Call **get_role_requirements** with the exact catalog role name. If the user uses a
   close synonym, normalize to the closest exact title before calling. If unsure,
   ask one short clarifying question listing likely options from context.
4. Call **calculate_skill_gaps** with:
   - **current_skills**: dict[str, str] using lowercase level strings:
     none | beginner | intermediate | advanced | expert
   - **required_skills**: the `required_skills` list from the `RoleRequirements` returned above
   - **target_role**: the same string you used for get_role_requirements
5. Summarize the result for the user: target role, count of gaps, top critical gaps,
   and skills already satisfied. Use clear markdown bullets. Include the structured
   gap list when helpful.

Rules:
- Never invent required skills; always use **get_role_requirements** first.
- Skill levels in **current_skills** must be one of: none, beginner, intermediate, advanced, expert.
- If **get_role_requirements** raises "Role not found", retry with another exact title or ask the user.
""".strip()


skill_gap_analysis_agent = Agent(
    name="skill_gap_analysis_agent",
    model="gemini-2.0-flash",
    description="Extracts current skills and target role, loads role requirements, and computes skill gaps.",
    instruction=_SKILL_GAP_INSTRUCTION,
    tools=[get_role_requirements, calculate_skill_gaps],
)

# Alias matching the plan snippet naming
skill_gap_agent = skill_gap_analysis_agent
