import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from base.nozzle.parabolic_nozzle import ParabolicNozzle


@dataclass
class BoundaryLayerParams:
    """
    Optional boundary layer grading definition.
    Two modes (set one):
      - n_layers + expansion_ratio: geometric progression
      - first_layer_thickness: absolute size, ratio computed from nozzle geometry
    """
    enabled: bool = False

    # Mode 1: explicit layers + ratio
    n_layers: Optional[int] = None
    expansion_ratio: Optional[float] = None

    # Mode 2: first layer absolute thickness (meters)
    first_layer_thickness: Optional[float] = None


@dataclass
class BlockMeshParams:
    # Wedge geometry (axisymmetric)
    wedge_angle_deg: float = 5.0

    # Discretization
    n_axial: int = 200
    n_radial: int = 50
    axial_grading: float = 1.0
    radial_grading: float = 1.0
    uniform_axial_spacing: bool = True

    # Patch names
    inlet_patch: str = "inlet"
    outlet_patch: str = "outlet"
    wall_patch: str = "wall"
    wedge0_patch: str = "wedge0"
    wedge1_patch: str = "wedge1"

    # Units
    convert_to_meters: float = 1.0

    # Optional boundary layer
    boundary_layer: BoundaryLayerParams = field(
        default_factory=BoundaryLayerParams)


def _resample_uniform_axial(x: np.ndarray, r: np.ndarray, n_axial: int) -> Tuple[np.ndarray, np.ndarray]:
    """Uniform Δx resampling to avoid spacing jumps at section interfaces."""
    xu = np.linspace(float(x[0]), float(x[-1]), n_axial + 1)
    ru = np.interp(xu, x, r)
    return xu, ru


def _compute_radial_grading(params: BlockMeshParams, r_wall: np.ndarray) -> str:
    bl = params.boundary_layer

    if not bl.enabled:
        return f"{params.radial_grading}"

    n_layers = bl.n_layers if bl.n_layers is not None else min(20, params.n_radial)
    n_layers = max(1, min(n_layers, params.n_radial))
    n_core = params.n_radial - n_layers

    # axis -> wall direction in this mesh
    if bl.expansion_ratio is not None:
        # User input is per-layer growth away from wall (e.g. 1.2)
        g = float(bl.expansion_ratio)
        if g <= 1.0:
            raise ValueError("boundary_layer.expansion_ratio must be > 1.0")
        # Convert per-layer growth to total segment expansion (axis -> wall)
        seg_exp = (1.0 / g) ** max(n_layers - 1, 1)

    elif bl.first_layer_thickness is not None:
        r_avg = float(np.mean(r_wall))
        avg = (r_avg / max(n_layers, 1))
        g = max(avg / float(bl.first_layer_thickness), 1.01)
        seg_exp = (1.0 / g) ** max(n_layers - 1, 1)

    else:
        # fallback
        g = 1.2
        seg_exp = (1.0 / g) ** max(n_layers - 1, 1)

    if n_core <= 0:
        # Entire radial direction is BL
        return f"((1 1 {seg_exp:.6g}))"

    # Keep simple split by cell fraction (core + near-wall BL segment)
    frac_core = n_core / params.n_radial
    frac_bl = n_layers / params.n_radial

    # Last segment is near wall
    return (
        f"(("
        f"{frac_core:.6g} {frac_core:.6g} {params.radial_grading:.6g}"
        f")("
        f"{frac_bl:.6g} {frac_bl:.6g} {seg_exp:.6g}"
        f"))"
    )


def _wedge_points(
    x: np.ndarray,
    r: np.ndarray,
    theta_half: float
) -> Tuple[List[Tuple[float, float, float]], List[int], List[int], List[int], List[int]]:
    """
    Build vertices for two wedge planes (+/- theta_half).
    Per station, vertex order: axis_p0, wall_p0, axis_p1, wall_p1
    """
    verts: List[Tuple[float, float, float]] = []
    idx_axis_p0: List[int] = []
    idx_wall_p0: List[int] = []
    idx_axis_p1: List[int] = []
    idx_wall_p1: List[int] = []

    c = np.cos(theta_half)
    s = np.sin(theta_half)

    for xi, ri in zip(x, r):
        # plane 0: -theta_half (negative z side)
        idx_axis_p0.append(len(verts))
        verts.append((float(xi), 0.0, 0.0))

        idx_wall_p0.append(len(verts))
        verts.append((float(xi), float(ri * c), float(-ri * s)))

        # plane 1: +theta_half (positive z side)
        idx_axis_p1.append(len(verts))
        verts.append((float(xi), 0.0, 0.0))

        idx_wall_p1.append(len(verts))
        verts.append((float(xi), float(ri * c), float(+ri * s)))

    return verts, idx_axis_p0, idx_wall_p0, idx_axis_p1, idx_wall_p1


def _build_blocks(
    x: np.ndarray,
    r: np.ndarray,
    a0: List[int], w0: List[int],
    a1: List[int], w1: List[int],
    params: BlockMeshParams
) -> List[str]:
    radial_grading = _compute_radial_grading(params, r)
    grading = f"simpleGrading ({params.axial_grading} {radial_grading} 1)"
    blocks = []
    for i in range(len(x) - 1):
        # hex vertex ordering: 4 bottom (p0) + 4 top (p1), axial then radial
        # follows OpenFOAM right-hand rule
        v0, v1, v2, v3 = a0[i], a0[i + 1], w0[i + 1], w0[i]
        v4, v5, v6, v7 = a1[i], a1[i + 1], w1[i + 1], w1[i]
        blocks.append(
            f"    hex ({v0} {v1} {v2} {v3} {v4} {v5} {v6} {v7}) (1 {params.n_radial} 1) {grading}"
        )
    return blocks


def _build_boundary_faces(
    x: np.ndarray,
    a0: List[int], w0: List[int],
    a1: List[int], w1: List[int]
) -> dict:
    j = len(x) - 1

    # Face normals must point outward
    # inlet: normal points in -x direction → reverse winding
    inlet_faces = [f"        ({a0[0]} {w0[0]} {w1[0]} {a1[0]})"]
    # outlet: normal points in +x direction
    outlet_faces = [f"        ({a0[j]} {a1[j]} {w1[j]} {w0[j]})"]

    wall_faces = []
    wedge0_faces = []
    wedge1_faces = []

    for i in range(len(x) - 1):
        # wall: normal points outward (+r direction)
        wall_faces.append(
            f"        ({w0[i]} {w1[i]} {w1[i + 1]} {w0[i + 1]})")
        # wedge0: plane at -theta (p0), normal points in -z direction
        wedge0_faces.append(
            f"        ({a0[i]} {w0[i]} {w0[i + 1]} {a0[i + 1]})")
        # wedge1: plane at +theta (p1), normal points in +z direction
        wedge1_faces.append(
            f"        ({a1[i + 1]} {w1[i + 1]} {w1[i]} {a1[i]})")

    return {
        "inlet": inlet_faces,
        "outlet": outlet_faces,
        "wall": wall_faces,
        "wedge0": wedge0_faces,
        "wedge1": wedge1_faces,
    }


def _format_vertices(verts: List[Tuple[float, float, float]]) -> str:
    lines = "\n".join([f"    ({x:.9g} {y:.9g} {z:.9g})" for x, y, z in verts])
    return f"vertices\n(\n{lines}\n);\n\n"


def _patch_block(name, patch_type, face_list):
    return (
        f"    {name}\n    {{\n        type {patch_type};\n"
        f"        faces\n        (\n"
        + "\n".join(face_list)
        + f"\n        );\n    }}"
    )


def _format_boundary(faces: dict, params: BlockMeshParams) -> str:
    patches = "\n\n".join([
        _patch_block(params.inlet_patch, "patch", faces["inlet"]),
        _patch_block(params.outlet_patch, "patch", faces["outlet"]),
        _patch_block(params.wall_patch, "wall", faces["wall"]),
        _patch_block(params.wedge0_patch, "wedge", faces["wedge0"]),
        _patch_block(params.wedge1_patch, "wedge", faces["wedge1"]),
    ])
    return f"boundary\n(\n{patches}\n);\n"


def _format_header(params: BlockMeshParams) -> str:
    return (
        f"FoamFile\n{{\n    version     2.0;\n    format      ascii;\n"
        f"    class       dictionary;\n    object      blockMeshDict;\n}}\n"
        f"convertToMeters {params.convert_to_meters:.9g};\n\n"
    )


def generate_block_mesh_dict(nozzle: ParabolicNozzle, params: BlockMeshParams) -> str:
    """
    Generate a blockMeshDict using an axisymmetric wedge and
    axial strips built from the nozzle contour.
    """
    x_raw, r_raw = nozzle.get_outer_wall(n_points=max(params.n_axial * 5, 1000))

    if params.uniform_axial_spacing:
        x, r = _resample_uniform_axial(x_raw, r_raw, params.n_axial)
    else:
        x, r = nozzle.get_outer_wall(n_points=params.n_axial + 1)

    theta_half = 0.5 * np.deg2rad(params.wedge_angle_deg)
    verts, a0, w0, a1, w1 = _wedge_points(x, r, theta_half)

    blocks = _build_blocks(x, r, a0, w0, a1, w1, params)
    faces = _build_boundary_faces(x, a0, w0, a1, w1)

    return (
        _format_header(params)
        + _format_vertices(verts)
        + "blocks\n(\n" + "\n".join(blocks) + "\n);\n"
        + "edges\n(\n);\n"
        + _format_boundary(faces, params)
        + "mergePatchPairs\n(\n);\n"
    )
