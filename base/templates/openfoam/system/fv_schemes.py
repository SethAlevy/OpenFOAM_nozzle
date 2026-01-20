from dataclasses import dataclass
from typing import Optional


@dataclass
class FvSchemesParams:
    """Parameters for fvSchemes file"""

    # Time schemes
    time_scheme: str = "Euler"

    # Gradient schemes
    default_grad: str = "Gauss linear"
    grad_U: Optional[str] = None
    grad_p: Optional[str] = None

    # Divergence schemes
    default_div: str = "none"
    div_phi_U: str = "Gauss linearUpwind grad(U)"
    div_phi_k: Optional[str] = None
    div_phi_epsilon: Optional[str] = None
    div_phi_omega: Optional[str] = None
    div_rho_phi_U: Optional[str] = None
    div_rho_phi_K: Optional[str] = None
    div_phi_K: Optional[str] = None

    # Laplacian schemes
    default_laplacian: str = "Gauss linear corrected"
    laplacian_nu_U: Optional[str] = None
    laplacian_DkEff_k: Optional[str] = None
    laplacian_DepsilonEff_epsilon: Optional[str] = None
    laplacian_DomegaEff_omega: Optional[str] = None

    # Interpolation schemes
    default_interpolation: str = "linear"
    interpolate_U: Optional[str] = None

    # Surface normal gradient
    default_sn_grad: str = "corrected"

    # Flux scheme (for compressible solvers)
    flux_scheme: Optional[str] = "Kurganov"


def generate_fv_schemes(params: FvSchemesParams) -> str:
    """
    Generate OpenFOAM fvSchemes file.

    Args:
        params: FvSchemesParams object with numerical scheme settings

    Returns:
        Formatted fvSchemes file as string
    """

    # Build ddtSchemes section
    ddt_schemes = f"""ddtSchemes
{{
    default         {params.time_scheme};
}}"""

    # Build gradSchemes section
    grad_schemes = f"""gradSchemes
{{
    default         {params.default_grad};"""

    if params.grad_U:
        grad_schemes += f"\n    grad(U)         {params.grad_U};"
    if params.grad_p:
        grad_schemes += f"\n    grad(p)         {params.grad_p};"

    grad_schemes += "\n}"

    # Build divSchemes section
    div_schemes = f"""divSchemes
{{
    default         {params.default_div};
    div(phi,U)      {params.div_phi_U};"""

    if params.div_phi_k:
        div_schemes += f"\n    div(phi,k)      {params.div_phi_k};"
    if params.div_phi_epsilon:
        div_schemes += f"\n    div(phi,epsilon) {params.div_phi_epsilon};"
    if params.div_phi_omega:
        div_schemes += f"\n    div(phi,omega)  {params.div_phi_omega};"
    if params.div_rho_phi_U:
        div_schemes += f"\n    div(phiv,p)     {params.div_rho_phi_U};"
    if params.div_rho_phi_K:
        div_schemes += f"\n    div(phi,K)      {params.div_rho_phi_K};"
    if params.div_phi_K:
        div_schemes += f"\n    div(phi,K)      {params.div_phi_K};"

    div_schemes += "\n}"

    # Build laplacianSchemes section
    laplacian_schemes = f"""laplacianSchemes
{{
    default         {params.default_laplacian};"""

    if params.laplacian_nu_U:
        laplacian_schemes += f"\n    laplacian(nu,U) {params.laplacian_nu_U};"
    if params.laplacian_DkEff_k:
        laplacian_schemes += f"\n    laplacian(DkEff,k) {params.laplacian_DkEff_k};"
    if params.laplacian_DepsilonEff_epsilon:
        laplacian_schemes += f"\n    laplacian(DepsilonEff,epsilon) {params.laplacian_DepsilonEff_epsilon};"
    if params.laplacian_DomegaEff_omega:
        laplacian_schemes += f"\n    laplacian(DomegaEff,omega) {params.laplacian_DomegaEff_omega};"

    laplacian_schemes += "\n}"

    # Build interpolationSchemes section
    interpolation_schemes = f"""interpolationSchemes
{{
    default         {params.default_interpolation};"""

    if params.interpolate_U:
        interpolation_schemes += f"\n    interpolate(U)  {params.interpolate_U};"

    interpolation_schemes += "\n}"

    # Build snGradSchemes section
    sn_grad_schemes = f"""snGradSchemes
{{
    default         {params.default_sn_grad};
}}"""

    # Build fluxRequired section (optional, for compressible)
    flux_required = """fluxRequired
{
    default         no;
    p;
}"""

    # Assemble full file
    content = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}}

{ddt_schemes}

{grad_schemes}

{div_schemes}

{laplacian_schemes}

{interpolation_schemes}

{sn_grad_schemes}

{flux_required}
"""

    # Add flux scheme for compressible solvers
    if params.flux_scheme:
        content += f"""
fluxScheme      {params.flux_scheme};
"""

    return content


# Pre-defined scenarios
def incompressible_simple() -> FvSchemesParams:
    """Standard schemes for incompressible SIMPLE"""
    return FvSchemesParams(
        time_scheme="steadyState",
        default_grad="Gauss linear",
        default_div="none",
        div_phi_U="Gauss linearUpwind grad(U)",
        div_phi_k="Gauss limitedLinear 1",
        div_phi_epsilon="Gauss limitedLinear 1",
        default_laplacian="Gauss linear corrected",
        default_interpolation="linear",
        default_sn_grad="corrected",
        flux_scheme=None
    )


def compressible_supersonic() -> FvSchemesParams:
    """Schemes for compressible supersonic flow (rhoCentralFoam)"""
    return FvSchemesParams(
        time_scheme="Euler",
        default_grad="Gauss linear",
        default_div="none",
        div_phi_U="Gauss linearUpwind grad(U)",
        div_rho_phi_U="Gauss linearUpwind grad(U)",
        div_phi_K="Gauss linear",
        default_laplacian="Gauss linear corrected",
        default_interpolation="linear",
        default_sn_grad="corrected",
        flux_scheme="Kurganov"
    )


def transient_pimple() -> FvSchemesParams:
    """Schemes for transient incompressible PIMPLE"""
    return FvSchemesParams(
        time_scheme="backward",
        default_grad="Gauss linear",
        default_div="none",
        div_phi_U="Gauss linearUpwind grad(U)",
        div_phi_k="Gauss limitedLinear 1",
        div_phi_epsilon="Gauss limitedLinear 1",
        default_laplacian="Gauss linear corrected",
        default_interpolation="linear",
        default_sn_grad="corrected",
        flux_scheme=None
    )
