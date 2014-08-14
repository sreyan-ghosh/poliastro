# coding: utf-8
"""Orbital maneuvers.

"""

import numpy as np

from astropy import units as u
u.one = u.dimensionless_unscaled  # astropy #1980

from poliastro.util import check_units


class Maneuver(object):
    """Class to represent a Maneuver.

    """
    def __init__(self, *impulses):
        """Constructor.

        Parameters
        ----------
        impulses : list
            List of pairs (delta_time, delta_velocity)

        Notes
        -----
        TODO: Fix docstring, \*args convention

        """
        self.impulses = impulses
        self._dts, self._dvs = zip(*impulses)
        u_times = check_units(self._dts, (u.s,))
        u_dvs = check_units(self._dvs, (u.m / u.s,))
        if not u_times or not u_dvs:
            raise u.UnitsError("Units must be consistent")
        try:
            if not all(len(dv) == 3 for dv in self._dvs):
                raise TypeError
        except TypeError:
            raise ValueError("Delta-V must be three dimensions vectors")

    @classmethod
    def impulse(cls, dv):
        """Single impulse at current time.

        """
        return cls((0 * u.s, dv))

    @classmethod
    def hohmann(cls, ss_i, r_f):
        """Compute a Hohmann transfer between two circular orbits.

        """
        # TODO: Check if circular?
        r_i = ss_i.a
        v_i = ss_i.v
        k = ss_i.attractor.k
        R = r_f / r_i
        dv_a = (np.sqrt(2 * R / (1 + R)) - 1) * v_i
        dv_b = (1 - np.sqrt(2 / (1 + R))) / np.sqrt(R) * v_i
        t_trans = np.pi * np.sqrt((r_i * (1 + R) / 2) ** 3 / k)
        return cls((0 * u.s, dv_a), (t_trans, dv_b))

    @classmethod
    def bielliptic(cls, ss_i, r_b, r_f):
        """Compute a bielliptic transfer between two circular orbits.

        """
        r_i = ss_i.a
        v_i = ss_i.v
        k = ss_i.attractor.k
        R = r_f / r_i
        Rs = r_b / r_i
        dv_a = (np.sqrt(2 * Rs / (1 + Rs)) - 1) * v_i
        dv_b = np.sqrt(2 / Rs) * (np.sqrt(1 / (1 + Rs / R)) -
                                  np.sqrt(1 / (1 + Rs))) * v_i
        dv_c = (np.sqrt(2 * Rs / (R + Rs)) - 1) / np.sqrt(R) * v_i
        t_trans1 = np.pi * np.sqrt((r_i * (1 + Rs) / 2) ** 3 / k)
        t_trans2 = np.pi * np.sqrt((r_i * (R + Rs) / 2) ** 3 / k)
        return cls((0 * u.s, dv_a), (t_trans1, dv_b), (t_trans2, dv_c))

    def get_total_time(self):
        """Returns total time of the maneuver.

        """
        total_time = sum(self._dts, 0 * u.s)
        return total_time

    def get_total_cost(self):
        """Returns otal cost of the maneuver.

        """
        dvs = [np.sqrt(dv.dot(dv)) for dv in self._dvs]
        return sum(dvs, 0 * u.km / u.s)