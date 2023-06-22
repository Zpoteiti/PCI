import random
from enum import Enum, auto
import pygame as pg
import numpy
from pygame.math import Vector2
from vi import Agent, Simulation,TimeMachine
import matplotlib.pyplot as plt
from vi.config import Config, dataclass, deserialize
import polars as pl






class NatureConfig(Config):
    # rabbit
    rabbit_max_speed: float = 1
    #rabbit_hungry_thershold: float = 50
    rabbit_pregnant_time : int = 600

    rabbit_starving_thershold: float = 605
    rabbit_reproduction_rate: float = 0.005

    # fox
    fox_die_rate: float = 0.005
    fox_max_speed: float = 2

    fox_reproduction_rate: float = 1

    fox_pregnant_time: int = 10
    fox_starving_thershold: float = 700
    #fox_die_rate = 0.001
    # grass
    grass_reproduction_rate: float = 0.005
    #fox_genotype = [[]]

    adult_threshold = 0.5 * rabbit_starving_thershold
    hungry_thershold: float = 0.4
    eat_range = 10
    safe_distance: float = 10
    noise_strength = 0.2
    energy_switch = True    # a switch to turn on the energy check

    #below are parameters for counting population
    rabbit_num = 0
    fox_num = 0
    grass_num = 0




# adding noise to the movement to avoid agents moving in a straight line and overlapping
# range from -noise_strength to 0.noise_strength
def noise():
    return Vector2(random.random()*2-1, random.random()*2-1)




class Rabbit(Agent):
    config: NatureConfig
    speed: float = 1.4
    hungry_counter: int = 0
    pregnant_counter: int = 0
    states = ["fine","child"]
    growth: int = 0
    #a parameter count the initial population
    count = True

    # def cave(self):
    #     if self.on_site():
    #         if hide > threshhold:
    #             self.state = "in cave"


    def separetion(self, neighbors):
        pos = [agent.pos for agent, len in neighbors]
        drift = Vector2(0, 0)
        for neighbor in pos:
            diff = self.pos - neighbor
            if diff.length() < self.config.safe_distance:
                a = diff[0]
                b = diff[1]
                x = a * diff.length() / self.config.safe_distance
                y = b * diff.length() / self.config.safe_distance
                quotient = Vector2(a - x, b - y)
                drift += quotient
        self.pos += drift

    def update(self):
        self.save_data("type", "rabbit")
        self.save_data("rabbit", self.config.rabbit_num)
        self.save_data("grass", None)
        self.save_data("fox", None)
        self.save_data("energy", "None")


    # run away from the nearest fox at highest speed
    def run_away_from_fox(self, fox):
            self.move = self.pos - fox[0].pos
            self.move.scale_to_length(self.speed)


        # when not hungry, go to average position of nearby grasses
    def grass_around_me(self, grasses):
        n = len(grasses)
        if n > 0:
            # move towards the average position of nearby grasses
            average_pos = Vector2(0, 0)
            for i in range(n):
                grass = grasses[i]
                average_pos += grass[0].pos
            average_pos = average_pos / n
            self.move = average_pos - self.pos
            self.move.scale_to_length(self.speed)

    # def tired(self):
    #     if "hungry" in self.states:
    #     #self.hungry_counter += 1
    #     #if self.hungry_counter >= 300:
    #     #    self.kill()
    #     # elif self.hungry_counter <= 200:
    #     #     self.max_speed = self.config.rabbit_max_speed
    #     # elif self.hungry_counter > 200 and self.hungry_counter < 300:
    #         self.speed = self.config.rabbit_max_speed * 0.5

    def chase(self, grass):
        if grass is not None:
            # move towards the rabbit
            self.move = grass[0].pos - self.pos
            self.move.scale_to_length(self.speed)

    def eat(self, grass):
        if grass is not None and self.pos.distance_to(grass[0].pos) < self.config.eat_range:
            grass[0].kill()
            self.config.grass_num -= 1
            #self.hungry_counter -= 0.3 * self.config.hungry_thershold
            self.hungry_counter = 0

    # def get_pregnent(self):
    #     if self.pregnent == False and self.hungry_counter < self.config.rabbit_hungry_thershold and random.random() < self.config.rabbit_reproduction_rate:
    #         self.pregnent = True
    #
    #
    #     if self.pregnent == True:
    #         self.pregnant_counter += 1
    #
    #     # rabbit reproduce when reach 28 days
    #     if self.pregnant_counter >= self.config.rabbit_pregnant_time:
    #         # give birth to 4-12 babies
    #         for i in range(random.randint(4, 12)):
    #             self.reproduce()
    #             self.config.rabbit_num += 1
    #         self.pregnant_counter = 0
    #         self.pregnent = False

    def pregnant(self,near_rabbits):
        for i in near_rabbits:
            if "fine" in i[0].states and "pregnant" not in i[0].states and random.random() < self.config.rabbit_reproduction_rate and "fine" in self.states and "pregnant" not in self.states:
                self.states.append("pregnant")

        if "pregnant" in self.states:
            self.change_image(1)

        if "pregnant" in self.states:
            self.pregnant_counter += 1
            if self.pregnant_counter > self.config.rabbit_pregnant_time:
                self.states.remove("pregnant")
                self.change_image(0)
                for i in range(random.randint(3, 6)):
                    self.reproduce()
                    self.config.rabbit_num += 1

    # hungry state function
    def hungry(self):
        if self.hungry_counter > self.config.rabbit_starving_thershold * self.config.hungry_thershold:
            self.states = ["hungry" if i == "fine" else i for i in self.states]
        else:
            self.states = ["fine" if i == "hungry" else i for i in self.states]

    def danger(self,nearest_fox):
        if nearest_fox is not None and "in danger" not in self.states:
            self.states.append("in danger")
        elif nearest_fox is None and "in danger" in self.states:
            self.states.remove("in danger")

    def grow_up(self):
        self.growth += 1
        if self.growth > self.config.adult_threshold and "child" in self.states:
            self.states.remove("child")


    def change_position(self):
        if self.count:
            self.count = False
            self.config.rabbit_num += 1

        self.there_is_no_escape()


        # local info of nearby agents
        nearest_fox = (self.in_proximity_accuracy().filter_kind(Fox).first())
        nearest_grass = (self.in_proximity_accuracy().filter_kind(Grass).first())
        nearby_grass = list(self.in_proximity_accuracy().filter_kind(Grass))
        nearby_rabbits = list(self.in_proximity_accuracy().filter_kind(Rabbit))


        # basic habbits
        self.there_is_no_escape()
        self.hungry_counter += 1
        # self.tired()

        self.separetion(nearby_rabbits)

        #states check
        self.hungry()
        self.danger(nearest_fox)
        if "child" in self.states:
            self.grow_up()


        # senarios
        # see foxes
        #self.run_away_from_fox(nearest_fox)

        # hungry and see no grass
        if "hungry" in self.states:
            self.chase(nearest_grass)

        # eat grass when hungry
        if "hungry" in self.states:
            self.eat(nearest_grass)     #only eat when hungry?

        # not hungry and see grass
        elif "in danger" not in self.states and self.hungry_counter <= self.config.rabbit_starving_thershold * self.config.hungry_thershold:
            pass#self.grass_around_me(nearby_grass)

        if "in danger" not in self.states and "child"not in self.states:
            self.pregnant(nearby_rabbits)



        # run away from the nearest fox at highest speed
        if "in danger" in self.states:
            self.run_away_from_fox(nearest_fox)
            ##### we can set a danger mode speed as well

        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        print("rr",self.states)
        # move
        self.move += noise()
        self.pos += self.move



class Fox(Agent):
    config: NatureConfig
    speed = 2
    hungry_counter = 0
    pregnant_counter = 0
    #growth_counter = 0
    count = True
    states = ["fine","child"]

    def update(self):
        self.save_data("type", "fox")
        self.save_data("rabbit", None)
        self.save_data("grass", None)
        self.save_data("fox", self.config.fox_num)
        self.save_data("energy",self.hungry_counter)



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
            if "hungry" in self.states:
                self.move.scale_to_length(self.config.fox_max_speed)
            else:
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
            self.hungry_counter = 0
            if "pregnant" not in self.states and random.random() < self.config.fox_reproduction_rate:
                self.states.append("pregnant")


    def hungry(self):
        if self.hungry_counter > self.config.fox_starving_thershold * self.config.hungry_thershold:
            self.states = ["hungry" if i == "fine" else i for i in self.states]
            # hungry state can run max speed when chasing.

    def pregnant(self,near_foxes):
        # if "fine" in self.states and "pregnant" not in self.states:
        #     for i in near_foxes:
        #         if "fine" in i[0].states and "pregnant" not in i[0].states and random.random() < self.config.fox_reproduction_rate:
        #             self.states.append("pregnant")
        if "pregnant" in self.states:
            self.pregnant_counter += 1
            if self.pregnant_counter > self.config.fox_pregnant_time:
                self.states.remove("pregnant")
                for i in range(2):
                    self.reproduce()
                self.config.fox_num += 2





    def change_position(self):

        if self.count:
            self.count = False
            self.config.fox_num += 1


        near_foxes = list(self.in_proximity_accuracy()
                        .filter_kind(Fox)
                      )

        self.there_is_no_escape()
        self.hungry_counter += 1
        self.hungry()
        #print(self.states)

        if self.hungry_counter > self.config.fox_starving_thershold and self.config.energy_switch:
            self.kill()
            self.config.fox_num -= 1
        # fox die
        if random.random() < self.config.fox_die_rate:
            self.kill()
            self.config.fox_num -= 1
        # chasing the nearest rabbit at highest speed
        self.chase_rabbit()
        self.pregnant(near_foxes)
        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        # eat the nearest rabbit in eat range
        self.eat()
        # move
        self.move += noise()
        self.pos += self.move

class Grass(Agent):
    config: NatureConfig
    round = 1
    count = True

    def update(self):
        self.save_data("type", "grass")
        self.save_data("rabbit", None)
        self.save_data("grass", self.config.grass_num)
        self.save_data("fox", None)
        self.save_data("energy","nope")

    def change_position(self):
        if self.count:
            self.count = False
            self.config.grass_num += 1

        grass = list(self.in_proximity_accuracy()
                        .filter_kind(Grass)
                      )

        # grass grow away from their parents at a random position with distance (+/-) 5 from their parents
        if self.round == 1:
            self.round += 1
            self.pos += Vector2(random.randint(-100, 100), random.randint(-100, 100))
        # grass reproduce
        if random.random() < self.config.grass_reproduction_rate and len(grass) < 10:
            self.reproduce()
            self.config.grass_num += 1

# class Cave(Agent):
#
#     config: NatureConfig
#
#     def update(self):
#         self.save_data("type", None)
#         self.save_data("rabbit", None)
#         self.save_data("fox", None)
#         self.save_data("grass", self.config.grass_num)
#         self.save_data("energy","nope")
#
#     def change_position(self):
#         pass






def run() -> pl.DataFrame:
    return\
        (
        Simulation(
            NatureConfig(
                image_rotation=False,
                visualise_chunks=False,
                movement_speed=1,
                radius=50,
                seed=2,
                duration=2000)
        )
        # spawn agents
        .batch_spawn_agents(50, Rabbit, images=["images/rabbit.png","images/rabbit_pregnant.png"])
        .batch_spawn_agents(5, Fox, images=["images/fox.png"])
        .batch_spawn_agents(100, Grass, images=["images/grass.png"])
        #.batch_spawn_agents(3, Cave, ["images/triangle@50px.png"])
        #.spawn_site("images/triangle@50px.png", x=300, y=300)

        # run simulation
        .run()
        .snapshots
        .groupby(["type", "frame"],maintain_order=True).max()
    )




if __name__ == '__main__':
    df = run()
    print(df)

    #export to excel
    df.write_excel('tt.xlsx')

