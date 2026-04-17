import numpy as np
from typing import Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class ParabolicNozzleParams:
    """Simple parameters for a parabolic nozzle"""
    throat_radius: float      # Radius at throat (minimum)
    exit_radius: float        # Radius at exit
    chamber_radius: float     # Radius at chamber inlet

    # Optional: control the parabola shape
    convergent_power: float   # Power for converging section (0.5-1.0)
    divergent_power: float    # Power for diverging section (0.5-1.2)

    # Geometry model parameters (moved from hardcoded values)
    convergent_length_factor: float   # e.g. 1.5
    divergent_length_factor: float    # e.g. 0.8
    divergent_half_angle_deg: float   # e.g. 15.0
    convergent_fraction: float        # e.g. 0.4
    throat_position: float            # axial position of throat


class ParabolicNozzle:
    """Simple parabolic nozzle generator"""

    def __init__(self, params: ParabolicNozzleParams):
        self.params = params

        self.length_convergent = params.convergent_length_factor * params.chamber_radius
        self.length_divergent = params.divergent_length_factor * \
            (params.exit_radius - params.throat_radius) / np.tan(
                np.deg2rad(params.divergent_half_angle_deg)
            )

    def generate_contour(self, n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate the nozzle contour points (outer wall only)

        Args:
            n_points: Total number of points

        Returns:
            x: Axial coordinates (1D array)
            r: Radial coordinates (1D array) - outer wall
        """
        n_conv = int(n_points * self.params.convergent_fraction)
        n_div = n_points - n_conv + 1

        x_conv, r_conv = self._convergent_section(n_conv)
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
        x_start = self.params.throat_position - self.length_convergent
        x_end = self.params.throat_position
        x = np.linspace(x_start, x_end, n_points)

        normalized_position = (x - x_start) / (x_end - x_start)

        # Parabolic interpolation from chamber_radius to throat_radius
        r = self.params.chamber_radius - \
            (self.params.chamber_radius - self.params.throat_radius) * \
            normalized_position**self.params.convergent_power
        return x, r

    def _divergent_section(self, n_points: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate diverging section using parabolic curve"""
        x_start = self.params.throat_position
        x_end = self.params.throat_position + self.length_divergent
        x = np.linspace(x_start, x_end, n_points)

        normalized_position = (x - x_start) / (x_end - x_start)

        # Parabolic interpolation from throat_radius to exit_radius
        r = self.params.throat_radius + \
            (self.params.exit_radius - self.params.throat_radius) * \
            normalized_position**self.params.divergent_power
        return x, r

    def plot(self, n_points: int = 100, show_centerline: bool = True) -> None:
        """
        Simple visualization of the nozzle
        
        args:
            n_points: Number of points to generate for smooth curve
            show_centerline: Whether to plot the centerline as well
        """

        x_wall, r_wall = self.get_outer_wall(n_points)

        plt.figure(figsize=(12, 4))
        plt.plot(x_wall, r_wall, 'b-', linewidth=2, label='Outer wall')

        if show_centerline:
            x_center, r_center = self.get_centerline(n_points)
            plt.plot(x_center, r_center, 'k--', linewidth=1,
                     alpha=0.5, label='Centerline')

        plt.axvline(
            x=self.params.throat_position,
            color='r',
            linestyle='--',
            alpha=0.3,
            label='Throat')

        plt.xlabel('Axial Position (m)')
        plt.ylabel('Radial Position (m)')
        plt.title('Parabolic Nozzle Contour (Half Section)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()
