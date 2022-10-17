# About

Python code used to simulate satellite orbits near Lagrange points. It is meant for the L4/L5 points but any of the 5 points can be used. The initial position and velocity of the satellite can be specified by the user. Additionally, the masses of the star and planet, and the distance between them can also be specified.

## Installation of application

The application is meant to be a user friendly interface to the code.

Go to Releases and download the latest release. The application is started through the file 'sim_gui.exe'.
It is made for 64 bit Windows, and may not work on other OSs or 32 bit systems. The application's large size is due to the fact that it contains all of its dependencies. This means that no further installation is required after downloading it.

With the exception of plotting conserved quantities, the application has all the features of the underlying python code and is the recommended way to use it.

## Installation of source code

Download the repository.
If you use Pip open your command line in the repository directory and enter "pip install -r requirements.txt". This will install all the packages this code depends on. If you use Poetry then a .lock file is provided.

## Usage of simulator.py

The simulator.py module is meant to be used by calling its main function.

```
main simulates a satellite's orbit and returns position and velocity arrays of the star, planet, and satellite.

Takes the following parameters:

#### Simulation Parameters

num_years: float. Number of years to simulate. The default is 100.0.

num_steps: int. Number of steps to simulate. The default is 10**6.

a ratio of 10**4 steps per year is recommended.

#### Satellite Parameters

perturbation_size: float. Size of perturbation away from the Lagrange point in AU.
The default is 0.0.

perturbation_angle: float. Angle of perturbation relative to positive x axis in degrees.
The default is None.
If None, then perturbations are away or toward the origin.

speed: float. Initial speed of satellite as a factor of the planet's speed.
e.g. speed = 1.0 -> satellite has the same speed as the planet.
the default is 1.0.

vel_angle: float. Angle of satellite's initial velocity relative to positive x axis in degrees.
The default is None.
If None, then vel_angle is perpendicular to the satellite's
default position relative to the star.

lagrange_point: string. Non-perturbed position of satellite.
The default is 'L4' but 'L1', 'L2', 'L3', and 'L5' can also be used.

#### System Parameters

star_mass: float. Mass of the star in kilograms. The default is the mass of the Sun.

planet_mass: float. Mass of the planet in kilograms. The default is the mass of the Earth.
The constants sun_mass and earth_mass may be imported from the file constants.py.

planet_distance: float. Distance between the planet and the star in AU. The default is 1.0.

This function will take ~0.42 seconds per 10**6 steps.
The time may vary depending on your hardware.
It will take longer than usual on the first simulation.
 ```

This is the docstring of simulator.main which can be seen at any time by using "help(simulation.main)" or "help(main)" in Python.
