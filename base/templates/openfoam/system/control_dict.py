from typing import Optional
from enum import Enum
from dataclasses import dataclass


class SolverType(Enum):
    """OpenFOAM solver types"""
    SIMPLE_FOAM = "simpleFoam"
    PIMPLE_FOAM = "pimpleFoam"
    RHOCENTRALFOAM = "rhoCentralFoam"
    SONICFOAM = "sonicFoam"


@dataclass
class ControlDictParams:
    """Default parameters for controlDict"""

    # Simulation control
    application: SolverType
    start_time: float
    end_time: float
    delta_t: float
    write_interval: int

    # Solver settings
    write_format: str = "ascii"
    write_precision: int = 6
    write_compression: str = "off"
    time_format: str = "general"
    time_precision: int = 6

    # Convergence
    purge_write: int = 0  # Keep all time steps (0 = keep all)


def generate_control_dict(params: ControlDictParams) -> str:
    """
    Generate OpenFOAM controlDict file.

    Args:
        params: ControlDictParams object with simulation settings

    Returns:
        Formatted controlDict file as string
    """

    content = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}}

// ========== APPLICATION ==========
application         {params.application.value};

// ========== TIME CONTROL ==========
startTime           {params.start_time};
endTime             {params.end_time};
deltaT              {params.delta_t};

writeControl        timeStep;
writeInterval       {params.write_interval};

// ========== OUTPUT FORMAT ==========
writeFormat         {params.write_format};
writePrecision      {params.write_precision};
writeCompression    {params.write_compression};

timeFormat          {params.time_format};
timePrecision       {params.time_precision};

// ========== CLEANUP ==========
purgeWrite          {params.purge_write};

// ========== FUNCTION OBJECTS ==========
functions
{{
}}
"""

    return content
