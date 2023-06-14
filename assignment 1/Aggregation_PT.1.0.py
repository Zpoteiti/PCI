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
    max_still_time: float = 500
    safe_distance: float = 5
    max_velocity: float = 50
    s_noise = 0.3
    state = "wdr"
    join_time = 0
    still_time = 0
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
        neighbors = list(self.in_proximity_accuracy())
        # s_noise is the strong of the random drift
        # drift = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise)
        # when joining, the agent could wander outside of the site. if the agent is outside of the site, it will bounce back
        # if not self.on_site():
        #     self.move = Vector2(-self.move[0], -self.move[1])
        num_js = 0
        for agent, lenth in neighbors:
            if agent.state == "still" or agent.state == "join":
                num_js += 1
        if len(neighbors) > 0:
            debuff = 1/len(neighbors)
        else:
            debuff = 0

        buff = self.join_time / 100
        #当agent聚集时，new agent难以从聚集处进入site
        drift = -0.7*self.move - self.move * (debuff * 5 - buff)
        if drift.length() > (self.move * -1).length():
            drift = self.move * -0.7
        if len(neighbors) > 5 and self.move.length() < 0.01:
            self.state = "still"
            self.join_time = 0
        if len(neighbors) < 5 and self.join_time > self.max_join_time:
            self.state = "still"
            self.join_time = 0

        return drift

    # leaving the group and return a random drift
    def leave(self):
        self.change_image(2)

        # adding a random drift between (-s_noise, -s_noise) and (s_noise, s_noise) to the movement when leaving the group
        if self.move.length() < self.config.movement_speed*0.5:
            self.move = Vector2(random.random()*self.s_noise*2-self.s_noise, random.random()*self.s_noise*2-self.s_noise).normalize()*self.config.movement_speed
            drift = Vector2(0,0)
        else:
            drift = self.move
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
        # neighbors = list(self.in_proximity_accuracy())
        # x = []
        # for agent, length in neighbors:
        #     if agent.state == "still":
        #       x.append(agent)
        # neighbors = x
        # print(x)

        # x is the calculated additonal probability of leaving the group
        x = 0
        # count number of neighbours with state 'still'
        num_s = 0
        for agent, lenth in self.in_proximity_accuracy():
            if agent.state == 'still':
                num_s += 1
        # count number of neighbours with state 'join'
        num_j = 0
        for agent, lenth in self.in_proximity_accuracy():
            if agent.state == 'join':
                num_s += 1

        # count number of neighbours with state 'leave'
        num_l = 0
        for agent, lenth in self.in_proximity_accuracy():
            if agent.state == 'leave':
                num_s += 1

        num_w = 0
        for agent, lenth in self.in_proximity_accuracy():
            if agent.state == 'wdr':
                num_w += 1

        if not self.on_site():
            self.state = 'wdr'
            self.leave_chance = 0
            return False

        if len(list(self.in_proximity_accuracy())) > 0 and num_s < 3:
            self.still_time += 1
            if self.still_time > self.max_still_time:
                x = 1
            else:
                x = 0

        # if sees a neighbour with state 'join', reduce probability of leaving
        # if num_j > 0:
            x -= num_j
        # if sees a neighbour with state 'leave', increase probability of leaving
        # if num_l > 0:
            x += num_l
        # number of neighbours with state 'still' will be the scaler of the probability of leaving
        # which means more neighbours with state 'still', lower probability of leaving
        # if num_s > 0:
            #x = x * 1/num_s
            x -= num_s
            x += num_w
        if len(list(self.in_proximity_accuracy())) > 0 :
            x = x / len(list(self.in_proximity_accuracy()))

        # if len(neighbors) > 0:
        #     avg_pos = self.pos
        #     pos_list = []
        #     variance = 0
        #     for agent in neighbors:
        #         avg_pos += agent.pos
        #         pos_list.append(agent.pos)
        #     avg_pos = avg_pos / (len(neighbors)+1)
        #     for i in pos_list:
        #         variance += (i-avg_pos).length()
        #     variance = variance+(self.pos-avg_pos).length()/len(neighbors)+1
        #
        #     x = 1-variance/50
        else:
            self.still_time += 1
            if self.still_time > self.max_still_time:
                x = 1
            else:
                x = 0




        # make a random number between 0 and 1
        print(x)
        y = random.random()
        # if y is smaller than x, then leave
        if y < x:
            return True
        else:
            return False

    def change_position(self):
            neighbors = list(self.in_proximity_accuracy())
            drift = Vector2(0,0)

            self.there_is_no_escape()
            # Obstacle Avoidance
            obstacle_hit = pg.sprite.spritecollideany(self, self._obstacles, pg.sprite.collide_mask)  # type: ignore
            collision = bool(obstacle_hit)

            # Reverse direction when colliding with an obstacle.
            if collision:
                self.move.rotate_ip(90)
            

            # when wandering and hit sites
            if self.on_site() and self.state == "wdr": #and self.if_join():
                self.state = "join"
            # if do not want to join, then bounce back
            if not(self.on_site()) and self.state == "join": #and not self.if_join():
                self.state = "wdr"
                #self.move = Vector2(-self.move[0], -self.move[1])

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
            
            # self.move += drift
            
            # make sure agents won't move too fast
            if self.move.length() > self.max_velocity:
                self.move = self.move.normalize()*self.max_velocity
                    
            # move
            self.pos += self.move + self.separetion(neighbors) + drift

(
    Simulation(
        AggregationConfig(
            image_rotation=False,
            visualise_chunks=False,
            movement_speed=7,
            radius=50,
            seed=1)
    )
    # spawn screen's edge
    #.spawn_obstacle("images/obstacle.png", x=375, y=375)
    # spawn sites
    .spawn_site("images/triangle@50px.png", x=100, y=100)
    .spawn_site("images/triangle@200px.png", x=600, y=600)
    # spawn agents
    .batch_spawn_agents(50, Cockroach, images=["images/white.png", 'images/red.png', 'images/blue.png', 'images/green.png'])
    
    # run simulation
    .run()
)
