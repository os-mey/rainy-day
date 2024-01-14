from time import time, perf_counter, sleep
from random import vonmisesvariate as randangle
from random import triangular as randfloat
from random import choice as randchoice
from random import randint
from noise import snoise2
from math import *
from pygame.locals import *
import pygame, numpy, os


def randcoord(width, height, x=0, y=0):
    """
    Returns a random coord in the bounds of the rect.
    """
    return (randint(x, x + width), randint(y, y + height))


def randbool(probability):
    """
    Returns True or False based on the probability for True.
    """
    return not randint(0, 100 - min(99, probability))


def noise(x, seed, start=-1, end=1):
    num = snoise2(x/10, seed)
    d = end - start
    m = (start + end) / 2
    num *= d / 2
    num += m
    return num


def bounds(x, start, end):
    return min(max(x, start), end)


def connect(point0, point1):
    ends = numpy.array([point0, point1])
    d0, d1 = numpy.abs(numpy.diff(ends, axis=0))[0]
    if d0 > d1:
        return numpy.c_[
            numpy.linspace(ends[0, 0], ends[1, 0], d0 + 1, dtype=numpy.int32),
            numpy.round(numpy.linspace(ends[0, 1], ends[1, 1], d0 +
                                       1)).astype(numpy.int32)]
    else:
        return numpy.c_[
            numpy.round(numpy.linspace(ends[0, 0], ends[1, 0], d1 +
                                       1)).astype(numpy.int32),
            numpy.linspace(ends[0, 1], ends[1, 1], d1 + 1, dtype=numpy.int32)]


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Window:
    pygame.init()
    size = (800, 600)
    surface = pygame.display.set_mode(size)
    surface.fill((0, 0, 0))
    running = True
    pygame.display.set_caption("Weather")

    def quit():
        Window.running = False


class Clock:
    start = perf_counter()
    frame_length = 1 / 60
    fps = 0
    tick_last = 0
    dt = 0
    frames = []
    time = time()

    def get_tick():
        return int((perf_counter() - Clock.start) / Clock.frame_length)

    def update():
        r = Clock.get_tick() + 1
        while Clock.get_tick() < r:
            sleep(1 / 1000)

        tick = Clock.get_tick()
        Clock.time = time()
        Clock.dt = Clock.time - Clock.tick_last
        Clock.fps = len(Clock.frames) - 1
        Clock.tick_last = Clock.time
        Clock.frames = list(
            filter(lambda x: x >= tick - 1 / Clock.frame_length, Clock.frames))
        Clock.frames.append(tick)


class Text:
    letters = {}
    font = pygame.image.load(resource_path("ressources/font.png")).convert()
    for i in range(0, 64):
        subsurf = font.subsurface((i * 3, 0, 3, 5))
        subsurf.set_colorkey((255, 255, 255))
        letters[chr(i + 32)] = subsurf

    def write(surf, text, color, size, coord):
        text = str(text)
        if color == (0, 0, 0):
            color = (1, 1, 1)
        for letter in enumerate(text):
            letter_surf = pygame.Surface((3, 5))
            letter_surf.set_colorkey((0, 0, 0))
            letter_surf.fill(color)
            letter_surf.blit(Text.letters[letter[1].upper()], (0, 0))
            surf.blit(
                pygame.transform.scale(letter_surf, (3 * size, 5 * size)),
                (letter[0] * 4 * size + coord[0], coord[1]))


class ButtonSwitch:
    button = []

    def __init__(self, row, heading, choices, default=0):
        self.rect = pygame.Rect(0, 30 * row, 150, 30)
        self.active = False
        self.heading = heading
        self.choices_names = choices
        first_row = max(0, row - len(choices) + 1)
        self.choices_rects = [pygame.Rect(150, 30 * (i + first_row), 100, 30) for i in range(len(choices))]
        self.index = default
        self.new = False
        ButtonSwitch.button.append(self)

    def collide(rect, mouse, pressed):
        if pressed and not mouse[0]:
            return False
        return rect.collidepoint(mouse[1])

    def update():
        mouse = (True in pygame.mouse.get_pressed(), pygame.mouse.get_pos())
        for button in ButtonSwitch.button:
            if button.new:
                button.active = False
                button.new = False
            was_active = button.active
            button.active = ButtonSwitch.collide(button.rect, mouse, False)
            if was_active and not button.active:
                for choice_rect in button.choices_rects:
                    if ButtonSwitch.collide(choice_rect, mouse, False):
                        button.active = True
                        break
            ButtonSwitch.draw(button.heading, button.rect, button.active)
            if button.active:
                for i in range(len(button.choices_names)):
                    if ButtonSwitch.collide(button.choices_rects[i], mouse, True):
                        button.index = i
                        button.new = True
                    ButtonSwitch.draw(button.choices_names[i], button.choices_rects[i], button.index == i)

    def draw(text, rect, active):
        if active:
            width = 0
            fg = 255
        else:
            width = 1
            fg = 0
            pygame.draw.rect(Window.surface, (255, 255, 255), rect)
        pygame.draw.rect(Window.surface, (0, 0, 0), rect, width)
        Text.write(Window.surface, text, (fg, fg, fg), 2, (rect.centerx - (len(text) * 8) // 2, rect.centery - 5))


def draw_table(texts, coord):
    for line in range(len(texts)):
        columns = len(texts[line])
        pygame.draw.rect(Window.surface, (255, 255, 255), (coord[0], coord[1] + 30 * line, 100 * columns, 30))
        pygame.draw.rect(Window.surface, (0, 0, 0), (coord[0], coord[1] + 30 * line, 100 * columns, 30), 1)
        for column in range(columns):
            text = str(texts[line][column])
            center = (coord[0] + column * 100 + 50, coord[1] + line * 30 + 15)
            Text.write(Window.surface, text, (0, 0, 0), 2, (center[0] - (len(text) * 8) // 2, center[1] - 5))


class Weather:
    active = True
    time_mult = 0.05
    start = Clock.time
    day = 0
    season = 0
    temperature = 0
    clouds = 0
    wind = 0
    weather_cycle = True
    running = True
    fix = None
    start_fix = 0
    weather_conditions = [(0.0, 0.5),
                          (0.3, 0.5),
                          (0.65, 0.0),
                          (0.65, 0.5),
                          (1.0, 0.75),
                          (1.0, 0.25)
                          ]
    weather_name = ["Sun",
                    "Clouds",
                    "Rain",
                    "Snow", 
                    "Storm",
                    "Thunderstorm"
                    ]
    season_name = ["Winter",
                   "Spring",
                   "Summer",
                   "Autumn"
                   ]
    weather = 0
    seeds = [randint(-10000, 10000) for n in range(3)]

    def update():
        if Weather.running:
            if Weather.weather_cycle:
                Weather.day = round(Clock.time * Weather.time_mult - Weather.start * Weather.time_mult, 4)
            else:
                Weather.start += Clock.dt
            Weather.clouds = noise(Weather.day, Weather.seeds[0], 0, 0.5) + abs(Weather.season - 2) / 4
            Weather.wind = noise(Weather.day, Weather.seeds[1])
            Weather.season = int(Weather.day % 365 // 92)
            Weather.temperature = (Weather.temperature + Weather.clouds + abs(Weather.wind) + abs(abs(Weather.season - 2) - 2) * 3 + abs(Weather.day % 1 - 0.5) + noise(Weather.day, Weather.seeds[2], -0.5, 0.5)) / 10

            if Clock.time - Weather.start_fix > 20:
                Weather.fix = None
            if Weather.fix is None:
                clouds = Weather.clouds
                temperature = Weather.temperature
            else:
                clouds = Weather.fix[0]
                temperature = Weather.fix[1]
                if abs(Weather.clouds - clouds) + abs(Weather.temperature - temperature) < 0.1:
                    Weather.fix = None

            if clouds < 0.1:
                Weather.weather = 0
            elif clouds < 0.5:
                Weather.weather = 1
            elif clouds < 0.8:
                if temperature < 0.2:
                    Weather.weather = 2
                else:
                    Weather.weather = 3
            else:
                if temperature > 0.5:
                    Weather.weather = 4
                else:
                    Weather.weather = 5

            if Weather.weather != 0 and randbool(int(100 * (Weather.clouds / 2 + abs(Weather.wind) / 2))):
                x = 1200 * max(0, ceil(Weather.wind * -1)) - 200
                y = randint(0, 300)
                Cloud((x, y), randint(50, 150))
            
        else:
            Weather.start += Clock.dt


class Sun:
    coord = [0, 0]

    def update():
        Sun.coord[0] = cos(Weather.day % 1 * 2 * pi - pi / 2) * Window.size[0] + Window.size[0] // 2
        Sun.coord[1] = sin(Weather.day % 1 * 2 * pi - pi / 2) * Window.size[0] + Window.size[1] * 1.4
        pygame.draw.circle(Window.surface, (255, 200, 50), Sun.coord, 40)
        pygame.draw.circle(Window.surface, (255, 255, 100), Sun.coord, 30)
        pygame.draw.circle(Window.surface, (255, 255, 255), Sun.coord, 20)


class Cloud:
    cloud = []
    color = 1
    
    def __init__(self, coord, size):
        self.coord = coord
        self.size = size
        self.points = numpy.zeros((size, 4))
        self.speed = randfloat(0.9, 1.1)
        for i in range(size):
            y = -randint(0, size)
            x = floor((size ** 2 - y ** 2) ** 0.5) + 1
            x = randint(-x, x)
            r = size // 5 + randint(-3, 3)
            c = randfloat(0.9, 1.0)
            self.points[i] = (x, y, r, c)
        Cloud.cloud.append(self)

    def update():
        for cloud in Cloud.cloud:
            if Weather.running and Weather.weather_cycle:
                cloud.coord = (cloud.coord[0] + Weather.wind * cloud.speed, cloud.coord[1])
            for i in range(cloud.size):
                x, y, r, c = cloud.points[i]
                d_point = (abs(Sun.coord[0] - x - cloud.coord[0]) + abs(Sun.coord[1] - y - cloud.coord[1]))
                d_cloud = (abs(Sun.coord[0] - cloud.coord[0]) + abs(Sun.coord[1] - (cloud.coord[1] - cloud.size // 2)))
                if d_cloud  - cloud.size * 0.6 > d_point:
                    c += 0.1
                color = min(255, Cloud.color * c)
                pygame.draw.circle(Window.surface, (color, color, color), (x + cloud.coord[0], y + cloud.coord[1]), r)
            if Weather.running and Weather.weather_cycle:
                if Weather.weather == 2 and not randint(0, 20):
                    Material.create(randcoord(cloud.size // World.tile_size * 2, cloud.size / 2 // World.tile_size, (cloud.coord[0] - cloud.size) // World.tile_size, (Window.size[1] - cloud.coord[1]) // World.tile_size), 1)
                elif (Weather.weather == 3 or Weather.weather > 1 and Weather.temperature < 0.2) and not randint(0, 20):
                    Material.create(randcoord(cloud.size // World.tile_size * 2, cloud.size / 2 // World.tile_size, (cloud.coord[0] - cloud.size) // World.tile_size, (Window.size[1] - cloud.coord[1]) // World.tile_size), 2)
                if Weather.weather == 5 and not randint(0, 400):
                    Lightning(randcoord(int(cloud.size * 2), int(cloud.size / 2), int(cloud.coord[0] - cloud.size), int(cloud.coord[1])))
            if cloud.coord[0] < -200 or cloud.coord[0] > 1000:
                cloud.kill()
        Cloud.color = (Cloud.color * 199 + 255 / (Weather.weather / 3 + 1)) / 200

    def kill(self):
        Cloud.cloud.remove(self)
        del(self)
            

class Lightning:
    lightning = []

    def __init__(self, coord):
        self.origin = coord
        self.points = [(coord, randfloat(0.5, 5.0))]
        self.angle = randfloat(0, pi)
        self.origin_angle = self.angle
        self.strongest = coord
        self.time = Clock.time
        self.visible = True
        Lightning.lightning.append(self)

    def update():
        for lightning in Lightning.lightning:
            strength = randfloat(lightning.points[-1][1] - Clock.dt,
                                 lightning.points[-1][1] + Clock.dt)
            bounds = [-Clock.fps, Clock.fps]
            if randbool(20):
                lightning.angle += randfloat(-pi / 2, pi / 2)
            if pi < lightning.angle % (2 * pi) < pi / 4 * 3:
                bounds[0] = 0
            elif pi / 4 * 3 < lightning.angle % (2 * pi) < 2 * pi:
                bounds[1] = 0
            lightning.angle += randfloat(*bounds) / 50
            lightning.angle = ((lightning.angle + lightning.origin_angle) %
                               (2 * pi)) / 2
            coord = (lightning.points[-1][0][0] +
                     cos(lightning.angle) * strength * 3,
                     lightning.points[-1][0][1] +
                     sin(lightning.angle) * strength * 3)
            if strength < 0 or lightning.time + lightning.points[-1][
                    1] / 5 < Clock.time:
                lightning.kill()
            lightning.points.append((coord, strength))
            if randbool(50):
                lightning.visible = not lightning.visible
            if lightning.visible:
                lightning.draw()

    def draw(self):
        color = 240 + randint(0, 15) - (Clock.tick_last - self.time) * 200
        pygame.draw.lines(Window.surface, (color, color, color), False,
                          list(map(lambda l: l[0], self.points)),
                          max(int(self.points[0][1]), 1))

    def kill(self):
        Lightning.lightning.remove(self)
        del(self)

class Lightning:
    lightning = []

    def __init__(self, coord):
        self.origin = coord
        self.lines = [[(coord, randfloat(0.5, 5.0))]]
        self.angle = randfloat(0, pi)
        self.origin_angle = self.angle
        self.strongest = coord
        self.time = Clock.time
        self.visible = True
        Lightning.lightning.append(self)

    def update():
        for lightning in Lightning.lightning:
            strength = randfloat(lightning.lines[-1][-1][1] - Clock.dt,
                                 lightning.lines[-1][-1][1] + Clock.dt)
            bounds = [-Clock.fps, Clock.fps]
            if randbool(20):
                lightning.angle += randfloat(-pi / 2, pi / 2)
            if pi < lightning.angle % (2 * pi) < pi / 4 * 3:
                bounds[0] = 0
            elif pi / 4 * 3 < lightning.angle % (2 * pi) < 2 * pi:
                bounds[1] = 0
            lightning.angle += randfloat(*bounds) / 50
            lightning.angle = ((lightning.angle + lightning.origin_angle) %
                               (2 * pi)) / 2
            coord = (lightning.lines[-1][-1][0][0] +
                     cos(lightning.angle) * (strength + 3),
                     lightning.lines[-1][-1][0][1] +
                     sin(lightning.angle) * (strength + 3))
            if strength < 0 or lightning.time + lightning.lines[-1][-1][1] < Clock.time:
                lightning.kill()
            lightning.lines[-1].append((coord, strength))
            if strength > 5:
                lightning.strongest = coord
            if randint(0, 5):
                lightning.lines.append([(lightning.strongest, 5), (lightning.strongest, 5)])
                lightning.angle = randfloat(0, pi)
                lightning.origin_angle = lightning.angle
            if randbool(50):
                lightning.visible = not lightning.visible
            if lightning.visible:
                lightning.draw()

            world_coord = (int(coord[0] / World.tile_size), World.world_size[1] - int(coord[1] / World.tile_size))
            if World.valid(world_coord) and not World.world[world_coord] in (0, 1):
                Lightning.explode(*world_coord, strength)
                lightning.kill()

    def explode(x, y, strength):
        strength += 1
        for degree in range(0, 360, 10):
            radians = degree / 180 * pi
            for i in range(ceil(strength)):
                coord = (floor(cos(degree) * (strength / 2) + x), floor(sin(degree) * (strength / 2) + y))
                if World.valid(coord):
                    if i < ceil(strength) - 1:
                        World.world[coord] = randchoice((0, 3))
                        World.redraw[coord] = True
                    World.update(coord)

    def draw(self):
        color = max(150, min(255, 230 + randint(0, 10) - (Clock.time - self.time) * 100))
        for points in self.lines:
            pygame.draw.lines(Window.surface, (color + 15, color + 15, color), False,
                              list(map(lambda l: l[0], points)),
                              min(3, max(int(points[0][1]), 1)))

    def kill(self):
        if self in Lightning.lightning:
            Lightning.lightning.remove(self)


class World:
    tile_size = 10
    world_size = (Window.size[0] // tile_size + 1, Window.size[1] // tile_size + 1)
    world = numpy.zeros(world_size, dtype=int)
    velocity = numpy.zeros(world_size, dtype=int)
    update_tiles = numpy.zeros(world_size, dtype=bool)
    redraw = numpy.zeros(world_size, dtype=bool)
    surface = pygame.Surface(Window.size)
    surface.set_colorkey((0, 0, 0))

    def reset():
        World.world_size = (Window.size[0] // World.tile_size + 1, Window.size[1] // World.tile_size + 1)
        World.world = numpy.zeros(World.world_size, dtype=int)
        World.velocity = numpy.zeros(World.world_size, dtype=int)
        World.update_tiles = numpy.zeros(World.world_size, dtype=bool)
        World.redraw = numpy.zeros(World.world_size, dtype=bool)
        World.surface.fill((0, 0, 0))
        for x in range(World.world_size[0]):
            Material.create((x, 0), 9)

    def generate():
        for x in range(World.world_size[0]):
            Material.create((x, 0), 9)
        seed = randint(-10000, 10000)
        tree = 0
        for x in range(World.world_size[0]):
            stone = int(noise(x / 10, seed, -5, 5)) + World.world_size[0] // 8
            dirt = int(noise(x / 10, seed + 2, -5, 5)) + World.world_size[0] // 4

            for y in range(stone):
                Material.create((x, y), 9)
            if stone < dirt:
                for y in range(stone, dirt):
                    Material.create((x, y), 4)
            Material.create((x, y + 1), 6)
            if not randint(0, 10):
                Material.create((x, y + 2), 7)
            elif tree > 10:
                height = randint(4, 5)
                size = randint(3, height) // 2 * 2 + 2
                for i in range(size + 1):
                    for j in range(size + 1):
                        if not (i, j) in ((0, 0), (0, size), (size, 0), (size, size)):
                            Material.create((int(i + x - size / 2), int(j + y + 2 + height - size / 2)), 6)
                for i in range(height):
                    Material.create((x, y + 2 + i), 8)
                tree = 0
            else:
                tree += noise(x, seed, 0, 2)

    def spawn_tree(x, y):
        height = randint(4, 5)
        size = randint(3, height) // 2 * 2 + 2
        for i in range(size + 1):
            for j in range(size + 1):
                if not (i, j) in ((0, 0), (0, size), (size, 0), (size, size)):
                    Material.create((int(i + x - size / 2), int(j + y + height - size / 2)), 6)
        for i in range(height):
            Material.create((x, y + i), 8)

    def valid(coord):
        return 0 <= coord[0] < World.world_size[0] and 0 <= coord[
            1] < World.world_size[1]

    def update(coord):
        if World.valid(coord):
            World.update_tiles[coord] = True

    def _update(coord):
        if World.valid(coord):
            World.update_tiles[coord] = False
            

class Material:
    density = {1:  500,
               2:  1,
               3:  4,
               4:  3,
               5:  1
               }
    color = [(0, 0, 0),
             (100, 170, 255),
             (180, 220, 240),
             "Fire",
             (60, 40, 10),
             (130, 100, 60),
             (25, 140, 20),
             "Flower",
             (40, 10, 0),
             (60, 60, 60)
             ]
    name = ["Air",
            "Water",
            "Snow", 
            "Fire",
            "Dirt",
            "Dead",
            "Plant",
            "Flower",
            "Wood",
            "Stone"
            ]
    flowers = [(50, 120, 210),
               (140, 10, 170),
               (170, 50, 90),
               (210, 200, 60),
               (200, 110, 40),
               (100, 60, 220)
               ]
    fires = [(255, 186, 10),
             (255, 120, 10),
             (237, 100, 31),
             (171, 34, 0),
             (189, 32, 32),
             (117, 68, 0)
             ]

    def create(coord, material):
        if World.valid(coord) and (World.world[coord] == 0 or material == 0):
            World.world[coord] = material
            World.velocity[coord] = 0
            World.update_tiles[coord] = True
            World.redraw[coord] = True
            for x in range(-1, 2):
                for y in range(-1, 2):
                    World.update((x + coord[0], y + coord[1]))

    def update():
        for x, y in numpy.argwhere(World.update_tiles):
            World.update_tiles[x, y] = False
            if World.world[x, y] == 0 or World.world[x, y] == 9: # Air, Stone
                continue
            if World.world[x, y] == 1: # Water
                Material.update_fluid(x, y)
            elif World.world[x, y] in (2, 4, 5): # Snow, Dirt, Dead
                Material.update_powder(x, y)
                if World.world[x, y] == 2: # Snow
                    if randbool(int(Weather.temperature * 100)):
                        World.world[x, y] = 1
                        World.redraw[x, y], World.update_tiles[x, y] = True, True
                    elif World.valid((x, y + 2)) and World.world[x, y + 2] == 2:
                        World.world[x, y] = 0
                        World.redraw[x, y] = True
                        for coord in ((x, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)):
                            if World.valid(coord):
                                World.update(coord)
                elif World.world[x, y] == 4: # Dirt
                    if World.valid((x, y + 1)) and World.world[x, y + 1] == 1 and Weather.temperature > 0.4:
                        if not randint(0, 30):
                            World.world[x, y], World.world[x, y + 1] = 7, 0
                        else:
                            World.world[x, y], World.world[x, y + 1] = 6, 0
                        World.redraw[x, y], World.redraw[x, y + 1] = True, True
                        World.update_tiles[x, y], World.update_tiles[x, y + 1] = True, True
                    elif World.valid((x, y)) and World.valid((x, y + 2)) and World.world[x, y + 2] == 0 and World.valid((x - 4, y + 5)) and World.valid((x + 4, y + 5)) and World.world[x - 4, y + 5] == 0 and World.world[x + 4, y + 5] == 0 and Weather.temperature > 0.4 and not randint(0, 200):
                        World.spawn_tree(x, y)
                elif World.world[x, y] == 5: # Dead
                    if World.valid((x, y + 1)) and World.world[x, y + 1] == 1:
                        World.world[x, y], World.world[x, y + 1] = 4, 0
                        World.redraw[x, y], World.redraw[x, y + 1] = True, True
                        World.update_tiles[x, y], World.update_tiles[x, y + 1] = True, True
                    elif not randint(0, 5):
                        World.world[x, y] = 4
                        World.redraw[x, y] = True
                        World.update_tiles[x, y] = True
                    elif not randint(0, 2):
                        World.world[x, y] = 0
                        World.redraw[x, y] = True
                        World.update_tiles[x, y] = True
            elif World.world[x, y] == 3: # Fire
                Material.update_fire(x, y)
            elif World.world[x, y] in (6, 7, 8): # Plant, Flower, Wood
                Material.update_plant(x, y)
        for _ in range(int(5 * Clock.fps * Weather.temperature)):
            World.update(randcoord(*World.world_size))

    def update_powder(x, y):
        found = False
        destination = (x, y - 1)
        if randbool(int(80 * abs(Weather.wind))) and World.valid((x + copysign(1, Weather.wind), y)) and World.world[int(x + copysign(1, Weather.wind)), y] == 0:
            found = True
            destination = (int(x + copysign(1, Weather.wind)), y)
        elif World.valid(destination) and World.world[destination] <= 1 and randint(0, 100):
            found = True
            World.velocity[x, y] = Material.density[World.world[x, y]]
        elif World.world[x, y] == World.world[x, y - 1] and randbool(100 - min(100, Material.density[World.world[x, y]])):
            return
        else:
            if randint(0, 1):
                destination = (x + 1, y - 1)
            else:
                destination = (x - 1, y - 1)

            if World.valid(destination) and World.world[destination] == 0 and World.world[destination[0], destination[1] + 1] == 0:
                found = True
                World.velocity[x, y] = Material.density[World.world[x, y]]
            else:
                destination = (2 * x - destination[0], destination[1])
                if World.valid(destination) and World.world[destination] == 0 and World.world[destination[0], destination[1] + 1] == 0:
                    found = True
                    World.velocity[x, y] = Material.density[World.world[x, y]]
                elif World.velocity[x, y]:
                    if randint(0, 1):
                        destination = (x + 1, y)
                    else:
                        destination = (x - 1, y)
                    if World.valid(destination) and World.world[
                            destination] < World.world[x, y]:
                        found = True
                        World.velocity[x, y] -= 1
                    else:
                        destination = (2 * x - destination[0], destination[1])
                        if World.valid(destination) and World.world[
                                destination] < World.world[x, y]:
                            found = True
                            World.velocity[x, y] -= 1
        if found:
            replaced = (World.world[destination], World.velocity[destination])
            World.world[destination], World.world[x, y] = World.world[x, y], 0
            World.velocity[destination], World.velocity[x, y] = World.velocity[x, y], 0
            World.update(destination)
            for coord in ((x - 1, y + 1), (x, y + 1), (x + 1, y + 1), destination):
                if World.valid(coord) and World.world[coord] != 0:
                    World.update(coord)
            World.redraw[x, y] = True
            World.redraw[destination] = True
            if replaced[0] != 0:
                for coord in ((destination[0] - 1, destination[1]),
                              (destination[0] + 1, destination[1]),
                              (destination[0] + 1, destination[1] + 1),
                              (destination[0] - 1, destination[1] + 1),
                              (destination[0], destination[1] + 1)):
                    if World.valid(coord) and World.world[coord] == 0:
                        World.world[coord], World.velocity[coord] = replaced
                        World.update(coord)
                        break
        elif World.world[x, y] == 2 and randbool(int(Weather.temperature * 100)):
            World.world[x, y] = 1

    def update_fluid(x, y):
        destination = (x, y - 1)
        found = False
        if randbool(int(90 * abs(Weather.wind))) and World.valid((x + copysign(1, Weather.wind), y)) and World.world[int(x + copysign(1, Weather.wind)), y] == 0:
            found = True
            destination = (int(x + copysign(1, Weather.wind)), y)
        if World.valid(destination) and World.world[destination] == 0:
            found = True
            World.velocity[x, y] = Material.density[World.world[x, y]]
        elif World.valid((x + 1, y - 1)) and World.world[x + 1, y - 1] == 0 and World.world[x + 1, y]:
            found = True
            destination = (x + 1, y - 1)
        elif World.valid((x - 1, y - 1)) and  World.world[x - 1, y - 1] == 0 and World.world[x - 1, y]:
            found = True
            destination = (x - 1, y - 1)
        elif World.velocity[x, y]:
            if randint(0, 1):
                destination = (x + 1, y)
            else:
                destination = (x - 1, y)
            if World.valid(destination) and World.world[
                    destination] < World.world[x, y]:
                found = True
                World.velocity[x, y] -= 1
            else:
                destination = (2 * x - destination[0],
                                destination[1])
                if World.valid(destination) and World.world[
                        destination] < World.world[x, y]:
                    found = True
                    World.velocity[x, y] -= 1
            if found:
                n = x - destination[0]
                if World.valid((destination[0], destination[1] - 1)) and 0 < World.world[destination[0], destination[1] - 1] < 8 and World.valid((destination[0] + n, destination[1] - 1)) and World.world[destination[0] + n, destination[1] - 1] == 0:
                    World.world[destination[0] + n, destination[1] - 1], World.world[destination[0], destination[1] - 1] = World.world[destination[0], destination[1] - 1], 0
                    World.update_tiles[destination[0] + n, destination[1] - 1] = True
                    World.redraw[destination[0] + n, destination[1] - 1], World.redraw[destination[0], destination[1] - 1] = True, True
                if randint(0, 1):
                    for i in range(1, 3):
                        if World.valid((x + i * n, y)) and World.world[x + i * n, y] == 0:
                            destination = (x + i * n, y)
                        else:
                            break
        if found:
            World.world[destination], World.world[x, y] = World.world[x, y], 0
            World.velocity[destination], World.velocity[x, y] = World.velocity[x, y], 0
            World.update(destination)
            for coord in ((x - 1, y + 1), (x, y + 1), (x + 1, y + 1), destination):
                if World.valid(coord) and World.world[coord] != 0:
                    World.update(coord)
            World.redraw[x, y] = True
            World.redraw[destination] = True
        elif randbool(int(Weather.temperature * 100)):
            World.world[x, y], World.velocity[x, y] = 0, 0
            World.redraw[x, y] = True
            for coord in ((x - 1, y + 1), (x, y + 1), (x + 1, y + 1), destination):
                if World.valid(coord) and World.world[coord] != 0:
                    World.update(coord)
        elif Weather.temperature < 0.2 and not randint(0, 3) and World.valid((x, y + 1)) and World.world[x, y + 1] == 0 and World.world[x, y - 1] != 0:
            World.world[x, y] = 2
            World.redraw[x, y] = True
            World.update((x, y))

    def update_plant(x, y):
        dead = False
        plant_tiles = [(x, y)]
        found_dirt = False
        iterations = 0
        while (not found_dirt) and iterations < 50:
            found_new = False
            for tile in plant_tiles:
                for i, j in ((0, -1), (1, 0), (-1, 0), (0, 1)):
                    coord = (tile[0] + i, tile[1] + j)
                    if World.valid(coord):
                        if World.world[coord] in (6, 7, 8):
                            if not coord in plant_tiles:
                                found_new = True
                                plant_tiles.append(coord)
                                break
                        elif World.world[coord] == 4:
                            found_dirt = True
                if found_dirt:
                    break
            if not found_new:
                break
            iterations += 1
        if not found_dirt:
            dead = True
        if dead:
            World.world[x, y] = randchoice((0, 0, 5))
            World.redraw[x, y] = True
            for i, j in ((x, y), (x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)):
                if World.valid((i, j)):
                    World.update_tiles[i, j] = True
        elif World.valid((x, y + 1)) and not World.world[x, y + 1] in (0, 1, 6, 7, 8) and World.world[x, y] == 7:
            World.world[x, y] = 0
            World.redraw[x, y] = True
            World.update_tiles[x, y] = True

    def update_fire(x, y):
        dead = True
        for i, j in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
            if World.valid((i, j)) and World.world[i, j] in (2, 6, 7, 9):
                if not randint(0, 2 + [2, 6, 7, 9].index(World.world[i, j])):
                    if World.world[i, j] == 2:
                        World.world[i, j] = randchoice((0, 0, 0, 1, 3))
                    else:
                        World.world[i, j] = randchoice((0, 0, 0, 3, 3, 3, 3, 5))
                    World.redraw[i, j] = True
                dead = False
            if World.valid((i, j)) and World.world[i, j] == 1:
                dead = True
                break
        if World.valid((x, y - 1)) and World.world[x, y - 1] == 0:
            World.world[x, y - 1], World.world[x, y] = World.world[x, y], 0
            World.redraw[x, y] = True
            World.redraw[x, y - 1] = True
            World.update_tiles[x, y - 1] = True
        elif dead or randbool(100 - floor(Weather.temperature * 100)):
            World.world[x, y] = 0
            World.redraw[x, y] = True

    def draw():
        for x, y in numpy.argwhere(World.redraw):
            World.redraw[x, y] = False
            color = Material.color[World.world[x, y]]
            if color == "Flower":
                color = randchoice(Material.flowers)
            elif color == "Fire":
                color = randchoice(Material.fires)
                World.redraw[x, y] = True
            if color != (0, 0, 0):
                color = [min(255, max(0, color[i] + randint(-3, 3))) for i in range(3)]
            pygame.draw.rect(
                World.surface, color,
                (World.tile_size * x, Window.size[1] - World.tile_size * y,
                 World.tile_size, World.tile_size))
        Window.surface.blit(World.surface, (0, 0))
        

def main():
    selected = 0
    overlay = pygame.Surface(Window.size)

    b0 = ButtonSwitch(0, "Running", ("On", "Off"))
    b1 = ButtonSwitch(1, "Weather cycle", ("On", "Off"))
    b2 = ButtonSwitch(3, "Season", Weather.season_name)
    b3 = ButtonSwitch(4, "Weather", Weather.weather_name)
    b4 = ButtonSwitch(5, "Material", Material.name)
    b5 = ButtonSwitch(6, "Days per second", ("10", "5", "1", "0.5", "0.1", "0.05", "0.01"), 5)
    b6 = ButtonSwitch(7, "Block size", ("25", "20", "10", "5", "4", "2", "1"), 2)
    b7 = ButtonSwitch(8, "Reload", ("Generate", "Clear Blocks", "Reset"), -1)
    b8 = ButtonSwitch(2, "Weather Active", ("On", "Off"), 0)

    World.generate()

    Window.running = True
    while Window.running:
        if Weather.time_mult < 1 or not Weather.active:
            light = abs(Weather.day % 1 - 0.5) * 2
        else:
            light = 1
        Window.surface.fill((100 * light, 200 * light, 250 * light))
        mouse = (True in pygame.mouse.get_pressed(), pygame.mouse.get_pos())

        if b0.new:
            Weather.running = not b0.index
        elif b1.new:
            Weather.weather_cycle = not b1.index
        elif b2.new:
            Weather.start = -b2.index * 92 / Weather.time_mult + Clock.time - Weather.day % 1 / Weather.time_mult
        elif b3.new:
            Weather.fix = Weather.weather_conditions[b3.index]
            Weather.start_fix = Clock.time
        elif b4.new:
            selected = b4.index
        elif b5.new:
            Weather.time_mult = (10, 5, 1, 0.5, 0.1, 0.05, 0.01)[b5.index]
        elif b6.new:
            World.tile_size = (25, 20, 10, 5, 4, 2, 1)[b6.index]
            World.reset()
            World.generate()
            World.redraw.fill(True)
        elif b7.new:
            World.reset()
            if b7.index == 0:
                World.generate()
            if b7.index == 2:
                World.generate()
                Weather.seeds = [randint(-10000, 10000) for n in range(3)]
                Weather.start = Clock.time
            b7.index = -1
        elif b8.new:
            Weather.active = not b8.index

        b2.index = Weather.season
        b3.index = Weather.weather

        if mouse[0]:
            Material.create((mouse[1][0] // World.tile_size, World.world_size[1] - mouse[1][1] // World.tile_size - 1), selected)

        if Weather.active:
            Sun.update()
            Cloud.update()
            Weather.update()

        if Weather.running:
            Material.update()
        Material.draw()
        if Weather.active:
            Lightning.update()

        if Weather.active:
            Window.surface.fill((max(230 - 30 * abs(light - 0.5) * 2, 220), 220, 220), special_flags=BLEND_MIN)
            light = min(0.9, max(0.1, light / 4 * 3 + 0.25))
            Window.surface.fill((255 * light, 255 * light, 255 * light), special_flags=BLEND_MULT)

        ButtonSwitch.update()

        if Weather.active:
            draw_table((("FPS:", Clock.fps),
                    ("Day:", round(Weather.day, 3)),
                    ("Season:", Weather.season_name[Weather.season]),
                    ("Temperature:", round(Weather.temperature, 3)),
                    ("Weather:", Weather.weather_name[Weather.weather])
                    ), (600, 0))
        else:
            draw_table((("FPS:", Clock.fps),), (600, 0))

        for event in pygame.event.get():
            if event.type == QUIT:
                Window.quit()
            elif event.type == KEYDOWN:
                if event.key == K_r:
                    World.reset()
                    World.generate()
                if event.key == K_c:
                    World.reset()
        Clock.update()
        pygame.display.update()
    pygame.quit()


if __name__ == "__main__":
    main()
