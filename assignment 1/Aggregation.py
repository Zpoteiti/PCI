import random
from enum import Enum, auto

import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
import math
from vi.config import Config, dataclass, deserialize


@deserialize
@dataclass
class FlockingConfig(Config):
    join_time: float = 50
    alignment_weight :float = 1
    cohesion_weight: float = 0.5
    separation_weight: float = 0.5
    avoid_crash_weight: float = 1
    total_population: int = 50

    delta_time: float = 3

    mass: int = 20

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig

    # def __init__(self):
    state = "wdr"
    join_time = 0
    leave_time = 0
    join_e = 0.8
    leave_cross = True
    first_cross = True


    def move(self):
        return self.move

    def to_join(self,adj):
        x = random.random()
        if x < self.join_e:
            self.move = -1 * self.move  # +Vector2(2,2)
            adj += self.move * 3
            # print("wdr not joining.")
        else:
            self.state = "join"

        return adj

    def join_state(self,adj):
        self.join_time += 1
        if self.on_site():
            self.move = -1 * self.move
            adj += self.move.normalize() * 5
            print("adj ", adj)
        if self.join_time > self.config.join_time:
            self.state = "still"
            self.join_time = 0
        else:
            self.pos += self.move + adj
            print(self.pos)

    def to_leave(self):
            neighbors = list(self.in_proximity_accuracy())
            if len(neighbors) > 0:
                still_num = 0
                for agent, distance in neighbors:
                    if agent.state == "still":
                        still_num += 1
                still_ratio = still_num/len(neighbors)
                neighbor_ratio = len(neighbors)/self.config.total_population
                leave_e = (still_ratio + neighbor_ratio)/2
            else:
                leave_e = 0.3

            x = random.random()
            if x > leave_e:
                self.state == "leave"


    def leave_state(self):
            self.leave_time += 1
            if self.on_site() and self.leave_cross:
                self.leave_cross = False
            self.pos += self.move


    def change_position(self):
            # Pac-man-style teleport to the other end of the screen when trying to escape
            self.there_is_no_escape()



            #c = self.obstacle_intersections()

            adj = Vector2(0,0)
            leave_e = 0.001
            #if self.state != "still":


            if not(self.first_cross) and self.on_site() and self.state == "wdr":
                adj = self.to_join(adj)

            if self.state == "join":
                    self.join_state(adj)

            if self.state == "still":
                    self.to_leave()

            if self.state == "leave":
                    self.leave_state()
            #print(self.join_time)
            #print(self.state)

            if self.first_cross and self.on_site():
                self.first_cross = False
                adj += self.move*10

            if self.state == "wdr":
                self.pos += self.move + adj*3
            # if self.state == "join":
            #     self.pos += self.move






                #END CODE -----------------


class Selection(Enum):
    ALIGNMENT = auto()
    COHESION = auto()
    SEPARATION = auto()


class FlockingLive(Simulation):
    selection: Selection = Selection.ALIGNMENT
    config: FlockingConfig
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
        #print(f"A: {a:.1f} - C: {c:.1f} - S: {s:.1f}")


(
    FlockingLive(
        FlockingConfig(
            image_rotation=True,
            movement_speed=1,
            radius=50,
            seed=1,
        )
    )
    .spawn_site("images/bubble-full.png", x=350, y=350)
    #.spawn_obstacle("C:/Users/PTFaust/Desktop/images/bubble-full.png", 350, 350)
    .batch_spawn_agents(50, Bird, images=["images/bird.png"])
    .run()
)
