from typing import List, Dict, Set
from collections import defaultdict, deque
from data_types.dto import LearningPath, SkillGap, LearningPhase, SkillToLearn, SkillLevel
from data.data_loader import get_skill_dependencies


def create_learning_path(
    skill_gaps: List[SkillGap],
    target_role: str,
    user_time_availability: int = 10
) -> LearningPath:
    """
    Create a structured learning path from skill gaps.
    
    Args:
        skill_gaps: List of SkillGap objects identifying skills to learn
        target_role: Name of the target role (required for LearningPath)
        user_time_availability: Hours per week the user can dedicate to learning (default: 10)
    
    Returns:
        LearningPath object with ordered phases and timeline estimates
    """
    if not skill_gaps:
        return LearningPath(
            target_role=target_role,
            total_estimated_weeks=0,
            phases=[]
        )
    
    # Step 1: Order skills by dependencies using topological sort
    ordered_skills = _order_skills_by_dependencies(skill_gaps)
    
    # Step 2: Create SkillToLearn objects with estimated hours
    skill_map = {gap.skill_name: gap for gap in skill_gaps}
    skills_to_learn = _create_skills_to_learn(ordered_skills, skill_gaps)
    
    # Step 3: Group skills into phases
    phases = _create_phases(skills_to_learn, skill_map, user_time_availability)
    
    # Step 4: Calculate total estimated weeks
    total_weeks = sum(phase.duration_weeks for phase in phases)
    
    return LearningPath(
        target_role=target_role,
        total_estimated_weeks=total_weeks,
        phases=phases
    )


def _order_skills_by_dependencies(skill_gaps: List[SkillGap]) -> List[SkillGap]:
    """
    Order skills by their dependencies using topological sort.
    Skills with dependencies come after their prerequisites.
    """
    # Create a mapping of skill name to SkillGap
    skill_map = {gap.skill_name: gap for gap in skill_gaps}
    
    # Build dependency graph
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    
    # Initialize all skills
    for gap in skill_gaps:
        in_degree[gap.skill_name] = 0
    
    # Build edges based on dependencies
    for gap in skill_gaps:
        dependencies = get_skill_dependencies(gap.skill_name)
        for dep in dependencies:
            # Only include dependencies that are in our skill_gaps list
            if dep in skill_map:
                graph[dep].append(gap.skill_name)
                in_degree[gap.skill_name] += 1
    
    # Topological sort using Kahn's algorithm
    queue = deque([skill for skill, degree in in_degree.items() if degree == 0])
    ordered = []
    
    while queue:
        skill_name = queue.popleft()
        ordered.append(skill_map[skill_name])
        
        for dependent in graph[skill_name]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # Add any remaining skills (shouldn't happen if graph is acyclic, but handle gracefully)
    remaining = [gap for gap in skill_gaps if gap not in ordered]
    ordered.extend(remaining)
    
    return ordered


def _create_skills_to_learn(
    ordered_skills: List[SkillGap],
    original_gaps: List[SkillGap]
) -> List[SkillToLearn]:
    """
    Convert SkillGap objects to SkillToLearn objects with estimated hours.
    """
    skill_map = {gap.skill_name: gap for gap in original_gaps}
    skills_to_learn = []
    
    for idx, gap in enumerate(ordered_skills, start=1):
        # Get prerequisites that are in our learning path
        dependencies = get_skill_dependencies(gap.skill_name)
        prerequisites = [dep for dep in dependencies if dep in skill_map]
        
        # Estimate hours based on gap severity and level difference
        estimated_hours = _estimate_learning_hours(gap)
        
        # Generate why_important message
        why_important = _generate_why_important(gap)
        
        skill_to_learn = SkillToLearn(
            skill_name=gap.skill_name,
            estimated_hours=estimated_hours,
            sequence=idx,
            why_important=why_important,
            prerequisites=prerequisites
        )
        skills_to_learn.append(skill_to_learn)
    
    return skills_to_learn


def _estimate_learning_hours(gap: SkillGap) -> int:
    """
    Estimate learning hours based on gap severity and level difference.
    """
    level_order = {
        SkillLevel.NONE: 0,
        SkillLevel.BEGINNER: 1,
        SkillLevel.INTERMEDIATE: 2,
        SkillLevel.ADVANCED: 3,
        SkillLevel.EXPERT: 4
    }
    
    current_order = level_order.get(gap.current_level, 0)
    required_order = level_order.get(gap.required_level, 0)
    level_diff = required_order - current_order
    
    # Base hours per level difference
    # These are rough estimates and can be adjusted
    base_hours = {
        1: 20,   # 1 level difference (e.g., none -> beginner)
        2: 50,   # 2 levels (e.g., none -> intermediate)
        3: 80,   # 3 levels (e.g., none -> advanced)
        4: 120   # 4 levels (e.g., none -> expert)
    }
    
    # Get base hours for the level difference
    hours = base_hours.get(level_diff, 40)
    
    # Adjust based on gap severity
    if gap.gap_severity == "high":
        hours = int(hours * 1.2)
    elif gap.gap_severity == "low":
        hours = int(hours * 0.8)
    
    # Adjust based on importance (critical skills may need more practice)
    if gap.importance.value == "critical":
        hours = int(hours * 1.1)
    elif gap.importance.value == "low":
        hours = int(hours * 0.9)
    
    return max(10, hours)  # Minimum 10 hours


def _generate_why_important(gap: SkillGap) -> str:
    """
    Generate a why_important message for a skill.
    """
    importance_msgs = {
        "critical": "Critical skill required for this role",
        "high": "Highly important skill for this role",
        "medium": "Important skill for this role",
        "low": "Useful skill for this role"
    }
    
    category_msgs = {
        "Frontend": "Essential for frontend development",
        "Backend": "Essential for backend development",
        "Database": "Essential for database management",
        "DevOps": "Essential for DevOps practices",
        "Cloud": "Essential for cloud deployment",
        "Mobile": "Essential for mobile development",
        "Programming Language": "Core programming language",
        "Tools": "Important development tool",
        "Soft Skills": "Important professional skill"
    }
    
    importance_msg = importance_msgs.get(gap.importance.value, "Important skill")
    category_msg = category_msgs.get(gap.category.value, "")
    
    if category_msg:
        return f"{importance_msg}. {category_msg}."
    return importance_msg


def _create_phases(
    skills_to_learn: List[SkillToLearn],
    skill_map: Dict[str, SkillGap],
    user_time_availability: int
) -> List[LearningPhase]:
    """
    Group skills into logical phases based on categories and dependencies.
    Each phase should have a reasonable duration based on user availability.
    """
    if not skills_to_learn:
        return []
    
    phases = []
    phase_number = 1
    
    # Strategy: Create phases based on logical groupings
    # Try to keep phases between 4-12 weeks for better user experience
    
    current_phase_skills = []
    current_phase_hours = 0
    current_phase_categories = set()
    phase_names = [
        "Foundation & Fundamentals",
        "Core Skills Development",
        "Advanced Concepts",
        "Specialization & Integration",
        "Mastery & Production Ready"
    ]
    
    for skill in skills_to_learn:
        # Get category for this skill
        skill_gap = skill_map.get(skill.skill_name)
        skill_category = skill_gap.category.value if skill_gap else None
        
        # Check if adding this skill would exceed reasonable phase duration
        weeks_if_added = (current_phase_hours + skill.estimated_hours) / user_time_availability
        
        # Start a new phase if:
        # 1. Current phase would exceed 12 weeks, OR
        # 2. Current phase has at least 4 weeks of content and this skill has dependencies
        #    that aren't in current phase, OR
        # 3. Current phase has at least 6 weeks and we're moving to a different major category
        has_unmet_prereqs = any(
            prereq not in [s.skill_name for s in current_phase_skills] 
            for prereq in skill.prerequisites
        )
        
        category_shift = (
            skill_category and 
            current_phase_categories and 
            skill_category not in current_phase_categories and
            len(current_phase_categories) > 0
        )
        
        should_start_new = (
            weeks_if_added > 12 or
            (current_phase_hours > 0 and 
             weeks_if_added >= 4 and
             has_unmet_prereqs) or
            (current_phase_hours > 0 and
             weeks_if_added >= 6 and
             category_shift)
        )
        
        if should_start_new and current_phase_skills:
            # Finalize current phase
            phase_duration = max(1, int((current_phase_hours / user_time_availability) + 0.5))
            phase_name = _generate_phase_name(current_phase_categories, phase_number, phase_names)
            milestone = _generate_milestone(current_phase_skills, phase_number)
            
            phases.append(LearningPhase(
                phase_number=phase_number,
                phase_name=phase_name,
                duration_weeks=phase_duration,
                skills=current_phase_skills.copy(),
                milestone=milestone
            ))
            
            phase_number += 1
            current_phase_skills = []
            current_phase_hours = 0
            current_phase_categories = set()
        
        current_phase_skills.append(skill)
        current_phase_hours += skill.estimated_hours
        if skill_category:
            current_phase_categories.add(skill_category)
    
    # Add the last phase
    if current_phase_skills:
        phase_duration = max(1, int((current_phase_hours / user_time_availability) + 0.5))
        phase_name = _generate_phase_name(current_phase_categories, phase_number, phase_names)
        milestone = _generate_milestone(current_phase_skills, phase_number)
        
        phases.append(LearningPhase(
            phase_number=phase_number,
            phase_name=phase_name,
            duration_weeks=phase_duration,
            skills=current_phase_skills,
            milestone=milestone
        ))
    
    return phases


def _generate_phase_name(categories: Set[str], phase_number: int, default_names: List[str]) -> str:
    """
    Generate a phase name based on categories or use default names.
    """
    if not categories:
        return default_names[min(phase_number - 1, len(default_names) - 1)]
    
    # Category-based phase names
    category_names = {
        "Frontend": "Frontend Development",
        "Backend": "Backend Development",
        "Database": "Database & Data Management",
        "DevOps": "DevOps & Infrastructure",
        "Cloud": "Cloud & Deployment",
        "Mobile": "Mobile Development",
        "Programming Language": "Programming Fundamentals",
        "Tools": "Development Tools",
        "Soft Skills": "Professional Skills"
    }
    
    # If single category, use specific name
    if len(categories) == 1:
        category = list(categories)[0]
        return category_names.get(category, category)
    
    # Multiple categories - use default name
    return default_names[min(phase_number - 1, len(default_names) - 1)]


def _generate_milestone(skills: List[SkillToLearn], phase_number: int) -> str:
    """
    Generate a milestone description for a phase.
    """
    if not skills:
        return "Complete phase learning objectives"
    
    skill_names = [skill.skill_name for skill in skills]
    
    if len(skill_names) == 1:
        return f"Build a project using {skill_names[0]}"
    elif len(skill_names) == 2:
        return f"Build a project combining {skill_names[0]} and {skill_names[1]}"
    else:
        primary_skill = skill_names[0]
        return f"Build a comprehensive project using {primary_skill} and related technologies"