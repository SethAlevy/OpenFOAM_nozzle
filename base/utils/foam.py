def patch(name: str, setup: dict, default: str) -> str:
    """
    Resolve patch name from parameter, setup dict, or default.

    Args:
        name: Patch name provided as parameter.
        setup: Dictionary with optional patch name defaults.
        default: Default patch name if none provided.

    Returns:
        str: Resolved patch name."""
    return name if name is not None else setup.get(default, default)


def generate_foam_field(
    object_name: str,
    dimensions: str,
    internal_value: str,
    boundary_conditions: dict,
    field_class: str = "volScalarField",
) -> str:
    """
    Generic OpenFOAM field file template generator.

    Args:
        object_name: Object name in FoamFile (e.g., "U", "p", "k")
        dimensions: Dimensional set [kg m s K mol A cd]
        internal_value: Internal field value
        boundary_conditions: Dict mapping patch names to BC specs
        field_class: Field class (volScalarField, volVectorField, etc.)

    Returns:
        Formatted OpenFOAM field file as string
    """
    foam_file_header = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       {field_class};
    object      {object_name};
}}

dimensions      {dimensions};

internalField   uniform {internal_value};

boundaryField
{{"""

    boundary_entries = "\n".join(
        f"    {bc_spec['patch_name']}\n    {{\n{bc_spec['content']}\n    }}"
        for bc_spec in boundary_conditions.values()
    )

    foam_file_footer = """
}
"""
    return foam_file_header + "\n" + boundary_entries + foam_file_footer


def build_bc_spec(patch_name: str, bc_type: str, value: str = None) -> dict:
    """
    Build a boundary condition specification.

    Args:
        patch_name: Name of the patch
        bc_type: OpenFOAM BC type (fixedValue, zeroGradient, etc.)
        value: Value line if needed (e.g., "value   uniform 0.5;")

    Returns:
        Dictionary with patch_name and content keys
    """
    content = f"        type            {bc_type};"
    if value:
        content += f"\n        {value}"

    return {
        "patch_name": patch_name,
        "content": content,
    }