import yaml
from pathlib import Path
from typing import Dict, Any
from base.nozzle.parabolic_nozzle import ParabolicNozzleParams, ParabolicNozzle


class NozzleConfigLoader:
    """Load and parse nozzle configuration from YAML"""

    def __init__(self, config_path: str = "config/nozzle_params.yaml"):
        """
        Initialize nozzle config loader.

        Args:
            config_path: Path to nozzle_params.yaml file.
            Defaults to "config/nozzle_params.yaml".
        """
        self.config_path = Path(config_path)
        self.config = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Returns:
            Dictionary with configuration

        Raises:
            FileNotFoundError: If config file not found.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"Nozzle config loaded from: {self.config_path}")
        return config

    def get_nozzle_config(self) -> Dict[str, Any]:
        """
        Get nozzle configuration section.

        Returns:
            Dictionary with nozzle settings
        """
        return self.config.get('nozzle', {})

    def get_nozzle_type(self) -> str:
        """Get nozzle type"""
        return self.get_nozzle_config().get('type', 'parabolic')

    def get_parabolic_nozzle_params(self) -> ParabolicNozzleParams:
        """
        Parse config and create ParabolicNozzleParams.

        Returns:
            ParabolicNozzleParams object

        Raises:
            ValueError: If nozzle type is not parabolic or params missing
        """
        nozzle_config = self.get_nozzle_config()

        if not nozzle_config:
            raise ValueError("No 'nozzle' section found in config")

        nozzle_type = nozzle_config.get('type', 'parabolic')
        if nozzle_type != 'parabolic':
            raise ValueError(
                f"Config is for '{nozzle_type}' nozzle, not parabolic")

        parabolic_config = nozzle_config.get('parabolic', {})
        length_model = nozzle_config.get('length_model', {})
        point_distribution = nozzle_config.get('point_distribution', {})

        params = ParabolicNozzleParams(
            throat_radius=float(nozzle_config['throat_radius']),
            exit_radius=float(nozzle_config['exit_radius']),
            chamber_radius=float(nozzle_config['chamber_radius']),
            convergent_power=float(
                parabolic_config.get('convergent_power', 0.6)),
            divergent_power=float(parabolic_config.get('divergent_power', 0.8)),
            convergent_length_factor=float(
                length_model.get('convergent_length_factor', 1.5)),
            divergent_length_factor=float(
                length_model.get('divergent_length_factor', 0.8)),
            divergent_half_angle_deg=float(
                length_model.get('divergent_half_angle_deg', 15.0)),
            convergent_fraction=float(
                point_distribution.get('convergent_fraction', 0.4)),
            throat_position=float(nozzle_config.get('throat_position', 0.0))
        )

        print("ParabolicNozzleParams created successfully")
        return params

    def create_nozzle(self) -> ParabolicNozzle:
        """
        Create a ParabolicNozzle object from config.

        Returns:
            ParabolicNozzle object
        """
        params = self.get_parabolic_nozzle_params()
        nozzle = ParabolicNozzle(params)
        print("ParabolicNozzle created successfully")
        return nozzle

    def get_mesh_params(self) -> Dict[str, int]:
        """Get mesh generation parameters"""
        nozzle_config = self.get_nozzle_config()
        mesh_config = nozzle_config.get('mesh', {})
        return {
            'axial_points': mesh_config.get('axial_points', 200),
            'radial_points': mesh_config.get('radial_points', 50)
        }

    def validate_config(self) -> bool:
        """
        Validate nozzle configuration completeness.

        Returns:
            True if config is valid

        Raises:
            ValueError: If required parameters are missing
        """
        nozzle_config = self.get_nozzle_config()

        required_params = [
            'type',
            'throat_radius',
            'exit_radius',
            'chamber_radius'
        ]

        if missing := [
            param for param in required_params if param not in nozzle_config
        ]:
            raise ValueError(f"Missing required parameters: {missing}")

        # Validate physical constraints
        throat_r = nozzle_config['throat_radius']
        exit_r = nozzle_config['exit_radius']
        chamber_r = nozzle_config['chamber_radius']

        if throat_r >= exit_r:
            raise ValueError(
                f"throat_radius ({throat_r}) must be < exit_radius ({exit_r})")

        if throat_r >= chamber_r:
            raise ValueError(
                f"throat_radius ({throat_r}) must be < chamber_radius ({chamber_r})")

        print("Nozzle configuration is valid")
        return True

    def print_config(self):
        """Print nozzle configuration in readable format"""
        print("\n" + "=" * 60)
        print("NOZZLE CONFIGURATION SUMMARY")
        print("=" * 60)

        if nozzle_config := self.get_nozzle_config():
            print(f"\nNozzle type: {nozzle_config.get('type', 'N/A')}")

            print("\nDIMENSIONS")
            print(
                f"  Throat radius:   {nozzle_config.get('throat_radius', 'N/A')} m")
            print(
                f"  Exit radius:     {nozzle_config.get('exit_radius', 'N/A')} m")
            print(
                f"  Chamber radius:  {nozzle_config.get('chamber_radius', 'N/A')} m")

            # Calculate expansion ratio
            if 'throat_radius' in nozzle_config and 'exit_radius' in nozzle_config:
                expansion_ratio = (
                    nozzle_config['exit_radius'] / nozzle_config['throat_radius']) ** 2
                print(f"  Expansion ratio: {expansion_ratio:.2f}")

            if nozzle_config.get('type') == 'parabolic':
                parabolic = nozzle_config.get('parabolic', {})
                print("\nPARABOLIC PARAMETERS")
                print(
                    f"  Convergent power: {parabolic.get('convergent_power', 'N/A')}")
                print(
                    f"  Divergent power:  {parabolic.get('divergent_power', 'N/A')}")

            if mesh := nozzle_config.get('mesh', {}):
                print("\nMESH PARAMETERS")
                print(f"  Axial points:   {mesh.get('axial_points', 'N/A')}")
                print(f"  Radial points:  {mesh.get('radial_points', 'N/A')}")

        print("\n" + "=" * 60 + "\n")


# Helper functions
def load_nozzle_config(
    config_path: str = "config/nozzle_params.yaml"
) -> NozzleConfigLoader:
    """
    Load nozzle configuration file.

    Args:
        config_path: Path to config file. Defaults to "config/nozzle_params.yaml".

    Returns:
        NozzleConfigLoader object
    """
    return NozzleConfigLoader(config_path)


def create_nozzle_from_config(
    config_path: str = "config/nozzle_params.yaml"
) -> ParabolicNozzle:
    """
    Quick function to create nozzle from config file.

    Args:
        config_path: Path to config file. Defaults to "config/nozzle_params.yaml".

    Returns:
        ParabolicNozzle object
    """
    loader = NozzleConfigLoader(config_path)
    return loader.create_nozzle()
