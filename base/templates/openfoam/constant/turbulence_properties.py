from dataclasses import dataclass
from enum import Enum


class TurbulenceModel(Enum):
    LAMINAR = "laminar"
    RAS = "RAS"
    LES = "LES"


class RASModel(Enum):
    K_EPSILON = "kEpsilon"
    K_OMEGA = "kOmega"
    K_OMEGA_SST = "kOmegaSST"
    REALIZABLE_KE = "realizableKE"
    SPALART_ALLMARAS = "SpalartAllmaras"


@dataclass
class TurbulencePropertiesParams:
    simulation_type: TurbulenceModel = TurbulenceModel.RAS
    ras_model: RASModel = RASModel.K_EPSILON
    turbulence: bool = True
    print_coeffs: bool = True


def generate_turbulence_properties(params: TurbulencePropertiesParams) -> str:
    """Generate turbulenceProperties file for OpenFOAM"""

    content = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      turbulenceProperties;
}}

simulationType  {params.simulation_type.value};
"""

    if params.simulation_type == TurbulenceModel.RAS:
        content += f"""
RAS
{{
    RASModel        {params.ras_model.value};
    turbulence      {'on' if params.turbulence else 'off'};
    printCoeffs     {'on' if params.print_coeffs else 'off'};
}}
"""
    elif params.simulation_type == TurbulenceModel.LES:
        content += """
LES
{
    LESModel        Smagorinsky;
    turbulence      on;
    printCoeffs     on;
}
"""

    return content
