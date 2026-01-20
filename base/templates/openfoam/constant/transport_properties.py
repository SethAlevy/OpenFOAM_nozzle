from dataclasses import dataclass


@dataclass
class TransportPropertiesParams:
    """Parameters for incompressible transport properties"""
    nu: float = 1.48e-5  # Kinematic viscosity [m^2/s]
    
    # Transport model (Newtonian, BirdCarreau, etc.)
    transport_model: str = "Newtonian"


def generate_transport_properties(params: TransportPropertiesParams) -> str:
    """Generate transportProperties file for incompressible solvers"""
    
    return f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      transportProperties;
}}

transportModel  {params.transport_model};

nu              {params.nu:.6e};
"""