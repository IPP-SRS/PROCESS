import json
from pathlib import Path

from process.core.exceptions import ProcessValueError
from process.data_structure import stellarator_configuration

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
    "i0": 13.06,  # Coil Current needed to produce 1T on axis in [MA] at outer radius 1m
    "inductance": 1655.76e-6,  # inductance in muH
    "wp_ratio": 1.2,  # The fit values in stellarator config class should be calculated using this value.
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
    "i0": 13.146,  # Coil Current needed to produce b0 on axis in [MA] at reference point
    "inductance": 1290.4e-6,  # inductance/R*A^2 in muH
    "wp_ratio": 1.3,
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
    "i0": 14.23,  # Coil Current needed to produce 1T on axis in [MA] at outer radius 1m
    "inductance": 1250.7e-6,  # inductance in muH
    "wp_ratio": 1.3,
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
    "i0": 2.9,  # Coil Current needed to produce b0 on axis in [MA] at reference point
    "inductance": 252.7e-6,  # inductance/R*A^2 in muH
    "wp_ratio": 1.2,
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
    "i0": 1.745,  # Coil Current needed to produce b0 on axis in [MA] at reference point
    "inductance": 412.4e-6,  # inductance/R*A^2 in muH
    "wp_ratio": 1.2,
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


def load_stellarator_config(istell: int, config_file: Path | None):
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
                machine_config = {k.lower(): v for k, v in json.load(f).items()}
        case _:
            raise ProcessValueError(f"{istell=} is not an integer in the range [1, 6]")

    stellarator_configuration.stella_config_name = machine_config["name"]
    stellarator_configuration.stella_config_rmajor_ref = machine_config["rmajor_ref"]
    stellarator_configuration.stella_config_rminor_ref = machine_config["rminor_ref"]
    stellarator_configuration.stella_config_aspect_ref = machine_config["aspect_ref"]
    stellarator_configuration.stella_config_coil_rmajor = machine_config["coil_rmajor"]
    stellarator_configuration.stella_config_coil_rminor = machine_config["coil_rminor"]
    stellarator_configuration.stella_config_bt_ref = machine_config["bt_ref"]
    stellarator_configuration.stella_config_wp_area = machine_config["wp_area"]
    stellarator_configuration.stella_config_wp_bmax = machine_config["wp_bmax"]
    stellarator_configuration.stella_config_symmetry = machine_config["symmetry"]
    stellarator_configuration.stella_config_coilspermodule = machine_config["coilspermodule"]
    stellarator_configuration.stella_config_a1 = machine_config["a1"]
    stellarator_configuration.stella_config_a2 = machine_config["a2"]
    stellarator_configuration.stella_config_vol_plasma = machine_config["vol_plasma"]
    stellarator_configuration.stella_config_dmin = machine_config["dmin"]
    stellarator_configuration.stella_config_max_portsize_width = machine_config["max_portsize_width"]
    stellarator_configuration.stella_config_plasma_surface = machine_config["plasma_surface"]
    stellarator_configuration.stella_config_maximal_coil_height = machine_config["maximal_coil_height"]
    stellarator_configuration.stella_config_coilsurface = machine_config["coilsurface"]
    stellarator_configuration.stella_config_coillength = machine_config["coillength"]
    stellarator_configuration.stella_config_i0 = machine_config["i0"]
    stellarator_configuration.stella_config_inductance = machine_config["inductance"]
    stellarator_configuration.stella_config_wp_ratio = machine_config["wp_ratio"]
    stellarator_configuration.stella_config_max_force_density = machine_config["max_force_density"]
    stellarator_configuration.stella_config_max_force_density_mnm = machine_config["max_force_density_mnm"]
    stellarator_configuration.stella_config_max_lateral_force_density = machine_config["max_lateral_force_density"]
    stellarator_configuration.stella_config_max_radial_force_density = machine_config["max_radial_force_density"]
    stellarator_configuration.stella_config_centering_force_max_mn = machine_config["centering_force_max_mn"]
    stellarator_configuration.stella_config_centering_force_min_mn = machine_config["centering_force_min_mn"]
    stellarator_configuration.stella_config_centering_force_avg_mn = machine_config["centering_force_avg_mn"]
    stellarator_configuration.stella_config_min_plasma_coil_distance = machine_config["min_plasma_coil_distance"]
    stellarator_configuration.stella_config_derivative_min_lcfs_coils_dist = machine_config["derivative_min_lcfs_coils_dist"]
    stellarator_configuration.stella_config_min_bend_radius = machine_config["min_bend_radius"]
    stellarator_configuration.stella_config_neutron_peakfactor = machine_config["neutron_peakfactor"]
    stellarator_configuration.stella_config_epseff = machine_config["epseff"]
