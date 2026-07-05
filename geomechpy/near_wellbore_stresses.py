from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from geomechpy.toolbox import rotate_nev_to_toh, rotate_stress_to_shmax


@dataclass(frozen=True)
class BoreholeWallStresses:
    """Near wellbore stress components on the borehole wall.

    Attributes:
        sigma_rr (npt.NDArray[np.float64]): Radial near wellbore stress component computed at azimuthal positions relative to the borehole axis. Unit: Pressure
        sigma_tt (npt.NDArray[np.float64]): Tangential near wellbore stress component computed at azimuthal positions relative to the borehole axis. Unit: Pressure
        sigma_zz (npt.NDArray[np.float64]): Axial near wellbore stress component computed at azimuthal positions relative to the borehole axis. Unit: Pressure
        sigma_tz (npt.NDArray[np.float64]): Tangential-axial shear stress component at the borehole wall. Unit: Pressure
        sigma_rt (npt.NDArray[np.float64]): Radial-tangential shear stress component at the borehole wall. Unit: Pressure
        sigma_rz (npt.NDArray[np.float64]): Radial-axial shear stress component at the borehole wall. Unit: Pressure
    """

    sigma_rr: npt.NDArray[np.float64]
    sigma_tt: npt.NDArray[np.float64]
    sigma_zz: npt.NDArray[np.float64]
    sigma_tz: npt.NDArray[np.float64]
    sigma_rt: npt.NDArray[np.float64]
    sigma_rz: npt.NDArray[np.float64]


@dataclass(frozen=True)
class PrincipalStresses:
    """Principal stresses derived from the near wellbore stresses on the borehole wall.

    Attributes:
        sigma_1 (npt.NDArray[np.float64]): Maximum principal stress. Unit: Pressure
        sigma_2 (npt.NDArray[np.float64]): Minimum principal stress. Unit: Pressure
        theta_tortuosity (npt.NDArray[np.float64]): Wellbore tortuosity (angle between borehole axis and plane of zero shear stress). Unit: [deg]
    """

    sigma_1: npt.NDArray[np.float64]
    sigma_2: npt.NDArray[np.float64]
    theta_tortuosity: npt.NDArray[np.float64]


class NearWellboreStressesCalculation:
    """Computation of the near wellbore stresses on the borehole wall for any borehole orientation.

    Reference:
        Fjaer, Erling, et al. Petroleum related rock mechanics. Vol. 53. Elsevier, 2008; Chapter 4 eq. 4.83 - 4.92.
        Jaeger, John Conrad, Neville GW Cook, and Robert Zimmerman. Fundamentals of rock mechanics. John Wiley & Sons, 2009; Chapter 2.3, eq. 2.31 - 2.33."""

    @staticmethod
    def calculate_kirsch_borehole_wall_stresses(
        shmin: float,
        shmax: float,
        svert: float,
        pore_pressure: float,
        shmax_azimuth: float,
        mud_pressure: float,
        theta: npt.NDArray[np.float64],
        poisson_ratio_static: float,
        borehole_deviation: float,
        borehole_azimuth: float,
    ) -> BoreholeWallStresses:
        """Compute the near wellbore stresses on the borehole wall for any borehole orientation using the Kirsch solution.

        Reference: Fjaer, Erling, et al. Petroleum related rock mechanics. Vol. 53. Elsevier, 2008; Chapter 4 eq. 4.83 - 4.92.

        Args:
            shmin (float): Minimum horizontal stress magnitude. Unit: Pressure Unit [psi]
            shmax (float): Maximum horizontal stress magnitude. Unit: Pressure Unit [psi]
            svert (float): Vertical stress magnitude. Unit: Pressure Unit [psi]
            pore_pressure (float): Pore pressure. Unit: Pressure Unit [psi]
            shmax_azimuth (float): Direction of the maximum horizontal stress magnitude relative to Geographic NORTH. Unit: [deg]
            mud_pressure (float): Mud pressure inside the borehole. Unit: Pressure Unit [psi]
            theta (npt.NDArray[np.float64]): Azimuthal angles around the borehole circumference measured relative to top of hole (TOH). Unit: [deg]
            poisson_ratio_static (float): Static Poisson's ratio. Unit: unitless
            borehole_deviation (float): Borehole inclination. Unit: [deg]
            borehole_azimuth (float): Borehole azimuth. Unit: [deg]

        Returns:
            BoreholeWallStresses: Dataclass containing the radial, tangential, axial and shear stress components on the borehole wall. See `BoreholeWallStresses` for details. Unit: consistent with input pressure unit
        """
        stress_tensor_nev = rotate_stress_to_shmax(shmin, shmax, svert, shmax_azimuth)
        stress_toh = rotate_nev_to_toh(borehole_deviation, borehole_azimuth, stress_tensor_nev)

        sx0 = stress_toh[0, 0]
        sy0 = stress_toh[1, 1]
        sz0 = stress_toh[2, 2]
        sxy0 = stress_toh[1, 0]
        syz0 = stress_toh[2, 1]
        sxz0 = stress_toh[2, 0]

        theta_rad = np.deg2rad(theta)

        sigma_rr = (mud_pressure - pore_pressure) * np.ones(len(theta))
        sigma_tt = (sx0 + sy0) - 2 * (sx0 - sy0) * np.cos(2 * theta_rad) - 4 * sxy0 * np.sin(2 * theta_rad) - (mud_pressure - pore_pressure)
        sigma_zz = sz0 - poisson_ratio_static * (2 * (sx0 - sy0) * np.cos(2 * theta_rad) + 4 * sxy0 * np.sin(2 * theta_rad))
        sigma_rt = np.zeros(len(theta))
        sigma_tz = 2 * (-sxz0 * np.sin(theta_rad) + syz0 * np.cos(theta_rad))
        sigma_rz = np.zeros(len(theta))

        return BoreholeWallStresses(sigma_rr, sigma_tt, sigma_zz, sigma_tz, sigma_rt, sigma_rz)

    @staticmethod
    def calculate_principal_stresses_analytical(
        sigma_tt: npt.NDArray[np.float64],
        sigma_zz: npt.NDArray[np.float64],
        sigma_tz: npt.NDArray[np.float64],
    ) -> PrincipalStresses:
        """Compute the principal stresses from the near wellbore stresses on the borehole wall.

        Reference: Jaeger, John Conrad, Neville GW Cook, and Robert Zimmerman. Fundamentals of rock mechanics. John Wiley & Sons, 2009; Chapter 2.3, eq. 2.31 - 2.33.

        Args:
            sigma_tt (npt.NDArray[np.float64]): Tangential near wellbore stress component computed at azimuthal positions relative to the borehole axis. Unit: Pressure Unit [psi]
            sigma_zz (npt.NDArray[np.float64]): Axial near wellbore stress component computed at azimuthal positions relative to the borehole axis. Unit: Pressure Unit [psi]
            sigma_tz (npt.NDArray[np.float64]): Tangential-axial shear stress component at the borehole wall. Unit: Pressure Unit [psi]

        Returns:
            PrincipalStresses: Dataclass containing the maximum and minimum principal stresses and the wellbore tortuosity angle. See `PrincipalStresses` for details. Unit: consistent with input pressure unit
        """
        sigma_1 = 0.5 * (sigma_tt + sigma_zz) + 0.5 * np.sqrt((sigma_tt - sigma_zz) ** 2 + 4 * sigma_tz**2)
        sigma_2 = 0.5 * (sigma_tt + sigma_zz) - 0.5 * np.sqrt((sigma_tt - sigma_zz) ** 2 + 4 * sigma_tz**2)
        theta_tortuosity = 0.5 * np.degrees(np.arctan(2 * sigma_tz / (sigma_tt - sigma_zz)))

        return PrincipalStresses(sigma_1, sigma_2, theta_tortuosity)
