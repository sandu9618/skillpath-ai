from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

# Enums
class SkillLevel(str, Enum):
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SkillCategory(str, Enum):
    FRONTEND = "Frontend"
    BACKEND = "Backend"
    DATABASE = "Database"
    DEVOPS = "DevOps"
    CLOUD = "Cloud"
    MOBILE = "Mobile"
    PROGRAMMING_LANGUAGE = "Programming Language"
    TOOLS = "Tools"
    SOFT_SKILLS = "Soft Skills"

class SkillImportance(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Skill Gap Models
class SkillRequirement(BaseModel):
    skill_name: str
    category: SkillCategory
    required_level: SkillLevel
    importance: SkillImportance
    description: Optional[str] = None

class RoleRequirements(BaseModel):
    role_name: str
    experience_level: str
    required_skills: List[SkillRequirement]
    
class SkillGap(BaseModel):
    skill_name: str
    current_level: SkillLevel
    required_level: SkillLevel
    category: SkillCategory
    priority: int
    importance: SkillImportance
    gap_severity: str  # "high", "medium", "low"

class SkillGapAnalysis(BaseModel):
    target_role: str
    skill_gaps: List[SkillGap]
    existing_skills: List[str]
    total_gaps: int

# Learning Path Models
class SkillToLearn(BaseModel):
    skill_name: str
    estimated_hours: int
    sequence: int
    why_important: str
    prerequisites: List[str] = []

class LearningPhase(BaseModel):
    phase_number: int
    phase_name: str
    duration_weeks: int
    skills: List[SkillToLearn]
    milestone: str

class LearningPath(BaseModel):
    target_role: str
    total_estimated_weeks: int
    phases: List[LearningPhase]

# Course Models
class Course(BaseModel):
    title: str
    provider: str
    url: str
    instructor: Optional[str] = None
    rating: Optional[float] = None
    estimated_hours: Optional[int] = None
    level: str
    price: str  # "Free", "Paid", "$X"
    description: Optional[str] = None

class CourseRecommendations(BaseModel):
    skill_name: str
    courses: List[Course]

# Final Output
class LearningPathOutput(BaseModel):
    skill_gap_analysis: SkillGapAnalysis
    learning_path: LearningPath
    course_recommendations: List[CourseRecommendations]