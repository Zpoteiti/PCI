import random
from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation,TimeMachine
import matplotlib.pyplot as plt
from vi.config import Config, dataclass, deserialize

class NatureConfig(Config):
    rabbit_reproduction_rate = 0.001
    fox_die_rate = 0.001
    eat_range = 10
    noise_strength = 0.2
    energy = 2000
    energy_switch = True
    rabbit_num = 0
    fox_num = 0
    round = ""
    time = 0
    population_history = [[20,5,0],[20,5,1]]# [rabbit,fox,time]

# adding noise to the movement to avoid agents moving in a straight line and overlapping
# range from -noise_strength to 0.noise_strength
def noise():
    return Vector2(random.random()*2-1, random.random()*2-1)

def show(population):
    plt.style.use('seaborn-whitegrid')

    time = []
    fox = []
    rabbit = []
    for i in population:
        time.append(i[2])
        rabbit.append(i[0])
        fox.append(i[1])
    plt.plot(time, fox, '-', label='fox')
    plt.plot(time, rabbit, '-', label='rabbit')

    plt.title('population')
    plt.xlabel('time')
    plt.ylabel('population_number')

    plt.pause(0.00000000000000001)



class Rabbit(Agent):
    config: NatureConfig
    speed = 1
    count = True


    # run away from the nearest fox at highest speed
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
        if self.config.round == "fox":
            self.config.round = "wait"
        else:
            self.config.round = "rabbit"

        if self.count:
            self.count = False
            self.config.rabbit_num += 1

        self.there_is_no_escape()
        
        # run away from the nearest fox at highest speed
        self.run_away_from_fox()
        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        # rabbit reproduce
        if random.random() < self.config.rabbit_reproduction_rate:
            self.reproduce()
            print("new rabbit!")
            self.config.rabbit_num += 1
        # move
        self.move += noise()
        self.pos += self.move

        rabbit = self.config.rabbit_num
        fox = self.config.fox_num
        time = self.config.time
        population = self.config.population_history

        # if (rabbit != population[-1][0] or fox != population[-1][1]) and time > 1:
        if time // 40 == 0 and time > 1:
            self.config.population_history.append([rabbit,fox,time])

        #oprint(self.config.population_history)
        show(self.config.population_history)
        print("rabbit:", self.config.rabbit_num, "time",self.config.time)
        

class Fox(Agent):
    config: NatureConfig
    round = 0
    speed = 2
    energy = NatureConfig.energy
    count = True

    # chasing the nearest rabbit at highest speed
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
            self.config.rabbit_num -= 1
            self.energy = self.config.energy
            self.reproduce()
            self.config.fox_num += 1

            
    def change_position(self):
        if self.config.round == "rabbit":
            self.config.round = "fox"
            self.config.time += 1

        if self.count:
            self.count = False
            self.config.fox_num += 1

        self.there_is_no_escape()
        self.round += 1
        self.energy -= 1

        if self.energy < 0 and self.config.energy_switch:
            self.kill()
            self.config.fox_num -= 1
        # fox die
        if random.random() < self.config.fox_die_rate:
            self.kill()
            self.config.fox_num -= 1
        # chasing the nearest rabbit at highest speed
        self.chase_rabbit()
        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        # eat the nearest rabbit in eat range
        self.eat()
        # move
        self.move += noise()
        self.pos += self.move
        rabbit = self.config.rabbit_num
        fox = self.config.fox_num
        time = self.config.time
        population = self.config.population_history

        # if (rabbit != population[-1][0] or fox != population[-1][1]) and time > 1 :
        if time % 20 == 0 and time > 1:
            self.config.population_history.append([rabbit,fox,time])
        show(self.config.population_history)
        print("fox:", self.config.fox_num, "time",self.config.time)
        #print(self.config.population_history)
            

(
    Simulation(
        NatureConfig(
            image_rotation=False,
            visualise_chunks=False,
            movement_speed=1,
            radius=50,
            seed=2)
    )
    # spawn agents
    .batch_spawn_agents(20, Rabbit, images=["images/rabbit.png"])
    .batch_spawn_agents(5, Fox, images=["images/fox.png"])
    
    # run simulation
    .run()
)
