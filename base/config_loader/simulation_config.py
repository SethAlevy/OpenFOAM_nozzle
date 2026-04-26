import yaml
from pathlib import Path
from typing import Dict, Any

from base.templates.openfoam.system.control_dict import ControlDictParams, SolverType
from base.templates.openfoam.system.fv_schemes import FvSchemesParams
from base.templates.openfoam.system.fv_solution import FvSolutionParams, LinearSolverParams
from base.templates.openfoam.system.block_mesh import BlockMeshParams, BoundaryLayerParams
from base.templates.openfoam.constant.turbulence_properties import (
    TurbulencePropertiesParams, TurbulenceModel, RASModel
)
from base.templates.openfoam.constant.thermophysical_properties import (
    ThermophysicalPropertiesParams, ThermoType, EquationOfState,
    ThermoModel, TransportModel
)


class ConfigLoader:
    """Load and parse simulation configuration from YAML"""

    def __init__(self, config_path: str = "config/simulation_config.yaml"):
        """
        Initialize config loader.

        Args:
            config_path: Path to simulation_config.yaml file.
            Defaults to "config/simulation_config.yaml".
        """
        self.config_path = Path(config_path)
        self.config = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Returns:
            Dictionary with configuration

        Raises:
            FileNotFoundError: If config file not found
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"Config loaded from: {self.config_path}")
        return config

    def get_controls_config(self) -> Dict[str, Any]:
        """
        Get simulation controls configuration section (controlDict parameters).

        Returns:
            Dictionary with control settings
        """
        return self.config.get('controls', {})

    def get_numerical_schemes_config(self) -> Dict[str, Any]:
        """
        Get numerical schemes configuration section.

        Returns:
            Dictionary with numerical schemes settings
        """
        return self.config.get('numerical_schemes', {})

    def get_control_dict_params(self) -> ControlDictParams:
        """
        Parse controls config and create ControlDictParams.

        Returns:
            ControlDictParams object
        """
        controls = self.get_controls_config()

        if not controls:
            raise ValueError("No 'controls' section found in config")

        params = ControlDictParams(
            application=SolverType(controls['application']),
            start_time=float(controls.get('start_time', 0)),
            end_time=float(controls['end_time']),
            delta_t=float(controls['delta_t']),
            write_interval=int(controls['write_interval']),
            write_format=controls.get('write_format', 'ascii'),
            write_precision=int(controls.get('write_precision', 6)),
            write_compression=controls.get('write_compression', 'off'),
            time_format=controls.get('time_format', 'general'),
            time_precision=int(controls.get('time_precision', 6)),
            purge_write=int(controls.get('purge_write', 0)),
        )
        print("ControlDictParams created successfully")
        return params

    def get_fv_schemes_params(self) -> 'FvSchemesParams':
        """
        Parse numerical schemes config and create FvSchemesParams.

        Returns:
            FvSchemesParams object
        """

        schemes = self.get_numerical_schemes_config()

        if not schemes:
            raise ValueError("No 'numerical_schemes' section found in config")

        params = FvSchemesParams(
            time_scheme=schemes.get('time_scheme', 'Euler'),
            default_grad=schemes.get('default_grad', 'Gauss linear'),
            grad_U=schemes.get('grad_U'),
            grad_p=schemes.get('grad_p'),
            default_div=schemes.get('default_div', 'none'),
            div_phi_U=schemes.get('div_phi_U', 'Gauss linearUpwind grad(U)'),
            div_phi_k=schemes.get('div_phi_k'),
            div_phi_epsilon=schemes.get('div_phi_epsilon'),
            div_phi_omega=schemes.get('div_phi_omega'),
            div_rho_phi_U=schemes.get('div_rho_phi_U'),
            div_rho_phi_K=schemes.get('div_rho_phi_K'),
            div_phi_K=schemes.get('div_phi_K'),
            default_laplacian=schemes.get(
                'default_laplacian', 'Gauss linear corrected'),
            laplacian_nu_U=schemes.get('laplacian_nu_U'),
            laplacian_DkEff_k=schemes.get('laplacian_DkEff_k'),
            laplacian_DepsilonEff_epsilon=schemes.get(
                'laplacian_DepsilonEff_epsilon'),
            laplacian_DomegaEff_omega=schemes.get('laplacian_DomegaEff_omega'),
            default_interpolation=schemes.get(
                'default_interpolation', 'linear'),
            interpolate_U=schemes.get('interpolate_U'),
            default_sn_grad=schemes.get('default_sn_grad', 'corrected'),
            flux_scheme=schemes.get('flux_scheme')
        )

        print("FvSchemesParams created successfully")
        return params

    def get_solver_settings_config(self) -> Dict[str, Any]:
        """
        Get solver settings configuration section.

        Returns:
            Dictionary with solver settings
        """
        return self.config.get('solver_settings', {})

    def get_fv_solution_params(self) -> 'FvSolutionParams':
        """
        Parse solver settings config and create FvSolutionParams.

        Returns:
            FvSolutionParams object
        """

        cfg = self.get_solver_settings_config()
        if not cfg:
            raise ValueError("No 'solver_settings' section found in config")

        solvers = cfg.get('solvers', {})

        def to_lin(name: str) -> LinearSolverParams:
            s = solvers.get(name, {})
            return LinearSolverParams(
                solver=s.get('solver', 'PBiCG'),
                tolerance=float(s.get('tolerance', 1e-6)),
                relTol=float(s.get('relTol', 0.0)),
                preconditioner=s.get('preconditioner'),
                smoother=s.get('smoother'),
            )

        relax = cfg.get('relaxation_factors', {})
        residual_control = cfg.get('residual_control')

        return FvSolutionParams(
            p=to_lin('p'),
            U=to_lin('U'),

            k=to_lin('k') if 'k' in solvers else None,
            epsilon=to_lin('epsilon') if 'epsilon' in solvers else None,
            omega=to_lin('omega') if 'omega' in solvers else None,

            algorithm=cfg.get('algorithm', 'PIMPLE'),
            nCorrectors=int(cfg.get('n_correctors', 2)),
            nNonOrthogonalCorrectors=int(
                cfg.get('n_non_orthogonal_correctors', 1)),
            momentumPredictor=bool(cfg.get('momentum_predictor', True)),

            relaxation_p=float(relax.get('p', 0.3)),
            relaxation_U=float(relax.get('U', 0.7)),
            relaxation_k=float(relax.get('k', 0.7)) if 'k' in relax else None,
            relaxation_epsilon=float(
                relax.get('epsilon', 0.7)) if 'epsilon' in relax else None,
            relaxation_omega=float(
                relax.get('omega')) if 'omega' in relax else None,
            residual_control=residual_control,
        )

    def get_block_mesh_params(self) -> BlockMeshParams:
        bm = self.config.get("block_mesh", {})
        bl = bm.get("boundary_layer", {})

        return BlockMeshParams(
            wedge_angle_deg=float(bm.get("wedge_angle_deg", 5.0)),
            n_axial=int(bm.get("n_axial", 200)),
            n_radial=int(bm.get("n_radial", 50)),
            axial_grading=float(bm.get("axial_grading", 1.0)),
            radial_grading=float(bm.get("radial_grading", 1.0)),
            uniform_axial_spacing=bool(bm.get("uniform_axial_spacing", True)),
            inlet_patch=bm.get("inlet_patch", "inlet"),
            outlet_patch=bm.get("outlet_patch", "outlet"),
            wall_patch=bm.get("wall_patch", "wall"),
            wedge0_patch=bm.get("wedge0_patch", "wedge0"),
            wedge1_patch=bm.get("wedge1_patch", "wedge1"),
            boundary_layer=BoundaryLayerParams(
                enabled=bool(bl.get("enabled", False)),
                n_layers=bl.get("n_layers"),
                expansion_ratio=bl.get("expansion_ratio"),
                first_layer_thickness=bl.get("first_layer_thickness"),
            ),
        )

    def get_constant_config(self) -> Dict[str, Any]:
        """Get constant directory configuration"""
        return self.config.get('constant', {})

    def get_turbulence_properties_params(self):
        const = self.get_constant_config()
        turb = const.get('turbulence', {})

        return TurbulencePropertiesParams(
            simulation_type=TurbulenceModel(
                turb.get('simulation_type', 'RAS')),
            ras_model=RASModel(turb.get('ras_model', 'kEpsilon')),
            turbulence=bool(turb.get('turbulence', True)),
            print_coeffs=bool(turb.get('print_coeffs', True))
        )

    def get_thermophysical_properties_params(self):
        const = self.get_constant_config()
        thermo = const.get('thermophysical', {})

        return ThermophysicalPropertiesParams(
            thermo_type=ThermoType(thermo.get('thermo_type', 'hePsiThermo')),
            mixture=thermo.get('mixture', 'pureMixture'),
            transport=TransportModel(thermo.get('transport', 'sutherland')),
            thermo=ThermoModel(thermo.get('thermo', 'janaf')),
            equation_of_state=EquationOfState(
                thermo.get('equation_of_state', 'perfectGas')),
            mol_weight=float(thermo.get('mol_weight', 28.96)),
            Cp=float(thermo.get('Cp', 1005.0)),
            Hf=float(thermo.get('Hf', 0.0)),
            mu=float(thermo.get('mu', 1.81e-5)),
            Ts=float(thermo.get('Ts', 110.4)),
            Pr=float(thermo.get('Pr', 0.7))
        )

    def validate_config(self) -> bool:
        """
        Validate entire configuration completeness.

        Returns:
            True if config is valid

        Raises:
            ValueError: If required parameters are missing
        """
        errors = []

        if controls_config := self.get_controls_config():
            required_controls = [
                'application',
                'start_time',
                'end_time',
                'delta_t',
                'write_interval'
            ]
            if missing_controls := [
                param
                for param in required_controls
                if param not in controls_config
            ]:
                errors.append(
                    f"Missing required controls parameters: {missing_controls}")

        else:
            errors.append("Missing 'controls' section")

        if schemes_config := self.get_numerical_schemes_config():
            required_schemes = [
                'time_scheme',
                'default_grad',
                'default_div',
                'default_laplacian'
            ]
            if missing_schemes := [
                param for param in required_schemes if param not in schemes_config
            ]:
                errors.append(
                    f"Missing required numerical_schemes parameters: {missing_schemes}")

        else:
            errors.append("Missing 'numerical_schemes' section")

        if errors:
            raise ValueError("Configuration validation failed:\n"
                             + "\n".join(f"  - {e}" for e in errors))

        print("Configuration is valid")
        return True

    def print_config(self):    # sourcery skip: low-code-quality
        """Print full configuration in readable format"""
        print("\n" + "=" * 60)
        print("SIMULATION CONFIGURATION SUMMARY")
        print("=" * 60)

        if controls := self.get_controls_config():
            print("\nCONTROLS")
            for key, value in controls.items():
                print(f"  {key}: {value}")

        if schemes := self.get_numerical_schemes_config():
            print("\nNUMERICAL SCHEMES")

            if 'time_scheme' in schemes:
                print("\n  Time Discretization:")
                print(f"    {schemes['time_scheme']}")

            if grad_keys := [k for k in schemes.keys() if 'grad' in k.lower()]:
                print("\n  Gradient Schemes:")
                for key in grad_keys:
                    print(f"    {key}: {schemes[key]}")

            if div_keys := [k for k in schemes.keys() if 'div' in k.lower()]:
                print("\n  Divergence Schemes:")
                for key in div_keys:
                    print(f"    {key}: {schemes[key]}")

            if laplacian_keys := [
                k for k in schemes.keys() if 'laplacian' in k.lower()
            ]:
                print("\n  Laplacian Schemes:")
                for key in laplacian_keys:
                    print(f"    {key}: {schemes[key]}")

            if interp_keys := [
                k for k in schemes.keys() if 'interpolat' in k.lower()
            ]:
                print("\n  Interpolation Schemes:")
                for key in interp_keys:
                    print(f"    {key}: {schemes[key]}")

            # Other schemes
            other_keys = ['default_sn_grad', 'flux_scheme']
            if remaining := [k for k in schemes.keys() if k in other_keys]:
                print("\n  Other Schemes:")
                for key in remaining:
                    print(f"    {key}: {schemes[key]}")

        if solver_settings := self.get_solver_settings_config():
            print("\n[SOLVER SETTINGS]")
            for key, value in solver_settings.items():
                if key == "solvers":
                    print("  Solvers:")
                    for solver_name, solver_params in value.items():
                        print(f"    {solver_name}:")
                        for param_key, param_value in solver_params.items():
                            print(f"      {param_key}: {param_value}")
                else:
                    print(f"  {key}: {value}")

        print("\n" + "=" * 60 + "\n")


def load_config(config_path: str = "config/simulation_config.yaml") -> ConfigLoader:
    """
    Load configuration file.

    Args:
        config_path: Path to config file

    Returns:
        ConfigLoader object
    """
    return ConfigLoader(config_path)
