from dataclasses import dataclass
from enum import Enum


class ThermoType(Enum):
    """Thermophysical model type"""
    HEPSI_THERMO = "hePsiThermo"
    HE_RHO_THERMO = "heRhoThermo"
    PSI_THERMO = "psiThermo"
    RHO_THERMO = "rhoThermo"


class EquationOfState(Enum):
    """Equation of state"""
    PERFECT_GAS = "perfectGas"
    INCOMPRESSIBLE_PERFECT_GAS = "incompressiblePerfectGas"
    RHO_CONST = "rhoConst"


class ThermoModel(Enum):
    """Thermodynamic model"""
    HCONST = "hConst"
    JANAF = "janaf"
    E_CONST = "eConst"


class TransportModel(Enum):
    """Transport model"""
    CONST = "const"
    SUTHERLAND = "sutherland"


@dataclass
class ThermophysicalPropertiesParams:
    """Parameters for thermophysicalProperties (compressible)"""

    # Thermo type selection
    thermo_type: ThermoType = ThermoType.HEPSI_THERMO
    mixture: str = "pureMixture"
    transport: TransportModel = TransportModel.SUTHERLAND
    thermo: ThermoModel = ThermoModel.JANAF
    equation_of_state: EquationOfState = EquationOfState.PERFECT_GAS
    specie: str = "specie"
    energy: str = "sensibleEnthalpy"

    # Gas properties
    mol_weight: float = 28.96  # kg/kmol (air)

    # Thermodynamic properties
    Cp: float = 1005.0  # J/kg/K
    Hf: float = 0.0     # Heat of formation J/kg

    # Transport properties (Sutherland)
    mu: float = 1.81e-5      # Reference viscosity [Pa·s]
    Ts: float = 110.4        # Sutherland temperature [K]
    Pr: float = 0.7          # Prandtl number

    # Or const transport
    mu_const: float = 1.81e-5  # If using const transport


def generate_thermophysical_properties(params: ThermophysicalPropertiesParams) -> str:
    """Generate thermophysicalProperties for compressible solvers"""

    content = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      thermophysicalProperties;
}}

thermoType
{{
    type            {params.thermo_type.value};
    mixture         {params.mixture};
    transport       {params.transport.value};
    thermo          {params.thermo.value};
    equationOfState {params.equation_of_state.value};
    specie          {params.specie};
    energy          {params.energy};
}}

mixture
{{
    specie
    {{
        molWeight   {params.mol_weight};
    }}
"""

    if params.thermo == ThermoModel.HCONST:
        content += f"""    thermodynamics
    {{
        Cp          {params.Cp};
        Hf          {params.Hf};
    }}
"""
    elif params.thermo == ThermoModel.JANAF:
        # JANAF coefficients for air (simplified)
        content += """    thermodynamics
    {
        Tlow            200;
        Thigh           6000;
        Tcommon         1000;
        highCpCoeffs    ( 3.28254 0.00148309 -5.68010e-07 1.00975e-10 -6.98508e-15 -1088.46 5.45323 );
        lowCpCoeffs     ( 3.56839 -0.000726708 2.31398e-06 -2.55152e-09 7.72293e-13 -1063.94 3.78510 );
    }
"""

    if params.transport == TransportModel.SUTHERLAND:
        content += f"""    transport
    {{
        As          {params.mu / 1.458e-6:.6e};
        Ts          {params.Ts};
    }}
"""
    elif params.transport == TransportModel.CONST:
        content += f"""    transport
    {{
        mu          {params.mu_const:.6e};
        Pr          {params.Pr};
    }}
"""

    content += "}\n"

    return content
