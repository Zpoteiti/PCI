import random
from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
import math
from vi.config import Config, dataclass, deserialize

class AggregationConfig(Config):
    pass

class Cockroach(Agent):
    config: AggregationConfig

    max_join_time: float = 101
    safe_distance: float = 10
    max_velocity: float = 1
    s_noise = 0.01
    state = "wdr"
    join_time = 0
    join_e = 0.2
    leave_e = 0.001

    def separetion(self, neighbors):
        # Separation to avoid overlapping
        pos = [agent.pos for agent, len in neighbors]
        drift = Vector2(0,0)
        for neighbor in pos:
            diff = self.pos - neighbor
            if diff.length() < self.safe_distance:
                a = diff[0]
                b = diff[1]
                x = a * diff.length()/self.safe_distance
                y = b * diff.length()/self.safe_distance
                quotient = Vector2(a-x, b-y)
                drift += quotient
        return drift

    # joining the group and return a random drift
    def join(self):
        self.change_image(1)
        self.join_time += 1
        # s_noise is the strong of the random drift
        drift = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise)
        # when joining, the agent could wander outside of the site. if the agent is outside of the site, it will bounce back
        if not self.on_site():
            self.move = Vector2(-self.move[0], -self.move[1])
        if self.join_time > self.max_join_time:
            self.state = "still"
            self.join_time = 0
        return drift

    # leaving the group and return a random drift
    def leave(self):
        self.change_image(2)
        # adding a random drift between (-s_noise, -s_noise) and (s_noise, s_noise) to the movement when leaving the group
        drift = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise)
        # if the agent is on the site, change state to wandering, in order to prevent the agent from stuck in group canter
        if not self.on_site():
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
        x = random.uniform(0, 1)
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
            neighbors = list(self.in_proximity_accuracy())
            drift = Vector2(0,0)

            # # when wdr and hit obstacle(edge of playground)
            # if self.on_obstacle() and self.state == "wdr":
            #     self.move = Vector2(-self.move[0], -self.move[1])

            # when wandering and hit sites
            if self.on_site() and self.state == "wdr" and self.if_join():
                self.state = "join"
            # if do not want to join, then bounce back
            elif self.on_site() and self.state == "wdr" and not self.if_join():
                pass# self.move = Vector2(-self.move[0], -self.move[1])                

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
            if self.move.length() > self.max_velocity:
                self.move = self.move.normalize()*self.max_velocity
                    
            # move
            self.pos += self.move + self.separetion(neighbors)

(
    Simulation(
        AggregationConfig(
            image_rotation=False,
            visualise_chunks=False,
            movement_speed=1,
            radius=50,
            seed=1)
    )
    # spawn screen's edge
    .spawn_obstacle("images/obstacle.png", x=375, y=375)   
    # spawn sites
    .spawn_site("images/triangle@50px.png", x=100, y=100)
    .spawn_site("images/triangle@200px.png", x=600, y=600)
    # spawn agents
    .batch_spawn_agents(50, Cockroach, images=["images/white.png", 'images/red.png', 'images/blue.png', 'images/green.png'])
    
    # run simulation
    .run()
)
