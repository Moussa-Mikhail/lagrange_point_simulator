# pylint: disable=invalid-name, missing-function-docstring
"""Simulates orbits near the Lagrange Point L4 using the position Verlet algorithm.
It assumes that both the star and planet are undergoing uniform circular motion.
"""

# to measure time taken in computing. for testing purposes only.
from functools import wraps
from math import ceil
from time import perf_counter

# numpy allows us to compute common math functions and work with arrays.
import numpy as np

# plotting module.
import pyqtgraph as pg  # type: ignore

# shortens function call
from numpy.linalg import norm
from pyqtgraph.Qt.QtCore import QTimer  # type: ignore

try:
    # cythonized version of integrate
    # roughly 4.5x times faster
    from integrate_cy import integrate  # type: ignore

except ImportError:

    from integrate_py import integrate

try:

    # cythonized version of transform_to_corotating
    # roughly 4.5x times faster
    from transform_cy import transform_to_corotating  # type: ignore

except ImportError:

    from transform_py import transform_to_corotating

from constants import AU, G, earth_mass, pi, sat_mass, sun_mass, years


def time_func(func):
    """Measures the time taken by a function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        print(f"{func.__name__} took {end - start} seconds")
        return result

    return wrapper


def calc_lagrange_points(star_mass, planet_mass, planet_distance):

    hill_radius = planet_distance * (planet_mass / (3 * star_mass)) ** (1 / 3)

    # Position of L1
    L1 = planet_distance * np.array((1, 0, 0)) - np.array((hill_radius, 0, 0))

    # Position of L2
    L2 = planet_distance * np.array((1, 0, 0)) + np.array((hill_radius, 0, 0))

    L3_dist = planet_distance * 7 / 12 * planet_mass / star_mass

    # Located opposite of the planet and slightly further away from the star
    # than the planet
    L3 = -planet_distance * np.array((1, 0, 0)) - np.array((L3_dist, 0, 0))

    # Position of L4 Lagrange point.
    # It is equidistant from both star and planet.
    # It forms a 60 degree=pi/3 radians angle with the positive x-axis.
    L4 = planet_distance * np.array((np.cos(pi / 3), np.sin(pi / 3), 0))

    # Position of L5 Lagrange point.
    # It is equidistant from both star and planet.
    # It forms a 60 degree=pi/3 radians angle with the positive x-axis.
    L5 = planet_distance * np.array((np.cos(pi / 3), -np.sin(pi / 3), 0))

    return {"L1": L1, "L2": L2, "L3": L3, "L4": L4, "L5": L5}


def calc_period_from_semi_major_axis(semi_major_axis, star_mass, planet_mass):
    # pylint: disable=redefined-outer-name

    period_squared = (
        4 * pi**2 * semi_major_axis**3 / (G * (star_mass + planet_mass))
    )

    return np.sqrt(period_squared)


def calc_default_angles(lagrange_point, perturbation_angle, vel_angle):
    """Calculates the default angles for the satellite in degrees"""

    default_pertubation_angle = np.arctan2(lagrange_point[1], lagrange_point[0])

    default_pertubation_angle = np.degrees(default_pertubation_angle)

    if perturbation_angle is None:

        perturbation_angle = default_pertubation_angle

    if vel_angle is None:

        vel_angle = default_pertubation_angle + 90

    return perturbation_angle, vel_angle


class Simulation:
    """Holds parameters and methods for simulation"""

    def __init__(
        self,
        num_years=100.0,
        num_steps=10**6,
        perturbation_size=0,
        perturbation_angle=None,
        speed=1.0,
        vel_angle=None,
        star_mass=sun_mass,
        planet_mass=earth_mass,
        planet_distance=1.0,
        lagrange_point="L4",
        plot_conserved=False,
    ):

        self.num_years = num_years

        self.num_steps = num_steps

        # converting num_years to seconds
        self.sim_stop = num_years * years

        self.time_step = self.sim_stop / num_steps

        # array of num_steps+1 time points evenly spaced between 0 and sim_stop
        self.times = np.linspace(0, self.sim_stop, num_steps + 1)

        self.perturbation_size = perturbation_size

        self.perturbation_angle = perturbation_angle

        self.speed = speed

        self.vel_angle = vel_angle

        self.star_mass = star_mass

        self.planet_mass = planet_mass

        self.planet_distance = planet_distance

        lagrange_points = calc_lagrange_points(
            star_mass, planet_mass, planet_distance * AU
        )

        self.lagrange_point = lagrange_points[lagrange_point]

        # star starts at origin
        CM_x_coord = (
            planet_distance * planet_mass / (star_mass + planet_mass + sat_mass)
        )

        CM_pos = [CM_x_coord, 0, 0]

        lagrange_point_trans = self.lagrange_point - CM_pos

        self.perturbation_angle, self.vel_angle = calc_default_angles(
            lagrange_point_trans, perturbation_angle, vel_angle
        )

        self.orbital_period = calc_period_from_semi_major_axis(
            planet_distance * AU, star_mass, planet_mass
        )

        self.angular_speed = 2 * pi / self.orbital_period

        self.plot_conserved = plot_conserved

        self.timer = QTimer()

    def main(self):

        star_pos, star_vel, planet_pos, planet_vel, sat_pos, sat_vel = self.calc_orbit()

        CM_pos = self.calc_center_of_mass(star_pos, planet_pos, sat_pos)

        # Transform to coordinate system where the Center of Mass is the origin
        star_pos_trans = star_pos - CM_pos

        planet_pos_trans = planet_pos - CM_pos

        sat_pos_trans = sat_pos - CM_pos

        orbit_plot, update_plot = self.plot_orbit(
            star_pos_trans, planet_pos_trans, sat_pos_trans
        )

        self.timer.timeout.connect(update_plot)

        star_pos_rotated = self.transform_to_corotating(star_pos_trans)

        planet_pos_rotated = self.transform_to_corotating(planet_pos_trans)

        sat_pos_rotated = self.transform_to_corotating(sat_pos_trans)

        lagrange_point_trans = self.lagrange_point - CM_pos

        corotating_plot, update_corotating = self.plot_corotating_orbit(
            star_pos_rotated,
            planet_pos_rotated,
            sat_pos_rotated,
            lagrange_point_trans,
        )

        self.timer.timeout.connect(update_corotating)

        # time in milliseconds between plot updates
        period = 33

        self.timer.start(period)

        if self.plot_conserved:
            (
                total_momentum,
                total_angular_momentum,
                total_energy,
            ) = self.conservation_calculations(
                star_pos, star_vel, planet_pos, planet_vel, sat_pos, sat_vel
            )

            init_planet_momentum = norm(self.planet_mass * planet_vel[0])

            self.plot_conserved_quantities(
                init_planet_momentum,
                total_momentum,
                total_angular_momentum,
                total_energy,
            )

        return orbit_plot, corotating_plot, self.timer

    def calc_orbit(self):

        # Initialize the positions and velocities of the bodies
        (
            star_pos,
            star_vel,
            planet_pos,
            planet_vel,
            sat_pos,
            sat_vel,
        ) = self.initialization()

        self.integrate(
            star_pos,
            star_vel,
            planet_pos,
            planet_vel,
            sat_pos,
            sat_vel,
        )

        return star_pos, star_vel, planet_pos, planet_vel, sat_pos, sat_vel

    def initialization(self):

        """Initializes the arrays of positions and velocities
        so that their initial values correspond to the input parameters
        """

        # creating position and velocity vector arrays

        # array of position vectors for star
        star_pos = np.empty((self.num_steps + 1, 3), dtype=np.double)

        # array of velocity vectors for star
        star_vel = np.empty_like(star_pos)

        planet_pos = np.empty_like(star_pos)

        planet_vel = np.empty_like(star_pos)

        sat_pos = np.empty_like(star_pos)

        sat_vel = np.empty_like(star_pos)

        # star is initially at origin but its position is not fixed
        star_pos[0] = np.array((0, 0, 0))

        # planet starts planet_distance from the star (and origin) and lies on the positive x-axis
        planet_pos[0] = np.array((self.planet_distance * AU, 0, 0))

        # Perturbation #

        perturbation_size = self.perturbation_size * AU

        perturbation_angle = np.radians(self.perturbation_angle)

        perturbation = perturbation_size * np.array(
            (np.cos(perturbation_angle), np.sin(perturbation_angle), 0)
        )

        # perturbing the initial position of the satellite
        sat_pos[0] = self.lagrange_point + perturbation

        # star and planet orbit about the Center of Mass
        # at an angular_speed = 2 pi radians/orbital_period
        # we setup conditions so that the star and planet have circular orbits
        # velocities have to be defined relative to the CM
        init_CM_pos = self.calc_center_of_mass(star_pos[0], planet_pos[0], sat_pos[0])

        # orbits are counter clockwise so
        # angular velocity is in the positive z direction
        angular_vel = np.array((0, 0, self.angular_speed))

        speed = self.speed * norm(np.cross(angular_vel, planet_pos[0] - init_CM_pos))

        vel_angle = np.radians(self.vel_angle)

        sat_vel[0] = speed * np.array((np.cos(vel_angle), np.sin(vel_angle), 0))

        # End Perturbation #

        # for a circular orbit velocity = cross_product(angular velocity, position)
        # where vec(position) is the position relative to the point being orbited
        # in this case the Center of Mass
        star_vel[0] = np.cross(angular_vel, star_pos[0] - init_CM_pos)

        # * 1.2 is used for testing purposes.
        planet_vel[0] = np.cross(angular_vel, planet_pos[0] - init_CM_pos)  # * 1.2

        return star_pos, star_vel, planet_pos, planet_vel, sat_pos, sat_vel

    def integrate(
        self,
        star_pos,
        star_vel,
        planet_pos,
        planet_vel,
        sat_pos,
        sat_vel,
    ):

        integrate(
            self.time_step,
            self.num_steps,
            self.star_mass,
            self.planet_mass,
            star_pos,
            star_vel,
            planet_pos,
            planet_vel,
            sat_pos,
            sat_vel,
        )

    def calc_center_of_mass(self, star_pos, planet_pos, sat_pos):

        return (
            self.star_mass * star_pos
            + self.planet_mass * planet_pos
            + sat_mass * sat_pos
        ) / (self.star_mass + self.planet_mass + sat_mass)

    def plot_orbit(self, star_pos_trans, planet_pos_trans, sat_pos_trans):

        orbit_plot = pg.plot(title="Orbits of Masses")
        orbit_plot.setLabel("bottom", "x", units="AU")
        orbit_plot.setLabel("left", "y", units="AU")
        orbit_plot.addLegend()

        orbit_plot.setXRange(-1.2 * self.planet_distance, 1.2 * self.planet_distance)
        orbit_plot.setYRange(-1.2 * self.planet_distance, 1.2 * self.planet_distance)
        orbit_plot.setAspectLocked(True)

        arr_step = self.plot_array_step()

        # Sun has an orbit on the scale of micro-AU under normal Earth-Sun conditions
        # Zoom in to see it
        orbit_plot.plot(
            star_pos_trans[::arr_step, :2] / AU,
            pen="y",
            name="Star",
        )

        orbit_plot.plot(
            planet_pos_trans[::arr_step, :2] / AU,
            pen="b",
            name="Planet",
        )

        orbit_plot.plot(
            sat_pos_trans[::arr_step, :2] / AU,
            pen="g",
            name="Satellite",
        )

        anim_plot = pg.ScatterPlotItem()

        # The purpose of this is to add the bodies to the plot legend
        # and plot their initial positions
        anim_plot.addPoints(
            [star_pos_trans[0, 0] / AU],
            [star_pos_trans[0, 1] / AU],
            pen="y",
            brush="y",
            size=10,
        )

        anim_plot.addPoints(
            [planet_pos_trans[0, 0] / AU],
            [planet_pos_trans[0, 1] / AU],
            pen="b",
            brush="b",
            size=10,
        )

        anim_plot.addPoints(
            [sat_pos_trans[0, 0] / AU],
            [sat_pos_trans[0, 1] / AU],
            pen="g",
            brush="g",
            size=10,
        )

        orbit_plot.addItem(anim_plot)

        idx = self.update_idx()

        def update_plot():

            i = next(idx)

            anim_plot.clear()

            anim_plot.addPoints(
                [star_pos_trans[i, 0] / AU],
                [star_pos_trans[i, 1] / AU],
                pen="y",
                brush="y",
                size=10,
                name="Star",
            )

            anim_plot.addPoints(
                [planet_pos_trans[i, 0] / AU],
                [planet_pos_trans[i, 1] / AU],
                pen="b",
                brush="b",
                size=10,
                name="Planet",
            )

            anim_plot.addPoints(
                [sat_pos_trans[i, 0] / AU],
                [sat_pos_trans[i, 1] / AU],
                pen="g",
                brush="g",
                size=10,
                name="Satellite",
            )

        return orbit_plot, update_plot

    def transform_to_corotating(self, pos_trans):

        return transform_to_corotating(self.times, self.angular_speed, pos_trans)

    def plot_corotating_orbit(
        self,
        star_pos_rotated,
        planet_pos_rotated,
        sat_pos_rotated,
        lagrange_point_trans,
    ):

        # Animated plot of satellites orbit in co-rotating frame.
        corotating_plot = pg.plot(title="Orbits in Co-Rotating Coordinate System")
        corotating_plot.setLabel("bottom", "x", units="AU")
        corotating_plot.setLabel("left", "y", units="AU")
        corotating_plot.addLegend()

        min_x = star_pos_rotated[0, 0] / AU - 0.2 * self.planet_distance

        max_x = planet_pos_rotated[0, 0] / AU + 0.2 * self.planet_distance

        min_y = -0.5 * self.planet_distance

        max_y = lagrange_point_trans[0, 1] / AU + 0.5 * self.planet_distance

        corotating_plot.setXRange(min_x, max_x)
        corotating_plot.setYRange(min_y, max_y)
        corotating_plot.setAspectLocked(True)

        anim_rotated_plot = pg.ScatterPlotItem()

        corotating_plot.addItem(anim_rotated_plot)

        arr_step = self.plot_array_step()

        corotating_plot.plot(
            sat_pos_rotated[::arr_step, 0] / AU,
            sat_pos_rotated[::arr_step, 1] / AU,
            pen="g",
        )

        # The purpose of this is to add the bodies to the plot legend
        # and plot their initial positions
        corotating_plot.plot(
            [star_pos_rotated[0, 0] / AU],
            [star_pos_rotated[0, 1] / AU],
            name="Star",
            pen="k",
            symbol="o",
            symbolPen="y",
            symbolBrush="y",
        )

        corotating_plot.plot(
            [planet_pos_rotated[0, 0] / AU],
            [planet_pos_rotated[0, 1] / AU],
            name="Planet",
            pen="k",
            symbol="o",
            symbolPen="b",
            symbolBrush="b",
        )

        corotating_plot.plot(
            [sat_pos_rotated[0, 0] / AU],
            [sat_pos_rotated[0, 1] / AU],
            name="Satellite",
            pen="k",
            symbol="o",
            symbolPen="g",
            symbolBrush="g",
        )

        corotating_plot.plot(
            [lagrange_point_trans[0, 0] / AU],
            [lagrange_point_trans[0, 1] / AU],
            name="Lagrange Point",
            pen="k",
            symbol="o",
            symbolPen="w",
            symbolBrush="w",
        )

        idx = self.update_idx()

        def update_corotating():

            j = next(idx)

            anim_rotated_plot.clear()

            anim_rotated_plot.addPoints(
                [star_pos_rotated[j, 0] / AU],
                [star_pos_rotated[j, 1] / AU],
                pen="y",
                brush="y",
                size=10,
                name="Star",
            )

            anim_rotated_plot.addPoints(
                [planet_pos_rotated[j, 0] / AU],
                [planet_pos_rotated[j, 1] / AU],
                pen="b",
                brush="b",
                size=10,
                name="Planet",
            )

            anim_rotated_plot.addPoints(
                [sat_pos_rotated[j, 0] / AU],
                [sat_pos_rotated[j, 1] / AU],
                pen="g",
                brush="g",
                size=10,
                name="Satellite",
            )

            # steps_per_year = int(self.num_steps / self.num_years)

            # plots where the satellite is after 1 year
            # anim_rotated_plot.addPoints(
            #     [sat_pos_rotated[steps_per_year, 0] / AU],
            #     [sat_pos_rotated[steps_per_year, 1] / AU],
            #     pen="g",
            #     brush="w",
            #     size=10,
            #     name="Satellite 1 yr",
            # )

        return corotating_plot, update_corotating

    def plot_array_step(self, num_points_to_plot=10**5):

        # no need to plot all points

        # step size when plotting
        # i.e. if points_plotted_step = 10 then plot every 10th point
        points_plotted_step = int((self.num_steps + 1) / num_points_to_plot)

        if points_plotted_step == 0:
            points_plotted_step = 1

        return points_plotted_step

    def update_idx(self):
        """This function is used to update the index of the plots"""

        i = 0

        time_step_default = 10 * years / 10**5

        # maximum rate of plot update is too slow
        # so instead step through arrays at a step of rate
        # inversely proportional to time_step so that
        # animated motion is the same regardless of
        # num_steps or num_years
        rate = 50 * ceil(time_step_default / self.time_step)

        while True:

            i = i + rate

            if i >= self.num_steps:
                i = 0

            yield i

    def conservation_calculations(
        self, star_pos, star_vel, planet_pos, planet_vel, sat_pos, sat_vel
    ):

        total_momentum = (
            self.star_mass * star_vel
            + self.planet_mass * planet_vel
            + sat_mass * sat_vel
        )

        angular_momentum_star = np.cross(star_pos, self.star_mass * star_vel)

        angular_momentum_planet = np.cross(planet_pos, self.planet_mass * planet_vel)

        angular_momentum_sat = np.cross(sat_pos, sat_mass * sat_vel)

        total_angular_momentum = (
            angular_momentum_star + angular_momentum_planet + angular_momentum_sat
        )

        # array of the distance between planet and star at each timestep
        d_planet_to_star = norm(star_pos - planet_pos, axis=1)

        d_planet_to_sat = norm(sat_pos - planet_pos, axis=1)

        d_star_to_sat = norm(sat_pos - star_pos, axis=1)

        potential_energy = (
            -G * self.star_mass * self.planet_mass / d_planet_to_star
            + -G * sat_mass * self.planet_mass / d_planet_to_sat
            + -G * sat_mass * self.star_mass / d_star_to_sat
        )

        # array of the magnitude of the velocity of star at each timestep
        mag_star_vel = norm(star_vel, axis=1)

        mag_planet_vel = norm(planet_vel, axis=1)

        mag_sat_vel = norm(sat_vel, axis=1)

        kinetic_energy = (
            0.5 * self.star_mass * mag_star_vel**2
            + 0.5 * self.planet_mass * mag_planet_vel**2
            + 0.5 * sat_mass * mag_sat_vel**2
        )

        total_energy = potential_energy + kinetic_energy

        return total_momentum, total_angular_momentum, total_energy

    def plot_conserved_quantities(
        self,
        init_planet_momentum,
        total_momentum,
        total_angular_momentum,
        total_energy,
    ):

        linear_momentum_plot = pg.plot(title="Normalized Linear Momentum vs Time")
        linear_momentum_plot.setLabel("bottom", "Time", units="years")
        linear_momentum_plot.setLabel("left", "Normalized Linear Momentum")

        linear_momentum_plot.addLegend()

        arr_step = self.plot_array_step()

        times_in_years = self.times[::arr_step] / years

        # total linear momentum is not conserved (likely due to floating point errors)
        # however the variation is insignificant compared to
        # the star's and planet's individual linear momenta
        linear_momentum_plot.plot(
            times_in_years,
            total_momentum[::arr_step, 0] / init_planet_momentum,
            pen="r",
            name="x",
        )

        linear_momentum_plot.plot(
            times_in_years,
            total_momentum[::arr_step, 1] / init_planet_momentum,
            pen="g",
            name="y",
        )

        linear_momentum_plot.plot(
            times_in_years,
            total_momentum[::arr_step, 2] / init_planet_momentum,
            pen="b",
            name="z",
        )

        angular_momentum_plot = pg.plot(title="Normalized Angular Momenta vs Time")
        angular_momentum_plot.setLabel("bottom", "Time", units="years")
        angular_momentum_plot.setLabel("left", "Normalized Angular Momentum")

        angular_momentum_plot.addLegend()

        # x and y components of angular momentum are 0
        # angular_momentum_plot.plot(
        #   times_in_years,
        #   total_angular_momentum[::arr_step, 0]/total_angular_momentum[0, 0]-1,
        #   pen='r',
        #   name='x'
        # )

        # angular_momentum_plot.plot(
        #   times_in_years,
        #   total_angular_momentum[::arr_step, 1]/total_angular_momentum[0, 1]-1,
        #   pen='g',
        #   name='y'
        # )

        angular_momentum_plot.plot(
            times_in_years,
            total_angular_momentum[::arr_step, 2] / total_angular_momentum[0, 2] - 1,
            pen="b",
            name="z",
        )

        energy_plot = pg.plot(title="Normalized Energy vs Time")
        energy_plot.setLabel("bottom", "Time", units="years")
        energy_plot.setLabel("left", "Normalized Energy")

        energy_plot.plot(times_in_years, total_energy[::arr_step] / total_energy[0] - 1)


@time_func
def main(
    num_years=100.0,
    num_steps=10**6,
    perturbation_size=0.0,
    perturbation_angle=None,
    speed=1.0,
    vel_angle=None,
    star_mass=sun_mass,
    planet_mass=earth_mass,
    planet_distance=1.0,
    lagrange_point="L4",
    plot_conserved=False,
):
    """main simulates a satellite's orbit corresponding to the following parameters.
    It then plots the orbit in inertial and corotating frames.

    All parameters have default values.

    It takes the following parameters:

    #### Simulation parameters
    num_years: Number of years to simulate. The default is 100.0.
    num_steps: Number of steps to simulate. Must be an integer. The default is 10**6.

    It is recommended that the ratio of num_steps to num_years
    remains close to the ratio of default values.

    #### Satellite parameters
    perturbation_size: Size of perturbation in AU. The default is 0.0.
    perturbation_angle: Angle of perturbation relative to positive x axis in degrees.
    The default is None.
    If None, then perturbation_size has the effect of
    moving the satellite away or towards the origin.

    speed: Initial speed of satellite as a factor of the planet's speed.
    i.e. speed = 1.0 -> satellite has the same speed as the planet.
    the default is 1.0.

    vel_angle: Angle of satellite's initial velocity relative to positive x axis in degrees.
    The default is None.
    If None, then vel_angle is perpendicular to the satellite's default position.

    lagrange_point: Non-perturbed position of satellite. String.
    The default is 'L4' but 'L1', 'L2', 'L3', 'L5' can also be used.

    #### System parameters
    star_mass: Mass of the star in kilograms. The default is the mass of the Sun.
    planet_mass: Mass of the planet in kilograms. The default is the mass of the Earth.
    The constants sun_mass and earth_mass may be imported from the file constants.py.
    planet_distance: Distance between the planet and the star in AU. The default is 1.0.

    plot_conserved: If True, plots the conserved quantities:
    energy, angular momentum, linear momentum.
    The default is False.

    This function will take ~0.46 seconds per 10**6 steps if
    the Cythonized extensions are available.
    1.4 seconds if not.
    The time may vary depending on your hardware.
    It will take longer than usual on the first call.
    """

    simulation = Simulation(
        num_years,
        num_steps,
        perturbation_size,
        perturbation_angle,
        speed,
        vel_angle,
        star_mass,
        planet_mass,
        planet_distance,
        lagrange_point,
        plot_conserved,
    )

    return simulation.main()
