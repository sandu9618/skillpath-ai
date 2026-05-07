from data_types.dto import RoleRequirements
from data.data_loader import DataLoader


def get_role_requirements(role_name: str) -> RoleRequirements:
    """
    Load required skills and metadata for a target role from the static catalog.

    Args:
        role_name: Exact role title as stored in ``roles_data.json`` (e.g. ``Full Stack Developer``).

    Returns:
        Parsed ``RoleRequirements`` including ``required_skills`` for gap analysis.

    Raises:
        ValueError: If the role name is not found; the error text lists sample available roles.
    """
    data_loader = DataLoader()
    raw = data_loader.get_role_requirements(role_name)
    if raw is None:
        sample = ", ".join(data_loader.get_all_roles()[:15])
        raise ValueError(
            f"Role not found: {role_name!r}. Match an exact catalog title. Examples: {sample}"
        )
    return RoleRequirements.model_validate(raw)
