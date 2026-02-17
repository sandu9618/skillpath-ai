from data_types.dto import RoleRequirements
from data.data_loader import DataLoader
def get_role_requirements(role_name: str) -> RoleRequirements:
    data_loader = DataLoader()
    role_requirements = data_loader.get_role_requirements(role_name)
    return role_requirements