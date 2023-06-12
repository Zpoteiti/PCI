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
    max_join_time: float = 101
    alignment_weight :float = 1
    cohesion_weight: float = 0.5
    separation_weight: float = 0.5
    avoid_crash_weight: float = 1
    safe_distance: float = 10
    max_velocity: float = 1

    delta_time: float = 3

    mass: int = 20

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Cockroach(Agent):
    config: AggregationConfig

    s_noise = 0.2
    state = "wdr"
    join_time = 0
    join_e = 0.5
    leave_e = 0.001

    def move(self):
        return self.move

    def separetion(self, neighbors):
        # Separation to avoid overlapping
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

    # joining the group and return a random drift
    def join(self):
        self.change_image(1)
        self.join_time += 1
        # s_noise is the strong of the random drift
        # adding a random drift between (-s_noise, -s_noise) and (s_noise, s_noise) to the movement when joining the group
        drift = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise)
        # if join time is over the threshold, change state to still
        if self.join_time > self.config.max_join_time:
            self.state = "still"
            self.join_time = 0
        return drift

        
    # leaving the group and return a random drift
    def leave(self):
        self.change_image(2)
        # adding a random drift between (-s_noise, -s_noise) and (s_noise, s_noise) to the movement when leaving the group
        drift = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise)
        # if the agent is on the site, change state to wandering, in order to prevent the agent from stuck in group canter
        if self.on_site():
            self.state = "wdr"
        return drift
    
    # wandering around
    def wandering(self):
        # random drift
        self.change_image(0)
        # adding a random drift between (-s_noise, -s_noise) and (s_noise, s_noise) to the movement when wandering
        drift = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise)
        return drift

    # stay at the same position
    def still(self):
        self.change_image(3)
        self.move = Vector2(0,0)
        return Vector2(0,0)
    
    # decide if agent should join the group
    def if_join(self):
        x = random.random()
        if x < self.join_e:
            return True
        else:
            return False
    
    # decide if agent should leave the group
    def if_leave(self):
        x = random.random()
        if x < self.leave_e:
            # give the agent a random velocity bewtween (-1,-1) and (1,1) to leave the group
            self.move = Vector2(random.random()*2-1, random.random()*2-1)
            return True
        else:
            return False


    def change_position(self):
            # Pac-man-style teleport to the other end of the screen when trying to escape
            self.there_is_no_escape()
            neighbors = list(self.in_proximity_accuracy())
            c = self.obstacle_intersections()
            drift = Vector2(0,0)

            # when wandering and hit a obstacle
            if self.on_site() and self.state == "wdr" and self.if_join():
                self.state = "join"
            
            # when joining and hit a obstacle，reflect
            # !!!
            if self.on_site() and self.state == "join":
                x = self.move[0]
                y = self.move[1]
                self.move = Vector2(-x, -y)

            # when still but want to leave
            if self.state == 'still' and self.if_leave():
                self.state = "leave"
            
            # state decided and change position
            if self.state == "join":
                drift = self.join()
            elif self.state == "leave":
                drift = self.leave()
            elif self.state == "wdr":
                drift = self.wandering()
            elif self.state == "still":
                drift = self.still()
            
            self.move += drift
            
            # make sure agents won't move too fast
            if self.move.length() > self.config.max_velocity:
                self.move = self.move.normalize()*self.config.max_velocity
                    
            # move
            self.pos += self.move + self.separetion(neighbors)
                


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
    .batch_spawn_agents(50, Cockroach, images=["images/white.png", 'images/red.png', 'images/blue.png', 'images/green.png'])
    .run()
)
