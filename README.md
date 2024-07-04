# Rainy Day
Rainy Day is a weather simulation created during a game jam in September 2022 and built using Python and Pygame.
The simulation provides a dynamic environment featuring day and night cycles, seasonal changes, and various weather conditions including rain, snow, and thunderstorms.
Note that the simulation is intended as a small sandbox game rather than a realistic weather model.

The simulation runs on a grid where each cell can contain different blocks. You can interact with the environment by choosing and drawing with various materials, which have unique properties and behaviors.

## Requirements
To run the game, you need Python 3.8+ along with these libraries:
- [`numpy`](https://pypi.org/project/numpy/)
- [`pygame`](https://pypi.org/project/pygame/)
- [`noise`](https://pypi.org/project/noise/)

Run the game using: `python main.py`

## Interface
The user interface consists of an options panel on the left-hand side and an info display on the right-hand side.

### Options
- `Running`: Toggle the simulation on or off.
- `Weather` Cycle: Enable or disable dynamic weather changes.
- `Weather` Active: Enable or disable weather effects on the simulation.
- `Season`: Manually set the current season.
- `Weather`: Manually set the current weather.
- `Material`: Select a material to draw with in the simulation.
- `Days` Per Second: Adjust the speed of the simulation.
- `Block` Size: Adjust the size of the grid blocks (note: smaller block sizes may reduce fps).
- `Reload`: Reload the game with options to:
    - Generate a new world.
    - Clear all blocks from the current world.
    - Reset the current world.

### Weather types
- Sun
- Clouds
- Rain
- Snow
- Storm
- Thunderstorm

### Material/Block types
- Air: Empty space, allowing other materials to move through.
- Water: Flows and allows grass and flowers to grow on adjacent dirt blocks.
- Snow: Falls and eventually melts into water.
- Fire: Falls and burns through plants, flowers, and wood; extinguished by water.
- Dirt: Falls and can support the growth of trees.
- Dead Plants: Falls and can decompose into dirt.
- Plant: Static; grows on trees as leaves and on dirt as grass; flammable.
- Flower: Static; grows on dirt if water is nearby; flammable.
- Wood: Static; can turn into dead plants if not connected to dirt or other wood blocks touching dirt; flammable.
- Stone: Static and immovable.
