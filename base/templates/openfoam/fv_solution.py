from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class LinearSolverParams:
    solver: str = "PBiCG"
    tolerance: float = 1e-6
    relTol: float = 0.0
    preconditioner: Optional[str] = None
    smoother: Optional[str] = None


@dataclass
class FvSolutionParams:
    # Field solvers
    p: LinearSolverParams
    U: LinearSolverParams
    k: Optional[LinearSolverParams] = None
    epsilon: Optional[LinearSolverParams] = None
    omega: Optional[LinearSolverParams] = None

    # Algorithm section (SIMPLE or PIMPLE)
    algorithm: str = "PIMPLE"  # SIMPLE or PIMPLE
    nCorrectors: int = 2
    nNonOrthogonalCorrectors: int = 1
    momentumPredictor: bool = True

    # Relaxation
    relaxation_p: float = 0.3
    relaxation_U: float = 0.7
    relaxation_k: Optional[float] = 0.7
    relaxation_epsilon: Optional[float] = 0.7
    relaxation_omega: Optional[float] = None

    # Optional residualControl (for PIMPLE)
    residual_control: Optional[Dict[str, float]] = None


def _linear_solver_block(name: str, cfg: LinearSolverParams) -> str:
    lines = [f"    {name}", "    {", f"        solver          {cfg.solver};",
             f"        tolerance       {cfg.tolerance};",
             f"        relTol         {cfg.relTol};"]
    if cfg.preconditioner:
        lines.append(f"        preconditioner  {cfg.preconditioner};")
    if cfg.smoother:
        lines.append(f"        smoother        {cfg.smoother};")
    lines.append("    }")
    return "\n".join(lines)


def generate_fv_solution(params: FvSolutionParams) -> str:
    header = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}
"""

    # solvers section
    solvers = ["solvers", "{",
               _linear_solver_block("p", params.p),
               _linear_solver_block("U", params.U)]
    if params.k:
        solvers.append(_linear_solver_block("k", params.k))
    if params.epsilon:
        solvers.append(_linear_solver_block("epsilon", params.epsilon))
    if params.omega:
        solvers.append(_linear_solver_block("omega", params.omega))
    solvers.append("}")
    solvers_block = "\n".join(solvers)

    # algorithm section
    algo_name = params.algorithm.upper()
    algo_lines = [f"{algo_name}", "{",
                  f"    nCorrectors                {params.nCorrectors};",
                  f"    nNonOrthogonalCorrectors   {params.nNonOrthogonalCorrectors};",
                  f"    momentumPredictor          {'yes' if params.momentumPredictor else 'no'};"]
    # residualControl optional
    if params.residual_control:
        algo_lines.append("    residualControl")
        algo_lines.append("    {")
        for field, tol in params.residual_control.items():
            algo_lines.append(f"        {field}")
            algo_lines.append("        {")
            algo_lines.append(f"            tolerance       {tol};")
            algo_lines.append("        }")
        algo_lines.append("    }")
    algo_lines.append("}")
    algorithm_block = "\n".join(algo_lines)

    # relaxationFactors section
    relax = ["relaxationFactors", "{", "    fields", "    {",
             f"        p               {params.relaxation_p};",
             "    }",
             "    equations", "    {",
             f"        U               {params.relaxation_U};"]
    if params.relaxation_k is not None:
        relax.append(f"        k               {params.relaxation_k};")
    if params.relaxation_epsilon is not None:
        relax.append(f"        epsilon         {params.relaxation_epsilon};")
    if params.relaxation_omega is not None:
        relax.append(f"        omega           {params.relaxation_omega};")
    relax.append("    }")
    relax.append("}")
    relaxation_block = "\n".join(relax)

    return "\n\n".join([header, solvers_block, algorithm_block, relaxation_block])
