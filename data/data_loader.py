"""
Data Loader Module

This module handles loading and accessing static data files for the SkillPath AI system.
It loads role requirements and skill dependencies from JSON files into memory
and provides helper functions to access this data efficiently.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache


class DataLoader:
    """
    Singleton class to load and manage static data for the SkillPath AI system.
    Loads data once at initialization and keeps it in memory for fast access.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Ensure only one instance of DataLoader exists (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the data loader and load all JSON files"""
        if DataLoader._initialized:
            return
            
        self.data_dir = self._get_data_directory()
        
        self.roles_data: Dict[str, Any] = {}
        self.skill_dependencies: Dict[str, List[str]] = {}
        self.all_roles: List[str] = []
        
        self._load_data()
        
        DataLoader._initialized = True
    
    def _get_data_directory(self) -> Path:
        """
        Determine the correct path to the data directory.
        Tries multiple locations to be flexible with project structure.
        """
        current_dir = Path(__file__).parent
        data_dir = current_dir
        
        if data_dir.name == 'data':
            return data_dir
        
        project_root = current_dir.parent if current_dir.name != 'skillpath-ai' else current_dir
        data_dir = project_root / 'data'
        
        # Create data directory if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)
        
        return data_dir
    
    def _load_data(self):
        """Load all JSON data files into memory"""
        try:
            # Load roles data
            roles_file = self.data_dir / 'roles_data.json'
            if roles_file.exists():
                with open(roles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Store roles in a dictionary keyed by role name for fast lookup
                    for role in data.get('roles', []):
                        role_name = role.get('role_name')
                        if role_name:
                            self.roles_data[role_name] = role
                            self.all_roles.append(role_name)
                print(f"✓ Loaded {len(self.roles_data)} roles from roles_data.json")
            else:
                print(f"⚠ Warning: roles_data.json not found at {roles_file}")
                self._create_sample_roles_file(roles_file)
            
            # Load skill dependencies
            dependencies_file = self.data_dir / 'skill_dependencies.json'
            if dependencies_file.exists():
                with open(dependencies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.skill_dependencies = data.get('dependencies', {})
                print(f"✓ Loaded {len(self.skill_dependencies)} skill dependencies")
            else:
                print(f"⚠ Warning: skill_dependencies.json not found at {dependencies_file}")
                self._create_sample_dependencies_file(dependencies_file)
                
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing JSON file: {e}")
            raise
        except Exception as e:
            print(f"✗ Error loading data files: {e}")
            raise
    
    # ==================== Helper Functions ====================
    
    def get_all_roles(self) -> List[str]:
        """
        Get a list of all available role names.
        
        Returns:
            List of role names (e.g., ['Full Stack Developer', 'Frontend Developer'])
        """
        return self.all_roles.copy()
    
    def get_role_requirements(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete requirements for a specific role.
        
        Args:
            role_name: Name of the role (e.g., "Full Stack Developer")
            
        Returns:
            Dictionary containing role information and required skills,
            or None if role not found
        """
        return self.roles_data.get(role_name)
    
    def get_required_skills_for_role(self, role_name: str) -> List[Dict[str, Any]]:
        """
        Get just the required skills list for a role.
        
        Args:
            role_name: Name of the role
            
        Returns:
            List of required skill dictionaries
        """
        role = self.get_role_requirements(role_name)
        if role:
            return role.get('required_skills', [])
        return []
    
    def role_exists(self, role_name: str) -> bool:
        """
        Check if a role exists in the data.
        
        Args:
            role_name: Name of the role to check
            
        Returns:
            True if role exists, False otherwise
        """
        return role_name in self.roles_data
    
    def find_role_by_partial_name(self, partial_name: str) -> List[str]:
        """
        Find roles that match a partial name (case-insensitive).
        
        Args:
            partial_name: Partial role name to search for
            
        Returns:
            List of matching role names
        """
        partial_lower = partial_name.lower()
        return [
            role for role in self.all_roles
            if partial_lower in role.lower()
        ]
    
    def get_skill_dependencies(self, skill_name: str) -> List[str]:
        """
        Get the list of prerequisite skills for a given skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            List of prerequisite skill names (empty list if no dependencies)
        """
        return self.skill_dependencies.get(skill_name, [])
    
    def has_dependencies(self, skill_name: str) -> bool:
        """
        Check if a skill has any prerequisites.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            True if skill has dependencies, False otherwise
        """
        return skill_name in self.skill_dependencies and len(self.skill_dependencies[skill_name]) > 0
    
    def get_all_skills_from_roles(self) -> List[str]:
        """
        Get a unique list of all skills mentioned across all roles.
        
        Returns:
            List of unique skill names
        """
        all_skills = set()
        for role_data in self.roles_data.values():
            for skill in role_data.get('required_skills', []):
                all_skills.add(skill.get('skill_name'))
        return sorted(list(all_skills))
    
    def get_skills_by_category(self, category: str) -> List[str]:
        """
        Get all skills that belong to a specific category.
        
        Args:
            category: Category name (e.g., "Frontend", "Backend", "Database")
            
        Returns:
            List of skill names in that category
        """
        skills = set()
        for role_data in self.roles_data.values():
            for skill in role_data.get('required_skills', []):
                if skill.get('category') == category:
                    skills.add(skill.get('skill_name'))
        return sorted(list(skills))
    
    def get_all_categories(self) -> List[str]:
        """
        Get all unique skill categories across all roles.
        
        Returns:
            List of category names
        """
        categories = set()
        for role_data in self.roles_data.values():
            for skill in role_data.get('required_skills', []):
                category = skill.get('category')
                if category:
                    categories.add(category)
        return sorted(list(categories))
    
    @lru_cache(maxsize=128)
    def get_learning_order(self, skill_name: str) -> List[str]:
        """
        Get the complete learning order for a skill (including all nested dependencies).
        Uses caching for performance.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Ordered list of skills to learn (dependencies first, then the skill itself)
        """
        visited = set()
        order = []
        
        def _dfs(skill: str):
            if skill in visited:
                return
            visited.add(skill)
            
            # First, process dependencies
            dependencies = self.get_skill_dependencies(skill)
            for dep in dependencies:
                _dfs(dep)
            
            # Then add the skill itself
            order.append(skill)
        
        _dfs(skill_name)
        return order
    
    def validate_skill_level(self, level: str) -> bool:
        """
        Validate if a skill level is valid.
        
        Args:
            level: Skill level string
            
        Returns:
            True if valid, False otherwise
        """
        valid_levels = ['none', 'beginner', 'intermediate', 'advanced', 'expert']
        return level.lower() in valid_levels
    
    def compare_skill_levels(self, level1: str, level2: str) -> int:
        """
        Compare two skill levels.
        
        Args:
            level1: First skill level
            level2: Second skill level
            
        Returns:
            -1 if level1 < level2
             0 if level1 == level2
             1 if level1 > level2
        """
        level_order = {
            'none': 0,
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
        
        l1 = level_order.get(level1.lower(), 0)
        l2 = level_order.get(level2.lower(), 0)
        
        if l1 < l2:
            return -1
        elif l1 > l2:
            return 1
        else:
            return 0
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all loaded data.
        
        Returns:
            Dictionary with counts and basic info
        """
        return {
            'total_roles': len(self.roles_data),
            'total_skills': len(self.get_all_skills_from_roles()),
            'total_dependencies': len(self.skill_dependencies),
            'categories': self.get_all_categories(),
            'roles': self.all_roles
        }
    
    def reload_data(self):
        """
        Reload all data files from disk.
        Useful if files are updated during runtime.
        """
        self.roles_data.clear()
        self.skill_dependencies.clear()
        self.all_roles.clear()
        self._load_data()
        print("✓ Data reloaded successfully")


# ==================== Convenience Functions ====================
# These are module-level functions that use the singleton instance

# Create singleton instance
_data_loader = DataLoader()


def get_all_roles() -> List[str]:
    """Get a list of all available role names."""
    return _data_loader.get_all_roles()


def get_role_requirements(role_name: str) -> Optional[Dict[str, Any]]:
    """Get the complete requirements for a specific role."""
    return _data_loader.get_role_requirements(role_name)


def get_required_skills_for_role(role_name: str) -> List[Dict[str, Any]]:
    """Get just the required skills list for a role."""
    return _data_loader.get_required_skills_for_role(role_name)


def role_exists(role_name: str) -> bool:
    """Check if a role exists in the data."""
    return _data_loader.role_exists(role_name)


def find_role_by_partial_name(partial_name: str) -> List[str]:
    """Find roles that match a partial name (case-insensitive)."""
    return _data_loader.find_role_by_partial_name(partial_name)


def get_skill_dependencies(skill_name: str) -> List[str]:
    """Get the list of prerequisite skills for a given skill."""
    return _data_loader.get_skill_dependencies(skill_name)


def has_dependencies(skill_name: str) -> bool:
    """Check if a skill has any prerequisites."""
    return _data_loader.has_dependencies(skill_name)


def get_all_skills_from_roles() -> List[str]:
    """Get a unique list of all skills mentioned across all roles."""
    return _data_loader.get_all_skills_from_roles()


def get_skills_by_category(category: str) -> List[str]:
    """Get all skills that belong to a specific category."""
    return _data_loader.get_skills_by_category(category)


def get_all_categories() -> List[str]:
    """Get all unique skill categories across all roles."""
    return _data_loader.get_all_categories()


def get_learning_order(skill_name: str) -> List[str]:
    """Get the complete learning order for a skill (including all nested dependencies)."""
    return _data_loader.get_learning_order(skill_name)


def validate_skill_level(level: str) -> bool:
    """Validate if a skill level is valid."""
    return _data_loader.validate_skill_level(level)


def compare_skill_levels(level1: str, level2: str) -> int:
    """Compare two skill levels."""
    return _data_loader.compare_skill_levels(level1, level2)


def get_data_summary() -> Dict[str, Any]:
    """Get a summary of all loaded data."""
    return _data_loader.get_data_summary()


def reload_data():
    """Reload all data files from disk."""
    _data_loader.reload_data()


# ==================== Example Usage ====================

if __name__ == "__main__":
    """
    Example usage and testing of the data loader.
    Run this file directly to test: python data_loader.py
    """
    
    print("\n" + "="*60)
    print("SkillPath AI - Data Loader Test")
    print("="*60 + "\n")
    
    # Test 1: Get data summary
    print("📊 Data Summary:")
    summary = get_data_summary()
    for key, value in summary.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 2: Get all roles
    print("👔 Available Roles:")
    roles = get_all_roles()
    for i, role in enumerate(roles, 1):
        print(f"  {i}. {role}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 3: Get requirements for a specific role
    if roles:
        test_role = roles[0]  # Use first role for testing
        print(f"🎯 Requirements for '{test_role}':")
        role_data = get_role_requirements(test_role)
        if role_data:
            print(f"  Experience Level: {role_data.get('experience_level')}")
            print(f"  Required Skills: {len(role_data.get('required_skills', []))}")
            print("\n  Top 5 Skills:")
            for skill in role_data.get('required_skills', [])[:5]:
                print(f"    • {skill.get('skill_name')} ({skill.get('category')}) - {skill.get('importance')}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 4: Test skill dependencies
    print("🔗 Skill Dependencies:")
    test_skills = ['React', 'Express.js', 'TypeScript']
    for skill in test_skills:
        deps = get_skill_dependencies(skill)
        if deps:
            print(f"  {skill} requires: {', '.join(deps)}")
        else:
            print(f"  {skill}: No dependencies")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 5: Get learning order
    print("📚 Learning Order (with nested dependencies):")
    if test_skills:
        test_skill = test_skills[0]
        order = get_learning_order(test_skill)
        print(f"  To learn '{test_skill}', study in this order:")
        for i, skill in enumerate(order, 1):
            print(f"    {i}. {skill}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 6: Get all categories
    print("📁 Skill Categories:")
    categories = get_all_categories()
    for category in categories:
        skills = get_skills_by_category(category)
        print(f"  {category}: {len(skills)} skills")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 7: Role search
    print("🔍 Role Search Test:")
    search_terms = ['full', 'frontend', 'backend']
    for term in search_terms:
        matches = find_role_by_partial_name(term)
        if matches:
            print(f"  '{term}' found: {', '.join(matches)}")
        else:
            print(f"  '{term}' found: No matches")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 8: Skill level comparison
    print("📊 Skill Level Comparison:")
    comparisons = [
        ('beginner', 'intermediate'),
        ('advanced', 'beginner'),
        ('intermediate', 'intermediate')
    ]
    for level1, level2 in comparisons:
        result = compare_skill_levels(level1, level2)
        if result == -1:
            comparison = "<"
        elif result == 1:
            comparison = ">"
        else:
            comparison = "="
        print(f"  {level1} {comparison} {level2}")
    
    print("\n" + "="*60)
    print("✓ All tests completed successfully!")
    print("="*60 + "\n")