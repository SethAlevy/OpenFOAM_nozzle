from base.utils.foam import patch, build_bc_spec, generate_foam_field


def p_bc(
    pressure_value: str,
    inlet_patch: str = None,
    outlet_patch: str = None,
    lower_wall_patch: str = None,
    upper_wall_patch: str = None,
    front_patch: str = None,
    back_patch: str = None,
    airfoil_patch: str = None,
    setup: dict = None,
) -> str:
    """
    Generate pressure (p) boundary condition file.

    Args:
        pressure_value: Pressure value string
        inlet_patch: Inlet patch name override
        outlet_patch: Outlet patch name override
        lower_wall_patch: Lower wall patch name override
        upper_wall_patch: Upper wall patch name override
        front_patch: Front patch name override
        back_patch: Back patch name override
        airfoil_patch: Airfoil patch name override
        setup: Dictionary with optional patch name defaults

    Returns:
        OpenFOAM p field file content
    """
    setup = setup or {}
    inlet = patch(inlet_patch, setup, "inlet")
    outlet = patch(outlet_patch, setup, "outlet")
    lower_wall = patch(lower_wall_patch, setup, "lowerWall")
    upper_wall = patch(upper_wall_patch, setup, "upperWall")
    front = patch(front_patch, setup, "front")
    back = patch(back_patch, setup, "back")
    airfoil = patch(airfoil_patch, setup, "airfoil")

    boundary_conditions = {
        "inlet": build_bc_spec(inlet, "zeroGradient"),
        "outlet": build_bc_spec(
            outlet, "fixedValue", f"value           uniform {pressure_value};"
        ),
        "lowerWall": build_bc_spec(lower_wall, "zeroGradient"),
        "upperWall": build_bc_spec(upper_wall, "zeroGradient"),
        "front": build_bc_spec(front, "symmetryPlane"),
        "back": build_bc_spec(back, "symmetryPlane"),
        "airfoil": build_bc_spec(airfoil, "zeroGradient"),
    }

    return generate_foam_field(
        "p", "[0 2 -2 0 0 0 0]", pressure_value, boundary_conditions
    )
