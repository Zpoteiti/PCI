from enum import Enum, auto

import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
import math
from vi.config import Config, dataclass, deserialize


@deserialize
@dataclass
class FlockingConfig(Config):
    alignment_weight: float = 0.5
    cohesion_weight: float = 0.5
    separation_weight: float = 10
    safe_distance: float = 15

    delta_time: float = 3

    mass: int = 20

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig

    def move(self):
        return self.move

    def rule_1(self, neighbors):
        speeds = [agent.move for agent, len in neighbors]
        #calculate Aligenment
        speed_sum = Vector2(0,0)
        for speed in speeds:
            speed_sum += speed
        a = (1/abs(len(neighbors))) * speed_sum
        alignment = self.config.alignment_weight*a
        return alignment

    def rule_2(self, neighbors):
        #calculate Cohesion
        pos = [agent.pos for agent, len in neighbors]
        pos_sum = Vector2(0,0)
        for i in pos:
            pos_sum += i
        p = pos_sum/abs(len(neighbors))
        
        fc = (p - self.pos)
        c = fc - self.move
        cohesion = self.config.cohesion_weight*c
        return cohesion
    
    def rule_3(self, neighbors):
        #calculate separation
        pos = [agent.pos for agent, len in neighbors]
        p = Vector2(0,0)
        sum = Vector2(0,0)
        count = 1
        for i in pos:
            if abs((self.pos - i).length()) < self.config.safe_distance:
                sum += (self.pos - i) 
                count += 1 
        p = sum/count
            # diff = self.pos - i
            # if abs(diff.length()) < self.config.safe_distance:
            #     p -= diff
        separation = self.config.separation_weight*p
        return separation


    def change_position(self):
        # Pac-man-style teleport to the other end of the screen when trying to escape
        self.there_is_no_escape()

        neighbors = list(self.in_proximity_accuracy())
        max_velocity = 5

        #when no neighbors, walk straight
        f_total = Vector2(0,0)

        if len(neighbors) != 0:
            a =c = s = Vector2(0,0)
            a = self.rule_1(neighbors)
            c = self.rule_2(neighbors)
            s = self.rule_3(neighbors)
            print(a,c,s,'a,c,s')

            # Calculate final steering force
            f_total = (a + c + s) /self.config.mass

        # Apply steering force to velocity
        self.move = f_total + self.move

        # update movements
        if self.move.length() > max_velocity:
            self.move = self.move.normalize()*max_velocity
        self.pos += self.move


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
        # print(f"A: {a:.1f} - C: {c:.1f} - S: {s:.1f}")


(
    FlockingLive(
        FlockingConfig(
            image_rotation=True,
            movement_speed=1,
            radius=50,
            seed=1,
        )
    )
    .batch_spawn_agents(50, Bird, images=["images/bird.png"])
    .run()
)
