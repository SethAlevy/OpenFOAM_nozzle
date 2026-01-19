import numpy as np
from typing import Tuple
from dataclasses import dataclass


@dataclass
class ParabolicNozzleParams:
    """Simple parameters for a parabolic nozzle"""
    throat_radius: float      # Radius at throat (minimum)
    exit_radius: float        # Radius at exit
    chamber_radius: float     # Radius at chamber inlet

    # Optional: control the parabola shape
    convergent_power: float = 0.6   # Power for converging section (0.5-1.0)
    divergent_power: float = 0.8    # Power for diverging section (0.5-1.2)


class ParabolicNozzle:
    """Simple parabolic nozzle generator"""

    def __init__(self, params: ParabolicNozzleParams):
        self.params = params

        # Calculate section lengths (simple estimates)
        self.L_convergent = 1.5 * params.chamber_radius
        self.L_divergent = 0.8 * \
            (params.exit_radius - params.throat_radius) / np.tan(np.deg2rad(15))

    def generate_contour(self, n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate the nozzle contour points (outer wall only)

        Args:
            n_points: Total number of points

        Returns:
            x: Axial coordinates (1D array)
            r: Radial coordinates (1D array) - outer wall
        """
        # Split points between sections (60% divergent, 40% convergent)
        n_conv = int(n_points * 0.4)
        n_div = n_points - n_conv

        # Converging section (from chamber to throat)
        x_conv, r_conv = self._convergent_section(n_conv)

        # Diverging section (from throat to exit)
        x_div, r_div = self._divergent_section(n_div)

        # Combine (skip first point of divergent to avoid duplicate at throat)
        x = np.concatenate([x_conv, x_div[1:]])
        r = np.concatenate([r_conv, r_div[1:]])

        return x, r

    def get_outer_wall(self, n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get outer wall geometry (same as generate_contour)

        Returns:
            x: Axial coordinates
            r: Radial coordinates (positive values only)
        """
        return self.generate_contour(n_points)

    def get_centerline(self, n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get centerline geometry

        Returns:
            x: Axial coordinates (same range as outer wall)
            r: Radial coordinates (all zeros)
        """
        x, _ = self.generate_contour(n_points)
        r = np.zeros_like(x)
        return x, r

    def get_both_sections(self, n_points: int = 100) -> dict:
        """
        Get both outer wall and centerline

        Returns:
            dict with keys:
                'outer_wall': (x, r) tuple for outer wall
                'centerline': (x, r) tuple for centerline
        """
        x_wall, r_wall = self.get_outer_wall(n_points)
        x_center, r_center = self.get_centerline(n_points)

        return {
            'outer_wall': (x_wall, r_wall),
            'centerline': (x_center, r_center)
        }

    def _convergent_section(self, n_points: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate converging section using parabolic curve"""
        # x coordinates (from -L_convergent to 0)
        x = np.linspace(-self.L_convergent, 0, n_points)

        # Normalized position (0 at chamber, 1 at throat)
        t = (x + self.L_convergent) / self.L_convergent

        # Parabolic interpolation from chamber_radius to throat_radius
        r = self.params.chamber_radius - \
            (self.params.chamber_radius - self.params.throat_radius) * \
            t**self.params.convergent_power

        return x, r

    def _divergent_section(self, n_points: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate diverging section using parabolic curve"""
        # x coordinates (from 0 to L_divergent)
        x = np.linspace(0, self.L_divergent, n_points)

        # Normalized position (0 at throat, 1 at exit)
        t = x / self.L_divergent

        # Parabolic interpolation from throat_radius to exit_radius
        r = self.params.throat_radius + \
            (self.params.exit_radius - self.params.throat_radius) * \
            t**self.params.divergent_power

        return x, r

    def plot(self, n_points: int = 100, show_centerline: bool = True):
        """Simple visualization of the nozzle"""
        import matplotlib.pyplot as plt

        x_wall, r_wall = self.get_outer_wall(n_points)

        plt.figure(figsize=(12, 4))
        plt.plot(x_wall, r_wall, 'b-', linewidth=2, label='Outer wall')

        if show_centerline:
            x_center, r_center = self.get_centerline(n_points)
            plt.plot(x_center, r_center, 'k--', linewidth=1,
                     alpha=0.5, label='Centerline')

        plt.axvline(x=0, color='r', linestyle='--', alpha=0.3, label='Throat')

        plt.xlabel('Axial Position (m)')
        plt.ylabel('Radial Position (m)')
        plt.title('Parabolic Nozzle Contour (Half Section)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()


# Example usage
if __name__ == "__main__":
    # Define nozzle dimensions
    params = ParabolicNozzleParams(
        throat_radius=0.05,      # 50 mm
        exit_radius=0.15,        # 150 mm
        chamber_radius=0.075,    # 75 mm
        convergent_power=0.6,    # Smooth convergence
        divergent_power=0.8      # Smooth divergence
    )

    # Create nozzle
    nozzle = ParabolicNozzle(params)

    # Get outer wall only
    x_wall, r_wall = nozzle.get_outer_wall(n_points=200)
    print(f"Outer wall: {len(x_wall)} points")

    # Get centerline only
    x_center, r_center = nozzle.get_centerline(n_points=200)
    print(f"Centerline: {len(x_center)} points, all r={r_center[0]}")

    # Get both
    sections = nozzle.get_both_sections(n_points=200)
    print(f"Both sections returned in dict")

    # Visualize
    nozzle.plot(n_points=200, show_centerline=True)
