import numpy as np
from typing import Tuple, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class SectionParameters:
    """Parameters for a nozzle section"""
    start_x: float  # Starting axial position
    end_x: float    # Ending axial position
    start_r: float  # Starting radius
    end_r: float    # Ending radius
    n_points: int = 50  # Number of points in this section


class NozzleSection(ABC):
    """Base class for nozzle sections"""

    def __init__(self, params: SectionParameters):
        self.params = params

    @abstractmethod
    def get_radius_function(self) -> Callable[[np.ndarray], np.ndarray]:
        """
        Return a function r(x) that describes the section geometry.

        Returns:
            A function that takes x coordinates and returns r coordinates
        """
        pass

    def generate_points(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate discrete points for this section"""
        x = np.linspace(self.params.start_x, self.params.end_x,
                        self.params.n_points)
        r_func = self.get_radius_function()
        r = r_func(x)
        return x, r


class FunctionBasedSection(NozzleSection):
    """Section defined by a user-provided mathematical function"""

    def __init__(self, params: SectionParameters,
                 radius_function: Callable[[np.ndarray], np.ndarray]):
        """
        Args:
            params: Section parameters
            radius_function: Function r(x) that takes x and returns radius
        """
        super().__init__(params)
        self.radius_function = radius_function

    def get_radius_function(self) -> Callable[[np.ndarray], np.ndarray]:
        return self.radius_function


class LinearSection(NozzleSection):
    """Straight conical section"""

    def __init__(self, params: SectionParameters):
        super().__init__(params)
        self.slope = (params.end_r - params.start_r) / \
            (params.end_x - params.start_x)

    def get_radius_function(self) -> Callable[[np.ndarray], np.ndarray]:
        def r_func(x: np.ndarray) -> np.ndarray:
            return self.params.start_r + self.slope * (x - self.params.start_x)
        return r_func


class CircularArcSection(NozzleSection):
    """Circular arc section (e.g., for throat region)"""

    def __init__(self, params: SectionParameters,
                 radius_of_curvature: float,
                 convex: bool = True):
        """
        Args:
            params: Section parameters
            radius_of_curvature: R for the circular arc
            convex: True for convex (outward bulge), False for concave
        """
        super().__init__(params)
        self.R_c = radius_of_curvature
        self.convex = convex

    def get_radius_function(self) -> Callable[[np.ndarray], np.ndarray]:
        # Calculate center of circular arc
        dx = self.params.end_x - self.params.start_x
        dr = self.params.end_r - self.params.start_r

        # Chord length
        chord = np.sqrt(dx**2 + dr**2)

        # Height of arc (sagitta)
        sign = 1 if self.convex else -1
        h = self.R_c - sign * np.sqrt(self.R_c**2 - (chord/2)**2)

        def r_func(x: np.ndarray) -> np.ndarray:
            # Parametric circle equation
            t = (x - self.params.start_x) / dx
            x_local = t * dx

            # Circle centered at appropriate location
            r = self.params.start_r + t * dr + sign * np.sqrt(
                self.R_c**2 - (x_local - dx/2)**2
            ) - sign * np.sqrt(self.R_c**2 - (dx/2)**2)

            return r

        return r_func


class ParabolicSection(NozzleSection):
    """Parabolic section"""

    def __init__(self, params: SectionParameters,
                 curvature: float = 1.0):
        """
        Args:
            params: Section parameters
            curvature: Controls the parabola shape (higher = more curved)
        """
        super().__init__(params)
        self.curvature = curvature

    def get_radius_function(self) -> Callable[[np.ndarray], np.ndarray]:
        def r_func(x: np.ndarray) -> np.ndarray:
            t = (x - self.params.start_x) / \
                (self.params.end_x - self.params.start_x)
            r = self.params.start_r + \
                (self.params.end_r - self.params.start_r) * t**self.curvature
            return r
        return r_func


class HermiteSection(NozzleSection):
    """Hermite interpolation section (smooth with specified slopes at endpoints)"""

    def __init__(self, params: SectionParameters,
                 start_slope: float,
                 end_slope: float):
        """
        Args:
            params: Section parameters
            start_slope: dr/dx at start point
            end_slope: dr/dx at end point
        """
        super().__init__(params)
        self.start_slope = start_slope
        self.end_slope = end_slope

    def get_radius_function(self) -> Callable[[np.ndarray], np.ndarray]:
        dx = self.params.end_x - self.params.start_x

        def r_func(x: np.ndarray) -> np.ndarray:
            t = (x - self.params.start_x) / dx

            # Hermite basis functions
            h00 = 2*t**3 - 3*t**2 + 1
            h10 = t**3 - 2*t**2 + t
            h01 = -2*t**3 + 3*t**2
            h11 = t**3 - t**2

            r = (h00 * self.params.start_r +
                 h10 * dx * self.start_slope +
                 h01 * self.params.end_r +
                 h11 * dx * self.end_slope)

            return r

        return r_func


@dataclass
class NozzleParameters:
    """Overall nozzle geometric parameters"""
    throat_radius: float
    exit_radius: float
    chamber_radius: float
    throat_position: float = 0.0  # Axial position of throat


class Nozzle:
    """Complete nozzle composed of multiple sections"""

    def __init__(self, params: NozzleParameters):
        self.params = params
        self.sections = []

    def add_section(self, section: NozzleSection):
        """Add a section to the nozzle"""
        self.sections.append(section)

    def add_converging_section(self, section: NozzleSection):
        """Add converging section (before throat)"""
        self.sections.insert(0, section)  # Add at beginning

    def add_throat_section(self, section: NozzleSection):
        """Add throat section"""
        # Insert after converging, before diverging
        insert_pos = 1 if len(self.sections) > 0 else 0
        self.sections.insert(insert_pos, section)

    def add_diverging_section(self, section: NozzleSection):
        """Add diverging section (after throat)"""
        self.sections.append(section)

    def generate_contour(self, remove_duplicates: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Generate complete nozzle contour from all sections"""
        x_list = []
        r_list = []

        for section in self.sections:
            x_sec, r_sec = section.generate_points()
            x_list.append(x_sec)
            r_list.append(r_sec)

        # Concatenate all sections
        x = np.concatenate(x_list)
        r = np.concatenate(r_list)

        if remove_duplicates:
            # Remove duplicate points at section boundaries
            unique_indices = np.unique(x, return_index=True)[1]
            x = x[unique_indices]
            r = r[unique_indices]

        return x, r

    def get_full_section(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get both upper and lower halves (for visualization)"""
        x, r = self.generate_contour()
        x_full = np.concatenate([x, x[::-1]])
        r_full = np.concatenate([r, -r[::-1]])
        return x_full, r_full


# Helper functions for common nozzle types

def create_conical_nozzle(params: NozzleParameters,
                          convergent_angle: float = 30.0,
                          divergent_angle: float = 15.0,
                          n_points_per_section: int = 50) -> Nozzle:
    """Create a simple conical nozzle"""

    nozzle = Nozzle(params)

    # Converging section
    theta_conv = np.deg2rad(convergent_angle)
    L_conv = (params.chamber_radius - params.throat_radius) / \
        np.tan(theta_conv)

    conv_params = SectionParameters(
        start_x=params.throat_position - L_conv,
        end_x=params.throat_position,
        start_r=params.chamber_radius,
        end_r=params.throat_radius,
        n_points=n_points_per_section
    )
    nozzle.add_converging_section(LinearSection(conv_params))

    # Diverging section
    theta_div = np.deg2rad(divergent_angle)
    L_div = (params.exit_radius - params.throat_radius) / np.tan(theta_div)

    div_params = SectionParameters(
        start_x=params.throat_position,
        end_x=params.throat_position + L_div,
        start_r=params.throat_radius,
        end_r=params.exit_radius,
        n_points=n_points_per_section
    )
    nozzle.add_diverging_section(LinearSection(div_params))

    return nozzle


def create_bell_nozzle(params: NozzleParameters,
                       percent_bell: float = 80.0,
                       theta_n: float = 30.0,
                       theta_e: float = 8.0,
                       n_points_per_section: int = 50) -> Nozzle:
    """Create a bell (Rao) nozzle"""

    nozzle = Nozzle(params)

    # Converging section (parabolic)
    L_conv = 1.5 * params.chamber_radius

    conv_params = SectionParameters(
        start_x=params.throat_position - L_conv,
        end_x=params.throat_position,
        start_r=params.chamber_radius,
        end_r=params.throat_radius,
        n_points=n_points_per_section
    )
    nozzle.add_converging_section(ParabolicSection(conv_params, curvature=0.6))

    # Throat section (optional circular arc)
    R_t = 0.382 * params.throat_radius
    throat_length = 0.1 * R_t

    throat_params = SectionParameters(
        start_x=params.throat_position,
        end_x=params.throat_position + throat_length,
        start_r=params.throat_radius,
        end_r=params.throat_radius,
        n_points=20
    )
    # Could add throat section if desired

    # Diverging section (Hermite for smooth transition)
    L_ref = (params.exit_radius - params.throat_radius) / \
        np.tan(np.deg2rad(15))
    L_div = (percent_bell / 100.0) * L_ref

    div_params = SectionParameters(
        start_x=params.throat_position,
        end_x=params.throat_position + L_div,
        start_r=params.throat_radius,
        end_r=params.exit_radius,
        n_points=n_points_per_section * 2
    )

    nozzle.add_diverging_section(
        HermiteSection(div_params,
                       start_slope=np.tan(np.deg2rad(theta_n)),
                       end_slope=np.tan(np.deg2rad(theta_e)))
    )

    return nozzle


def create_custom_nozzle(params: NozzleParameters,
                         converging_func: Callable[[np.ndarray], np.ndarray],
                         diverging_func: Callable[[np.ndarray], np.ndarray],
                         throat_func: Optional[Callable[[
                             np.ndarray], np.ndarray]] = None,
                         n_points_per_section: int = 50) -> Nozzle:
    """
    Create a nozzle from custom mathematical functions

    Args:
        params: Nozzle parameters
        converging_func: Function r(x) for converging section
        diverging_func: Function r(x) for diverging section
        throat_func: Optional function r(x) for throat section
        n_points_per_section: Points per section

    Example:
        # Exponential converging section
        def conv_func(x):
            return throat_radius + (chamber_radius - throat_radius) * np.exp(x / L_conv)
    """

    nozzle = Nozzle(params)

    # Auto-calculate reasonable section lengths if not specified
    L_conv = 1.5 * params.chamber_radius
    L_div = 0.8 * (params.exit_radius - params.throat_radius) / \
        np.tan(np.deg2rad(15))

    # Converging section
    conv_params = SectionParameters(
        start_x=params.throat_position - L_conv,
        end_x=params.throat_position,
        start_r=params.chamber_radius,
        end_r=params.throat_radius,
        n_points=n_points_per_section
    )
    nozzle.add_converging_section(
        FunctionBasedSection(conv_params, converging_func))

    # Throat section (optional)
    if throat_func is not None:
        L_throat = 0.1 * params.throat_radius
        throat_params = SectionParameters(
            start_x=params.throat_position,
            end_x=params.throat_position + L_throat,
            start_r=params.throat_radius,
            end_r=params.throat_radius,
            n_points=20
        )
        nozzle.add_throat_section(
            FunctionBasedSection(throat_params, throat_func))

    # Diverging section
    div_start = params.throat_position + (L_throat if throat_func else 0)
    div_params = SectionParameters(
        start_x=div_start,
        end_x=div_start + L_div,
        start_r=params.throat_radius,
        end_r=params.exit_radius,
        n_points=n_points_per_section
    )
    nozzle.add_diverging_section(
        FunctionBasedSection(div_params, diverging_func))

    return nozzle
