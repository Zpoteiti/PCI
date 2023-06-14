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
    safe_distance: float = 5
    max_velocity: float = 5
    s_noise = 0.3
    state = "wdr"
    join_time = 0
    join_e = 0.2
    join_max = 0.8
    leave_chance = 0
    patience = 200

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
        # x is the calculated probability of joining the group
        x = 0
        # count number of neighbours with state 'still'
        num_s = 0

        for agent, len in self.in_proximity_accuracy():
            if agent.state == 'still':
                num_s += 1


        # probability of join is highly influenced by the number 
        # of neighbors with state 'still' more neighbors with 
        # state 'still', lower probability of joining
        if num_s == 0:
            x = self.join_max
        else:
            x = self.join_max * 1/num_s

        # make a random number between 0 and 1
        y = random.random()
        # if y is smaller than x, then join
        if y < x:
            return True
        else:
            return False
    
    # probability of leave increase overtime
    # if sees a neighbour with state 'join', reduce probability of leaving
    # if sees a neighbour with state 'leave', highly increase probability of leaving
    # 1/(number of neighbours with state 'still') will be the scaler of the probability of leaving
    # which means more neighbours with state 'still', lower probability of leaving
    # if get crashed out of the site, then start wandering
    def if_leave(self): 
        # x is the calculated additonal probability of leaving the group
        x = 0.0001
        # count number of neighbours with state 'still'
        num_s = 0
        for agent, len in self.in_proximity_accuracy():
            if agent.state == 'still':
                num_s += 1
        # count number of neighbours with state 'join'
        num_j = 0
        for agent, len in self.in_proximity_accuracy():
            if agent.state == 'join':
                num_s += 1

        # count number of neighbours with state 'leave'
        num_l = 0
        for agent, len in self.in_proximity_accuracy():
            if agent.state == 'leave':
                num_s += 1

        if not self.on_site():
            self.state = 'wdr'
            self.leave_chance = 0
            return False

        # if sees a neighbour with state 'join', reduce probability of leaving
        if num_j > 0:
            x -= num_j*0.3
        # if sees a neighbour with state 'leave', increase probability of leaving
        if num_l > 0:
            x += num_l*0.7

        # add the additional probability to the base probability
        self.leave_chance += x

        # make a random number between 0 and 1
        y = random.random()
        # if y is smaller than x, then leave
        if y < self.leave_chance/(num_s+1):
            self.leave_chance = 0
            return True
        else:
            return False

    def change_position(self):
            neighbors = list(self.in_proximity_accuracy())
            drift = Vector2(0,0)

            # Obstacle Avoidance
            obstacle_hit = pg.sprite.spritecollideany(self, self._obstacles, pg.sprite.collide_mask)  # type: ignore
            collision = bool(obstacle_hit)

            # Reverse direction when colliding with an obstacle.
            if collision:
                self.move.rotate_ip(90)
            

            # when wandering and hit sites
            if self.on_site() and self.state == "wdr" and self.if_join():
                self.state = "join"
            # if do not want to join, then bounce back
            elif self.on_site() and self.state == "wdr" and not self.if_join():
                self.move = Vector2(-self.move[0], -self.move[1])                

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
