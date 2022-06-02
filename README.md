# simulation

Python code used to simulate orbits near Lagrange points.

## Installation of GUI
This GUI is an application to make using simulation.py more user friendly.

Go to Releases and download the latest release. It is made for 64 bit Windows, and may not work on other OS's or 32 bit systems. The executable's large size is due to the fact that it contains all of its dependencies. This means that no further installation is required after downloading it.

## Installation of source code

Download the repository.
If you use Pip open your command line and enter "pip install -r requirements.txt". This will install all the packages these scripts depend on. If you use Poetry then a .lock file is provided.

## Usage

The simulation.py module is meant to be used by calling its main function.

```
main simulates a satellite's orbit near a Lagrange point.
It then plots the orbit in inertial and corotating frames.
The plots created are interactive.

It takes the following parameters:

#### Simulation Parameters
num_years: Number of years to simulate. The default is 100.0.
num_steps: Number of steps to simulate. Must be an integer. The default is 10**6.

It is recommended that the ratio of num_steps to num_years
remains close to the ratio of the default values.

#### Satellite Parameters
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

If None, then vel_angle is perpendicular to the satellite's
default position relative to the center of mass.

lagrange_point: Non-perturbed position of satellite. String.
The default is 'L4' but the others can also be used.

#### System Parameters
star_mass: Mass of the star in kilograms. The default is the mass of the Sun.

planet_mass: Mass of the planet in kilograms. The default is the mass of the Earth.

The constants sun_mass and earth_mass may be imported from the file constants.py.

planet_distance: Distance between the planet and the star in AU. The default is 1.0.

plot_conserved: If True, plots the conserved quantities:
energy, angular momentum, linear momentum.
The default is False.

This function will take ~0.42 seconds per 10**6 steps if
The time may vary depending on your hardware.
It will take longer than usual on the first call.
```

This is the docstring of simulation.main which can be seen at any time by using "help(simulation.main)" or "help(main)" in Python.
