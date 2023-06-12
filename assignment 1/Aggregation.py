import random
from enum import Enum, auto

import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
import math
from vi.config import Config, dataclass, deserialize


@deserialize
@dataclass
class AggregationConfig(Config):
    join_time: float = 101
    alignment_weight :float = 1
    cohesion_weight: float = 0.5
    separation_weight: float = 0.5
    avoid_crash_weight: float = 1
    safe_distance: float = 20

    delta_time: float = 3

    mass: int = 20

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Cockroach(Agent):
    config: AggregationConfig

    # def __init__(self):
    state = "wdr"
    join_time = 0
    join_e = 0.8
    #nei_still = 0

    def move(self):
        return self.move

    def separetion(self, neighbors):
        pos = [agent.pos for agent, len in neighbors]
        drift = Vector2(0,0)
        for neighbor in pos:
            diff = self.pos - neighbor
            if diff.length() < self.config.safe_distance:
                a = diff[0]
                b = diff[1]
                x = a * diff.length()/self.config.safe_distance
                y = b * diff.length()/self.config.safe_distance
                quotient = Vector2(a-x, b-y)
                drift += quotient
        return drift


                

    def change_position(self):
            # Pac-man-style teleport to the other end of the screen when trying to escape
            self.there_is_no_escape()

            neighbors = list(self.in_proximity_accuracy())

            self.separetion(neighbors)

            c = self.obstacle_intersections()

            adj = Vector2(0,0)
            leave_e = 0.001

            if self.on_site() and self.state == "wdr":
                x = random.random()
                if x < self.join_e:
                    self.move = -1*self.move#+Vector2(2,2)
                    adj += self.move*3
                else:
                    self.state = "join"
                    self.change_image(1)

            if self.state == "join":
                    self.join_time += 1
                    if self.join_time > self.config.join_time:
                        self.state = "still"
                        self.change_image(2)

            if self.state != "still":
                adj += self.separetion(neighbors)
                self.pos += self.move + adj


class Selection(Enum):
    ALIGNMENT = auto()
    COHESION = auto()
    SEPARATION = auto()


class AggregationLive(Simulation):
    selection: Selection = Selection.ALIGNMENT
    config: AggregationConfig
    def handle_event(self, by: float):
        if self.selection == Selection.ALIGNMENT:
           self.config.alignment_weight += by
        elif self.selection == Selection.COHESION:
            self.config.cohesion_weight += by
        elif self.selection == Selection.SEPARATION:
            self.config.separation_weight += by

    def before_update(self):
        super().before_update()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.handle_event(by=0.1)
                elif event.key == pg.K_DOWN:
                    self.handle_event(by=-0.1)
                elif event.key == pg.K_1:
                    self.selection = Selection.ALIGNMENT
                elif event.key == pg.K_2:
                    self.selection = Selection.COHESION
                elif event.key == pg.K_3:
                    self.selection = Selection.SEPARATION

        a, c, s = self.config.weights()


(
    AggregationLive(
        AggregationConfig(
            image_rotation=True,
            movement_speed=1,
            radius=50,
            seed=1,
        )
    )
    .spawn_site("images/bubble-full.png", x=350, y=350)
    #.spawn_obstacle("C:/Users/PTFaust/Desktop/images/bubble-full.png", 350, 350)
    .batch_spawn_agents(50, Cockroach, images=["images/white.png", 'images/red.png', 'images/green.png'])
    .run()
)
