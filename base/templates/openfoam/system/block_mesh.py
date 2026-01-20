from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from base.nozzle.parabolic_nozzle import ParabolicNozzle


@dataclass
class BlockMeshParams:
    # Wedge geometry (axisymmetric)
    wedge_angle_deg: float = 5.0

    # Discretization
    n_axial: int = 200         # number of axial blocks (segments)
    n_radial: int = 50         # cells in radial direction
    axial_grading: float = 1.0
    radial_grading: float = 1.0

    # Patch names
    inlet_patch: str = "inlet"
    outlet_patch: str = "outlet"
    wall_patch: str = "wall"
    wedge0_patch: str = "wedge0"
    wedge1_patch: str = "wedge1"

    # Units
    convert_to_meters: float = 1.0


def _wedge_points(x: np.ndarray, r: np.ndarray, theta_half: float) -> Tuple[List[Tuple[float, float, float]], List[int], List[int], List[int], List[int]]:
    """Build vertices for two wedge planes (+/- theta_half).
    Returns:
      vertices: list of (x,y,z)
      idx_axis_p0, idx_wall_p0, idx_axis_p1, idx_wall_p1: index arrays per station
    """
    verts: List[Tuple[float, float, float]] = []
    idx_axis_p0: List[int] = []
    idx_wall_p0: List[int] = []
    idx_axis_p1: List[int] = []
    idx_wall_p1: List[int] = []

    c = np.cos(theta_half)
    s = np.sin(theta_half)

    for xi, ri in zip(x, r):
        # plane 0 (-theta_half)
        idx_axis_p0.append(len(verts))
        verts.append((float(xi), 0.0, 0.0))
        idx_wall_p0.append(len(verts))
        verts.append((float(xi), float(ri * c), float(-ri * s)))

        # plane 1 (+theta_half)
        idx_axis_p1.append(len(verts))
        verts.append((float(xi), 0.0, 0.0))
        idx_wall_p1.append(len(verts))
        verts.append((float(xi), float(ri * c), float(+ri * s)))

    return verts, idx_axis_p0, idx_wall_p0, idx_axis_p1, idx_wall_p1


def generate_block_mesh_dict(nozzle: ParabolicNozzle, params: BlockMeshParams) -> str:
    """
    Generate a blockMeshDict using an axisymmetric wedge and
    axial strips built from the nozzle contour.
    """
    # stations = n_axial + 1 => n_axial blocks
    x, r = nozzle.get_outer_wall(n_points=params.n_axial + 1)

    theta = np.deg2rad(params.wedge_angle_deg)
    theta_half = 0.5 * theta

    verts, a0, w0, a1, w1 = _wedge_points(x, r, theta_half)

    # Build blocks: one block per axial segment
    blocks: List[str] = []
    grading = f"simpleGrading ({params.axial_grading} {params.radial_grading} 1)"

    for i in range(len(x) - 1):
        # vertex ordering: lower face (plane 0), upper face (plane 1)
        v0 = a0[i]
        v1 = a0[i + 1]
        v2 = w0[i + 1]
        v3 = w0[i]
        v4 = a1[i]
        v5 = a1[i + 1]
        v6 = w1[i + 1]
        v7 = w1[i]

        block = f"    hex ({v0} {v1} {v2} {v3} {v4} {v5} {v6} {v7}) (1 {params.n_radial} 1) {grading}"
        blocks.append(block)

    # Boundary faces
    inlet_faces = []
    outlet_faces = []
    wall_faces = []
    wedge0_faces = []
    wedge1_faces = []

    # Inlet face at first station (x[0])
    inlet_faces.append(f"        ({a0[0]} {a1[0]} {w1[0]} {w0[0]})")
    # Outlet face at last station (x[-1])
    j = len(x) - 1
    outlet_faces.append(f"        ({a0[j]} {w0[j]} {w1[j]} {a1[j]})")

    # For each axial strip, add wall and wedge faces
    for i in range(len(x) - 1):
        # Wall face between stations i and i+1 (curved wall side)
        wall_faces.append(f"        ({w0[i]} {w0[i+1]} {w1[i+1]} {w1[i]})")
        # Wedge faces (plane 0 and plane 1)
        wedge0_faces.append(f"        ({a0[i]} {a0[i+1]} {w0[i+1]} {w0[i]})")
        wedge1_faces.append(f"        ({a1[i+1]} {a1[i]} {w1[i]} {w1[i+1]})")

    # Format vertices
    vertices_block = "vertices\n(\n" + "\n".join(
        [f"    ({vx:.9g} {vy:.9g} {vz:.9g})" for vx, vy, vz in verts]) + "\n);\n"

    # Format blocks
    blocks_block = "blocks\n(\n" + "\n".join(blocks) + "\n);\n"

    # No curved edges needed (we approximate with many blocks)
    edges_block = "edges\n(\n);\n"

    # Boundary block
    boundary = f"""boundary
(
    {params.inlet_patch}
    {{
        type patch;
        faces
        (
{chr(10).join(inlet_faces)}
        );
    }}

    {params.outlet_patch}
    {{
        type patch;
        faces
        (
{chr(10).join(outlet_faces)}
        );
    }}

    {params.wall_patch}
    {{
        type wall;
        faces
        (
{chr(10).join(wall_faces)}
        );
    }}

    {params.wedge0_patch}
    {{
        type wedge;
        faces
        (
{chr(10).join(wedge0_faces)}
        );
    }}

    {params.wedge1_patch}
    {{
        type wedge;
        faces
        (
{chr(10).join(wedge1_faces)}
        );
    }}
);
"""

    merge_block = "mergePatchPairs\n(\n);\n"

    header = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
convertToMeters {params.convert_to_meters:.9g};

"""

    return header + vertices_block + blocks_block + edges_block + boundary + merge_block
