import random
from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
import math
from vi.config import Config, dataclass, deserialize

class NatureConfig(Config):
    rabbit_reproduction_rate = 0.001
    fox_die_rate = 0.001
    eat_range = 10
    noise_strength = 0.2

# adding noise to the movement to aviod agents moving in a straight line and overlapping
# range from -noise_strength to 0.noise_strength
def noise():
    return Vector2(random.random()*2-1, random.random()*2-1)

class Rabbit(Agent):
    config: NatureConfig
    speed = 1

    # run away from the nearest fox at heighest speed
    def run_away_from_fox(self):
        fox = (
            self.in_proximity_accuracy()
            .filter_kind(Fox)
            .first()
        )
        if fox is not None:
            # move away from the fox    
            self.move = self.pos - fox[0].pos
            self.move.scale_to_length(self.speed)

    def change_position(self):
        self.there_is_no_escape()
        
        # run away from the nearest fox at heighest speed
        self.run_away_from_fox()
        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        # rabbit reproduce
        if random.random() < self.config.rabbit_reproduction_rate:
            self.reproduce()
        # move
        self.move += noise()
        self.pos += self.move
        

class Fox(Agent):
    config: NatureConfig
    round = 0
    speed = 2

    # chaseing the nearest rabbit at heighest speed
    def chase_rabbit(self):
        rabbit = (
            self.in_proximity_accuracy()
            .filter_kind(Rabbit)
            .first()
        )
        if rabbit is not None:
            # move towards the rabbit
            self.move = rabbit[0].pos - self.pos
            self.move.scale_to_length(self.speed)

    # eat the nearest rabbit in eat range
    def eat(self):
        rabbit = (
            self.in_proximity_accuracy()
            .filter_kind(Rabbit)
            .first()
        )
        # eat the rabbit and reproduce if it's in eat range
        if rabbit is not None and self.pos.distance_to(rabbit[0].pos) < self.config.eat_range:
            rabbit[0].kill()
            self.reproduce()     
            
    def change_position(self):
        self.there_is_no_escape()
        self.round += 1      

        # fox die
        if random.random() < self.config.fox_die_rate:
            self.kill()
        # chaseing the nearest rabbit at heighest speed
        self.chase_rabbit()
        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        # eat the nearest rabbit in eat range
        self.eat()
        # move
        self.move += noise()
        self.pos += self.move
            

(
    Simulation(
        NatureConfig(
            image_rotation=False,
            visualise_chunks=False,
            movement_speed=1,
            radius=200,
            seed=2)
    )
    # spawn agents
    .batch_spawn_agents(1, Rabbit, images=["images/rabbit.png"])
    .batch_spawn_agents(1, Fox, images=["images/fox.png"])
    
    # run simulation
    .run()
)
