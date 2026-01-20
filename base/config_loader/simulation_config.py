import yaml
from pathlib import Path
from typing import Dict, Any
from base.templates.openfoam.control_dict import ControlDictParams, SolverType


class ConfigLoader:
    """Load and parse simulation configuration from YAML"""

    def __init__(self, config_path: str = "config/simulation_config.yaml"):
        """
        Initialize config loader.

        Args:
            config_path: Path to simulation_config.yaml file
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
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✓ Config loaded from: {self.config_path}")
        return config

    def get_project_info(self) -> Dict[str, str]:
        """
        Get project information.

        Returns:
            Dictionary with project details
        """
        return self.config.get('project', {})

    def get_controls_config(self) -> Dict[str, Any]:
        """
        Get controls configuration section (controlDict parameters).

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
        print("✓ ControlDictParams created successfully")
        return params

    def get_fv_schemes_params(self) -> 'FvSchemesParams':
        """
        Parse numerical schemes config and create FvSchemesParams.

        Returns:
            FvSchemesParams object
        """
        from base.templates.openfoam.fv_schemes import FvSchemesParams

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

        print("✓ FvSchemesParams created successfully")
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
        from base.templates.openfoam.fv_solution import FvSolutionParams, LinearSolverParams

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

    def get_block_mesh_params(self) -> 'BlockMeshParams':
        from base.templates.openfoam.block_mesh import BlockMeshParams
        bm = self.config.get('block_mesh', {}) or {}
        return BlockMeshParams(
            wedge_angle_deg=float(bm.get('wedge_angle_deg', 5.0)),
            n_axial=int(bm.get('n_axial', 200)),
            n_radial=int(bm.get('n_radial', 50)),
            axial_grading=float(bm.get('axial_grading', 1.0)),
            radial_grading=float(bm.get('radial_grading', 1.0)),
            inlet_patch=bm.get('inlet_patch', 'inlet'),
            outlet_patch=bm.get('outlet_patch', 'outlet'),
            wall_patch=bm.get('wall_patch', 'wall'),
            wedge0_patch=bm.get('wedge0_patch', 'wedge0'),
            wedge1_patch=bm.get('wedge1_patch', 'wedge1'),
            convert_to_meters=float(bm.get('convert_to_meters', 1.0)),
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

        # Validate controls section
        controls_config = self.get_controls_config()
        if not controls_config:
            errors.append("Missing 'controls' section")
        else:
            required_controls = [
                'application',
                'start_time',
                'end_time',
                'delta_t',
                'write_interval'
            ]
            missing_controls = [
                param for param in required_controls if param not in controls_config]
            if missing_controls:
                errors.append(
                    f"Missing required controls parameters: {missing_controls}")

        # Validate numerical_schemes section
        schemes_config = self.get_numerical_schemes_config()
        if not schemes_config:
            errors.append("Missing 'numerical_schemes' section")
        else:
            required_schemes = [
                'time_scheme',
                'default_grad',
                'default_div',
                'default_laplacian'
            ]
            missing_schemes = [
                param for param in required_schemes if param not in schemes_config]
            if missing_schemes:
                errors.append(
                    f"Missing required numerical_schemes parameters: {missing_schemes}")

        # Validate project section (optional but recommended)
        project_config = self.get_project_info()
        if not project_config:
            print("⚠ Warning: No 'project' section found (optional)")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" +
                             "\n".join(f"  - {e}" for e in errors))

        print(f"✓ Configuration is valid")
        return True

    def print_config(self):
        """Print full configuration in readable format"""
        print("\n" + "="*60)
        print("SIMULATION CONFIGURATION SUMMARY")
        print("="*60)

        # Project info
        project = self.get_project_info()
        if project:
            print("\n[PROJECT]")
            for key, value in project.items():
                print(f"  {key}: {value}")
        else:
            print("\n[PROJECT]")
            print("  (not configured)")

        # Controls config
        controls = self.get_controls_config()
        if controls:
            print("\n[CONTROLS]")
            for key, value in controls.items():
                print(f"  {key}: {value}")
        else:
            print("\n[CONTROLS]")
            print("  (not configured)")

        # Numerical schemes config
        schemes = self.get_numerical_schemes_config()
        if schemes:
            print("\n[NUMERICAL SCHEMES]")

            # Time schemes
            if 'time_scheme' in schemes:
                print(f"\n  Time Discretization:")
                print(f"    {schemes['time_scheme']}")

            # Gradient schemes
            grad_keys = [k for k in schemes.keys() if 'grad' in k.lower()]
            if grad_keys:
                print(f"\n  Gradient Schemes:")
                for key in grad_keys:
                    print(f"    {key}: {schemes[key]}")

            # Divergence schemes
            div_keys = [k for k in schemes.keys() if 'div' in k.lower()]
            if div_keys:
                print(f"\n  Divergence Schemes:")
                for key in div_keys:
                    print(f"    {key}: {schemes[key]}")

            # Laplacian schemes
            laplacian_keys = [
                k for k in schemes.keys() if 'laplacian' in k.lower()]
            if laplacian_keys:
                print(f"\n  Laplacian Schemes:")
                for key in laplacian_keys:
                    print(f"    {key}: {schemes[key]}")

            # Interpolation schemes
            interp_keys = [
                k for k in schemes.keys() if 'interpolat' in k.lower()]
            if interp_keys:
                print(f"\n  Interpolation Schemes:")
                for key in interp_keys:
                    print(f"    {key}: {schemes[key]}")

            # Other schemes
            other_keys = ['default_sn_grad', 'flux_scheme']
            remaining = [k for k in schemes.keys() if k in other_keys]
            if remaining:
                print(f"\n  Other Schemes:")
                for key in remaining:
                    print(f"    {key}: {schemes[key]}")
        else:
            print("\n[NUMERICAL SCHEMES]")
            print("  (not configured)")

        # Solver settings
        solver_settings = self.get_solver_settings_config()
        if solver_settings:
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
        else:
            print("\n[SOLVER SETTINGS]")
            print("  (not configured)")

        print("\n" + "="*60 + "\n")


def load_config(config_path: str = "config/simulation_config.yaml") -> ConfigLoader:
    """
    Load configuration file.

    Args:
        config_path: Path to config file

    Returns:
        ConfigLoader object
    """
    return ConfigLoader(config_path)
