from typing import Dict, List
from data_types.dto import SkillGapAnalysis, SkillRequirement, SkillGap, SkillLevel
from data.data_loader import compare_skill_levels


def calculate_skill_gaps(
    current_skills: Dict[str, str],
    required_skills: List[SkillRequirement],
    target_role: str
) -> SkillGapAnalysis:
    """
    Compare current skills with required skills and identify gaps.
    
    Args:
        current_skills: Dictionary mapping skill names to current skill levels (e.g., {"Python": "intermediate"})
        required_skills: List of SkillRequirement objects for the target role
        target_role: Name of the target role (required for SkillGapAnalysis)
    
    Returns:
        SkillGapAnalysis object containing identified gaps, existing skills, and prioritization
    """
    skill_gaps: List[SkillGap] = []
    existing_skills: List[str] = []
    
    # Normalize current_skills keys to lowercase for case-insensitive matching
    current_skills_normalized = {
        skill_name.lower(): level.lower() 
        for skill_name, level in current_skills.items()
    }
    
    # Process each required skill
    for req_skill in required_skills:
        skill_name = req_skill.skill_name
        skill_name_lower = skill_name.lower()
        required_level = req_skill.required_level
        
        # Get current level (default to NONE if skill not found)
        current_level_str = current_skills_normalized.get(skill_name_lower, "none")
        
        # Convert string to SkillLevel enum
        try:
            current_level = SkillLevel(current_level_str)
        except ValueError:
            # If invalid level string, default to NONE
            current_level = SkillLevel.NONE
        
        # Compare levels to determine if there's a gap
        level_comparison = compare_skill_levels(current_level.value, required_level.value)
        
        # If current level is less than required level, there's a gap
        if level_comparison < 0:
            # Calculate gap severity based on level difference
            gap_severity = _calculate_gap_severity(current_level, required_level)
            
            # Calculate priority based on importance and gap severity
            priority = _calculate_priority(req_skill.importance.value, gap_severity)
            
            gap = SkillGap(
                skill_name=skill_name,
                current_level=current_level,
                required_level=required_level,
                category=req_skill.category,
                priority=priority,
                importance=req_skill.importance,
                gap_severity=gap_severity
            )
            skill_gaps.append(gap)
        else:
            # Skill meets or exceeds requirement - add to existing skills
            existing_skills.append(skill_name)
    
    # Sort gaps by priority (lower number = higher priority)
    skill_gaps.sort(key=lambda gap: gap.priority)
    
    return SkillGapAnalysis(
        target_role=target_role,
        skill_gaps=skill_gaps,
        existing_skills=existing_skills,
        total_gaps=len(skill_gaps)
    )


def _calculate_gap_severity(current_level: SkillLevel, required_level: SkillLevel) -> str:
    """
    Calculate gap severity based on the difference between current and required levels.
    
    Args:
        current_level: Current skill level
        required_level: Required skill level
    
    Returns:
        "high", "medium", or "low" severity
    """
    level_order = {
        SkillLevel.NONE: 0,
        SkillLevel.BEGINNER: 1,
        SkillLevel.INTERMEDIATE: 2,
        SkillLevel.ADVANCED: 3,
        SkillLevel.EXPERT: 4
    }
    
    current_order = level_order.get(current_level, 0)
    required_order = level_order.get(required_level, 0)
    gap_size = required_order - current_order
    
    if gap_size >= 3:
        return "high"
    elif gap_size == 2:
        return "medium"
    else:
        return "low"


def _calculate_priority(importance: str, gap_severity: str) -> int:
    """
    Calculate priority score for a skill gap.
    Lower number = higher priority.
    
    Priority is based on:
    1. Importance (critical > high > medium > low)
    2. Gap severity (high > medium > low)
    
    Args:
        importance: Skill importance ("critical", "high", "medium", "low")
        gap_severity: Gap severity ("high", "medium", "low")
    
    Returns:
        Priority score (lower = higher priority)
    """
    importance_weights = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4
    }
    
    severity_weights = {
        "high": 1,
        "medium": 2,
        "low": 3
    }
    
    # Combine weights (importance is weighted more heavily)
    priority = (importance_weights.get(importance, 4) * 10) + severity_weights.get(gap_severity, 3)
    
    return priority