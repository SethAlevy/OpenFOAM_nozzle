from base.config_loader.nozzle_config import NozzleConfigLoader
from base.nozzle.parabolic_nozzle import ParabolicNozzle


class NozzleBuilder:
    """Top-level orchestrator for nozzle creation from config files"""

    def __init__(
        self,
        nozzle_config_path: str = "config/nozzle_params.yaml",
        simulation_config_path: str = "config/simulation_config.yaml"
    ):
        self.nozzle_loader = NozzleConfigLoader(nozzle_config_path)

        self.nozzle_loader.validate_config()

    def build(self) -> ParabolicNozzle:
        """Create and return a ParabolicNozzle from config"""
        return self.nozzle_loader.create_nozzle()

    def get_n_points(self) -> int:
        """Get axial mesh resolution from nozzle config"""
        return self.nozzle_loader.get_mesh_params()["axial_points"]

    def print_summary(self):
        self.nozzle_loader.print_config()

    def run(self, plot: bool = True):
        """Build nozzle, print geometry info and optionally plot"""
        self.print_summary()

        nozzle = self.build()
        n_points = self.get_n_points()

        if plot:
            nozzle.plot(n_points=n_points, show_centerline=True)

        return nozzle
