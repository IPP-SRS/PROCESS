"""Load the appropriate Stellarator machine configuration"""

import json
from pathlib import Path

from process.core.exceptions import ProcessValueError
from process.core.model import DataStructure

HELIAS5B = {
    "name": "Helias 5b",
    "rmajor_ref": 22.2,
    "rminor_ref": 1.80,
    "aspect_ref": 12.33,
    "coil_rmajor": 22.44,
    "coil_rminor": 4.76,
    "bt_ref": 5.6,
    "wp_area": 0.8 * 0.6,
    "wp_bmax": 11.44,
    "symmetry": 5,
    "coilspermodule": 10,
    "a1": 0.688,
    "a2": 0.025,
    "vol_plasma": 1422.63,  # This value is for Helias 5
    "dmin": 0.84,
    "max_portsize_width": 2.12,
    "plasma_surface": 1960.0,  # Plasma Surface
    "maximal_coil_height": 12.7,  # [m] Full height max point to min point
    "coilsurface": 4817.7,  # Coil surface, dimensionfull. At reference point
    "coillength": 1680.0,  # Central filament length of machine with outer radius 1m.
    "I0": 13.06,  # Coil Current needed to produce 1T on axis in [MA] at outer radius 1m
    "inductance": 1655.76e-6,  # inductance in muH
    # The fit values in stellarator config class should be calculated using this value.
    "WP_ratio": 1.2,
    "max_force_density": 120.0,  # [MN/m^3]
    "max_force_density_mnm": 98.0,  # [MN/m]
    "max_lateral_force_density": 92.4,  # [MN/m^3]
    "max_radial_force_density": 113.5,  # [MN/m^3]
    "centering_force_max_mn": 189.5,
    "centering_force_min_mn": -55.7,
    "centering_force_avg_mn": 93.0,
    "min_plasma_coil_distance": 1.9,
    "derivative_min_lcfs_coils_dist": -1.0,  # this is approximated for now
    "min_bend_radius": 1.0,  # [m]
    "neutron_peakfactor": 1.6,
    "epseff": 0.015,
}


HELIAS4 = {
    "name": "Helias 4",
    # Reference point where all the other variables are determined from
    # Plasma outer radius
    "rmajor_ref": 17.6,
    "rminor_ref": 2.0,
    "aspect_ref": 8.8,
    # Coil radii
    "coil_rmajor": 18.39,
    "coil_rminor": 4.94,
    "bt_ref": 5.6,
    "wp_area": 0.8 * 0.6,
    "wp_bmax": 11.51,
    "symmetry": 4,
    "coilspermodule": 10,
    "a1": 0.676,
    "a2": 0.029,
    "vol_plasma": 1380.0,
    "dmin": 1.08,
    "max_portsize_width": 3.24,
    "plasma_surface": 1900.0,
    "maximal_coil_height": 13.34,  # [m] Full height max point to min point
    "coilsurface": 4100.0,  # Coil surface, dimensionfull. At reference point
    "coillength": 1435.07,  # Central filament length of machine with outer radius 1m.
    "I0": 13.146,  # Coil Current needed to produce b0 on axis in [MA] at reference point
    "inductance": 1290.4e-6,  # inductance/R*A^2 in muH
    "WP_ratio": 1.3,
    "max_force_density": 120.0,  # [MN/m^3]
    "max_force_density_mnm": 98.0,  # [MN/m]
    "max_lateral_force_density": 87.9,  # [MN/m^3]
    "max_radial_force_density": 109.9,  # [MN/m^3]
    "centering_force_max_mn": 226.0,
    "centering_force_min_mn": -35.3,
    "centering_force_avg_mn": 125.8,
    "min_plasma_coil_distance": 1.7,
    "derivative_min_lcfs_coils_dist": -1.0,  # this is approximated for now
    "min_bend_radius": 0.86,  # [m]
    "neutron_peakfactor": 1.6,
    "epseff": 0.015,
}

HELIAS3 = {
    "name": "Helias 3",
    # Reference point where all the other variables are determined from
    # Plasma outer radius
    "rmajor_ref": 13.86,
    "rminor_ref": 2.18,
    "aspect_ref": 6.36,
    # Coil radii
    "coil_rmajor": 14.53,
    "coil_rminor": 6.12,
    "bt_ref": 5.6,
    "wp_bmax": 12.346,
    "wp_area": 0.8 * 0.6,
    "symmetry": 3,
    "coilspermodule": 10,
    # Bmax fit parameters
    "a1": 0.56,
    "a2": 0.030,
    "vol_plasma": 1300.8,
    "dmin": 1.145,
    "max_portsize_width": 3.24,  # ??? guess. not ready yet
    "plasma_surface": 1600.00,
    "maximal_coil_height": 17.74,  # [m] Full height max point to min point
    "coilsurface": 4240.0,  # Coil surface, dimensionfull. At reference point
    "coillength": 1287.3,  # Central filament length of machine with outer radius 1m.
    "I0": 14.23,  # Coil Current needed to produce 1T on axis in [MA] at outer radius 1m
    "inductance": 1250.7e-6,  # inductance in muH
    "WP_ratio": 1.3,
    "max_force_density": 120.0,  # [MN/m]
    "max_force_density_mnm": 98.0,
    "max_lateral_force_density": 96.6,  # [MN/m^3]
    "max_radial_force_density": 130.5,  # [MN/m^3]
    "centering_force_max_mn": 428.1,
    "centering_force_min_mn": -70.3,
    "centering_force_avg_mn": 240.9,
    "min_plasma_coil_distance": 1.78,
    "derivative_min_lcfs_coils_dist": -1.0,  # this is approximated for now
    "min_bend_radius": 1.145,  # [m]
    "neutron_peakfactor": 1.6,
    "epseff": 0.015,
}

W7X30 = {
    "name": "W7X-30",
    # Reference point where all the other variables are determined from
    # Plasma outer radius
    "rmajor_ref": 5.50,
    "rminor_ref": 0.49,
    "aspect_ref": 11.2,
    # Coil radii
    "coil_rmajor": 5.62,
    "coil_rminor": 1.36,
    "bt_ref": 3.0,
    "wp_area": 0.18 * 0.15,
    "wp_bmax": 10.6,
    "symmetry": 5,
    "coilspermodule": 6,
    "a1": 0.98,
    "a2": 0.041,
    "vol_plasma": 26.4,
    "dmin": 0.21,
    "max_portsize_width": 0.5,
    "plasma_surface": 128.3,
    "maximal_coil_height": 3.6,  # [m] Full height max point to min point
    "coilsurface": 370.0,  # Coil surface, dimensionfull. At reference point
    "coillength": 303.4,  # Central filament length of machine with outer radius 1m.
    "I0": 2.9,  # Coil Current needed to produce b0 on axis in [MA] at reference point
    "inductance": 252.7e-6,  # inductance/R*A^2 in muH
    "WP_ratio": 1.2,
    "max_force_density": 350.0,  # [MN/m^3]
    "max_force_density_mnm": 98.0,  # [MN/m]
    "max_lateral_force_density": 271.1,  # [MN/m^3]
    "max_radial_force_density": 305.2,  # [MN/m^3]
    "centering_force_max_mn": 7.95,
    "centering_force_min_mn": -2.15,
    "centering_force_avg_mn": 3.46,
    "min_plasma_coil_distance": 0.45,
    "derivative_min_lcfs_coils_dist": -1.0,  # this is approximated for now
    "min_bend_radius": 0.186,  # [m]
    "neutron_peakfactor": 1.6,
    "epseff": 0.015,
}

W7X50 = {
    "name": "W7X-50",
    # Reference point where all the other variables are determined from
    # Plasma outer radius
    "rmajor_ref": 5.5,
    "rminor_ref": 0.49,
    "aspect_ref": 11.2,
    # Coil radii
    "coil_rmajor": 5.62,
    "coil_rminor": 1.18,
    "bt_ref": 3.0,
    "wp_area": 0.18 * 0.15,
    "wp_bmax": 6.3,
    "symmetry": 5,
    "coilspermodule": 10,
    "a1": 0.66,
    "a2": 0.025,
    "vol_plasma": 26.4,
    "dmin": 0.28,
    "max_portsize_width": 0.3,
    "plasma_surface": 128.3,
    "maximal_coil_height": 3.1,  # [m] Full height max point to min point
    "coilsurface": 299.85,  # Coil surface, dimensionfull. At reference point
    "coillength": 420.67,  # Central filament length of machine with outer radius 1m.
    "I0": 1.745,  # Coil Current needed to produce b0 on axis in [MA] at reference point
    "inductance": 412.4e-6,  # inductance/R*A^2 in muH
    "WP_ratio": 1.2,
    "max_force_density": 250.0,  # [MN/m^3]
    "max_force_density_mnm": 98.0,  # [MN/m]
    "max_lateral_force_density": 116.4,  # [MN/m^3]
    "max_radial_force_density": 148.0,  # [MN/m^3]
    "centering_force_max_mn": 2.99,
    "centering_force_min_mn": -1.29,
    "centering_force_avg_mn": 1.61,
    "min_plasma_coil_distance": 0.39,
    "derivative_min_lcfs_coils_dist": -1.0,  # this is approximated for now
    "min_bend_radius": 0.39,  # [m]
    "neutron_peakfactor": 1.6,
    "epseff": 0.015,
}


def load_stellarator_config(istell: int, config_file: Path | None, data: DataStructure):
    """Load the appropriate Stellarator machine configuration

    Parameters
    ----------
    istell:
        istell = 1: Helias5 machine
        istell = 2: Helias4 machine
        istell = 3: Helias3 machine
        istell = 4: w7x30 machine
        istell = 5: w7x50 machine
        istell = 6: Init from json
    config_file:

    data: DataStructure
        data structure object

    Raises
    ------
    ProcessValueError
        If stellarator config file is None but istell=6, or if
        istell is not an integer in the range [1, 6]
    """
    match istell:
        case 1:
            machine_config = HELIAS5B
        case 2:
            machine_config = HELIAS4
        case 3:
            machine_config = HELIAS3
        case 4:
            machine_config = W7X30
        case 5:
            machine_config = W7X50
        case 6:
            if config_file is None:
                raise ProcessValueError("Stellarator config file is None but istell=6")

            with open(config_file) as f:
                machine_config = json.load(f)
        case _:
            raise ProcessValueError(f"{istell=} is not an integer in the range [1, 6]")

    _assign_stellarator_config(data, machine_config)


def _assign_stellarator_config(data: DataStructure, machine_config: dict) -> None:
    """Copy *machine_config* onto ``data.stellarator_config``.

    One explicit assignment per declared field, in ``StellaratorConfigData``
    declaration order. This replaced a ``setattr`` loop over the config keys.
    The loop was correct but wrote 35 fields through a computed name, so no
    static reader -- an IDE, ``mypy``, a grep, or a dependency analyser --
    could see that these fields are ever written. They appeared to be
    configuration that nothing produces.

    Three behaviours of the loop are preserved deliberately:

    * **Case folding.** Nine keys are not written in the case of the field they
      set -- ``I0``, ``WP_area``, ``WP_bmax``, ``WP_ratio``,
      ``max_force_density_MNm``, the three ``centering_force_*_MN``, and
      ``derivative_min_LCFS_coils_dist`` -- hence the ``.lower()`` normalisation
      before the block rather than at each lookup.
    * **Unknown keys are skipped silently.** This is not theoretical:
      ``tests/regression/input_files/stellarator_helias.stella_conf.json``
      carries 38 keys of which 3 match no field (``number_nu_star``,
      ``D11_star_mono_input``, ``nu_star_mono_input``). Raising on an unknown
      key would break that scenario.
    * **Duplicate folded keys keep last-wins.** ``{"I0": 1.0, "i0": 2.0}`` are
      two distinct keys that fold to one; the loop ``setattr``\\ ed both and the
      last won, and the dict comprehension below keeps the last for the same
      reason.

    A new config key now costs two edits rather than one -- a field on
    ``StellaratorConfigData`` and an assignment here. That is the price of the
    writes being visible, and it is what the surrounding tooling assumes.

    Note what is deliberately *not* fixed: the silent skip hides typos, so a
    user writing ``epsef`` for ``epseff`` gets the dataclass default and no
    warning. That is arguably the worse defect, but changing it would change
    behaviour, which this does not.
    """
    config = {key.lower(): value for key, value in machine_config.items()}

    if "name" in config:
        data.stellarator_config.stella_config_name = config["name"]
    if "symmetry" in config:
        data.stellarator_config.stella_config_symmetry = config["symmetry"]
    if "coilspermodule" in config:
        data.stellarator_config.stella_config_coilspermodule = config["coilspermodule"]
    if "rmajor_ref" in config:
        data.stellarator_config.stella_config_rmajor_ref = config["rmajor_ref"]
    if "rminor_ref" in config:
        data.stellarator_config.stella_config_rminor_ref = config["rminor_ref"]
    if "coil_rmajor" in config:
        data.stellarator_config.stella_config_coil_rmajor = config["coil_rmajor"]
    if "coil_rminor" in config:
        data.stellarator_config.stella_config_coil_rminor = config["coil_rminor"]
    if "aspect_ref" in config:
        data.stellarator_config.stella_config_aspect_ref = config["aspect_ref"]
    if "bt_ref" in config:
        data.stellarator_config.stella_config_bt_ref = config["bt_ref"]
    if "wp_area" in config:
        data.stellarator_config.stella_config_wp_area = config["wp_area"]
    if "wp_bmax" in config:
        data.stellarator_config.stella_config_wp_bmax = config["wp_bmax"]
    if "i0" in config:
        data.stellarator_config.stella_config_i0 = config["i0"]
    if "a1" in config:
        data.stellarator_config.stella_config_a1 = config["a1"]
    if "a2" in config:
        data.stellarator_config.stella_config_a2 = config["a2"]
    if "dmin" in config:
        data.stellarator_config.stella_config_dmin = config["dmin"]
    if "inductance" in config:
        data.stellarator_config.stella_config_inductance = config["inductance"]
    if "coilsurface" in config:
        data.stellarator_config.stella_config_coilsurface = config["coilsurface"]
    if "coillength" in config:
        data.stellarator_config.stella_config_coillength = config["coillength"]
    if "max_portsize_width" in config:
        data.stellarator_config.stella_config_max_portsize_width = config[
            "max_portsize_width"
        ]
    if "maximal_coil_height" in config:
        data.stellarator_config.stella_config_maximal_coil_height = config[
            "maximal_coil_height"
        ]
    if "min_plasma_coil_distance" in config:
        data.stellarator_config.stella_config_min_plasma_coil_distance = config[
            "min_plasma_coil_distance"
        ]
    if "derivative_min_lcfs_coils_dist" in config:
        data.stellarator_config.stella_config_derivative_min_lcfs_coils_dist = config[
            "derivative_min_lcfs_coils_dist"
        ]
    if "vol_plasma" in config:
        data.stellarator_config.stella_config_vol_plasma = config["vol_plasma"]
    if "plasma_surface" in config:
        data.stellarator_config.stella_config_plasma_surface = config["plasma_surface"]
    if "wp_ratio" in config:
        data.stellarator_config.stella_config_wp_ratio = config["wp_ratio"]
    if "max_force_density" in config:
        data.stellarator_config.stella_config_max_force_density = config[
            "max_force_density"
        ]
    if "max_force_density_mnm" in config:
        data.stellarator_config.stella_config_max_force_density_mnm = config[
            "max_force_density_mnm"
        ]
    if "min_bend_radius" in config:
        data.stellarator_config.stella_config_min_bend_radius = config[
            "min_bend_radius"
        ]
    if "epseff" in config:
        data.stellarator_config.stella_config_epseff = config["epseff"]
    if "max_lateral_force_density" in config:
        data.stellarator_config.stella_config_max_lateral_force_density = config[
            "max_lateral_force_density"
        ]
    if "max_radial_force_density" in config:
        data.stellarator_config.stella_config_max_radial_force_density = config[
            "max_radial_force_density"
        ]
    if "centering_force_max_mn" in config:
        data.stellarator_config.stella_config_centering_force_max_mn = config[
            "centering_force_max_mn"
        ]
    if "centering_force_min_mn" in config:
        data.stellarator_config.stella_config_centering_force_min_mn = config[
            "centering_force_min_mn"
        ]
    if "centering_force_avg_mn" in config:
        data.stellarator_config.stella_config_centering_force_avg_mn = config[
            "centering_force_avg_mn"
        ]
    if "neutron_peakfactor" in config:
        data.stellarator_config.stella_config_neutron_peakfactor = config[
            "neutron_peakfactor"
        ]
