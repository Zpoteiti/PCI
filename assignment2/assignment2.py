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
    rabbit_pregnant_time : int = 300

    rabbit_starving_thershold: float = 605
    rabbit_reproduction_rate: float = 0.005
    rabbit_reproduction_limit: int = 7

    # fox
    fox_die_rate: float = 0.005
    fox_max_speed: float = 2.5

    fox_reproduction_rate: float = 0.7

    fox_pregnant_time: int = 100
    fox_starving_thershold: float = 1000
    #fox_die_rate = 0.001
    # grass
    grass_reproduction_rate: float = 0.005
    #fox_genotype = [[]]


    adult_threshold = 0.2 * rabbit_starving_thershold
    hungry_thershold: float = 0.2
    eat_range = 5
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
    x = Vector2(random.random()*2-1, random.random()*2-1)
    return x




class Rabbit(Agent):
    config: NatureConfig
    speed: float = 1.4
    hungry_counter: int = 0
    pregnant_counter: int = 0
    states = ["fine","child"]
    growth: int = 0
    #a parameter count the initial population
    count = True
    hide_prob = 0.002
    leave_prob = 0.002
    #motivation = Vector2(0, 0)

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
            motivation = self.pos - fox[0].pos
            #self.motivation.scale_to_length(self.speed)
            return motivation


        # when not hungry, go to average position of nearby grasses
    # def grass_around_me(self, grasses):
    #     n = len(grasses)
    #     if n > 0:
    #         # move towards the average position of nearby grasses
    #         average_pos = Vector2(0, 0)
    #         for i in range(n):
    #             grass = grasses[i]
    #             average_pos += grass[0].pos
    #         average_pos = average_pos / n
    #         self.move = average_pos - self.pos
    #         self.move.scale_to_length(self.speed)

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
        if grass is not None and "in danger" not in self.states:
            # move towards the rabbit
            motivation = grass[0].pos - self.pos
            return motivation
            #self.motivation.scale_to_length(self.speed)

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
            if "fine" in i[0].states and "pregnant" not in i[0].states and random.random() < self.config.rabbit_reproduction_rate \
                    and "fine" in self.states and "pregnant" not in self.states and len(near_rabbits) < self.config.rabbit_reproduction_limit:
                self.states.append("pregnant")

        if "pregnant" in self.states:
            self.pregnant_counter += 1
            if self.pregnant_counter > self.config.rabbit_pregnant_time:
                self.states.remove("pregnant")
                for i in range(random.randint(3, 6)):
                    self.reproduce()
                    #self.config.rabbit_num += 1

    #cave related behaviors
    def hide(self):
        caves = (
            self.in_proximity_accuracy()
            .filter_kind(Cave)
            .first()
        )
        if caves is not None and "full" not in caves[0].states:
            #print(caves)
            if caves[1] > 20 and (random.random() < self.hide_prob or "in danger" in self.states):
                if "go hide" not in self.states:
                    self.states.append("go hide")
            else:
                if "go hide" in self.states:
                    pass#self.states.remove("go hide")
        else:
            if "go hide" in self.states:
                self.states.remove("go hide")

        if "go hide" in self.states:
            self.move = caves[0].pos - self.pos
            self.move.scale_to_length(self.speed)

    def rejec_by_cave(self,cave):
        if cave is not None and cave[1] < 31 and "go hide" not in self.states and "hiding" not in self.states:
            motivation = (self.pos - cave[0].pos) * 100
            # move.scale_to_length(self.speed)
            print("reject")
        else:
            motivation = Vector2(0, 0)

        return motivation


    def leave(self,cave):
        if random.random() < self.leave_prob and "hiding" in self.states and "leaving" not in self.states:
            self.states.append("leaving")
        if "leaving" in self.states:
            motivation = (self.pos - cave[0].pos)
            motivation.scale_to_length(self.speed)
        else:
            motivation = Vector2(0, 0)

        return motivation


    # state functions
    def hungry(self):
        if self.hungry_counter > self.config.rabbit_starving_thershold * self.config.hungry_thershold:
            self.states = ["hungry" if i == "fine" else i for i in self.states]
        else:
            self.states = ["fine" if i == "hungry" else i for i in self.states]

    def danger(self,nearest_fox):
        if nearest_fox is not None and "hiding" not in self.states:
            if "in danger" not in self.states:
                self.states.append("in danger")
        else:
            if "in danger" in self.states:
                self.states.remove("in danger")

    def grow_up(self):
        self.growth += 1
        if self.growth > self.config.adult_threshold and "child" in self.states:
            self.states.remove("child")

    def hiding(self,caves):
        #print(caves[0][1])
        #print(caves)
        motivation = Vector2(0,0)
        if caves is not None and caves[1] < 20 and "hiding" not in self.states and "go hide" in self.states:
            self.states.append("hiding")
            self.states.remove("go hide")
        elif (caves is None or caves[1] > 20) and "hiding" in self.states :
            self.states.remove("hiding")
            if "leaving" in self.states:
                self.states.remove("leaving")

        if "hiding" in self.states and caves[1] > 18 and "leaving" not in self.states:
            motivation = caves[0].pos - self.pos
            #self.motivation = Vector2(0,0)
            motivation.scale_to_length(1000000)
        return motivation





    def change_position(self):
        if self.count:
            self.count = False
            self.config.rabbit_num += 1

        self.there_is_no_escape()

        motivation = Vector2(0, 0)


        # local info of nearby agents
        nearest_fox = (self.in_proximity_accuracy().filter_kind(Fox).first())
        nearest_grass = (self.in_proximity_accuracy().filter_kind(Grass).first())
        near_cave = (self.in_proximity_accuracy().filter_kind(Cave).first())
        nearby_grass = list(self.in_proximity_accuracy().filter_kind(Grass))
        nearby_rabbits = list(self.in_proximity_accuracy().filter_kind(Rabbit))


        # basic habbits
        self.there_is_no_escape()
        self.hungry_counter += 1
        # self.tired()
        print("rr",self.hungry_counter)

        #basic behaviors
        self.separetion(nearby_rabbits)
        self.hide()
        motivation += self.leave(near_cave)
        motivation += self.rejec_by_cave(near_cave)



        #states check
        self.hungry()
        self.danger(nearest_fox)
        if "child" in self.states:
            self.grow_up()
        motivation += self.hiding(near_cave)


        # senarios
        # see foxes
        #self.run_away_from_fox(nearest_fox)

        # hungry and see no grass
        if "hungry" in self.states:
            x = self.chase(nearest_grass)
            if x is not None:
                motivation += x

        # eat grass when hungry
        if "hungry" in self.states:
            self.eat(nearest_grass)     #only eat when hungry?

        # not hungry and see grass
        # elif "in danger" not in self.states and self.hungry_counter <= self.config.rabbit_starving_thershold * self.config.hungry_thershold:
        #     pass#self.grass_around_me(nearby_grass)

        if "in danger" not in self.states and "child" not in self.states:
            self.pregnant(nearby_rabbits)

        # run away from the nearest fox at highest speed
        if "in danger" in self.states and "hiding" not in self.states:
            x = self.run_away_from_fox(nearest_fox)
            if x is not None:
                motivation += x
            ##### we can set a danger mode speed as well
        print(self.states)

        # make sure the speed equal to max speed
        if motivation.length() > 0:
            motivation.scale_to_length(self.speed)
        else:
            motivation += noise()
        #print("rr",self.states)
        # if "go hide" in self.states:
        #     motivation = Vector2(0,0)
        # move
        #print("momo",motivation)
        #print("MOMO",self.move)
        self.move += motivation #+ noise()
        if self.move.length() > 0:
            #print("MM",self.move)
            self.move.scale_to_length(self.speed)
        #print("rm",motivation)
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



    # chasing the nearest rabbit at highest speed
    def chase_rabbit(self):
        rabbit = (
            self.in_proximity_accuracy()
            .filter_kind(Rabbit)
            .first()
        )

        if rabbit is not None and "hiding" not in rabbit[0].states:
            # move towards the rabbit
            #print("rrs",rabbit[0].states)
            motivation = rabbit[0].pos - self.pos
            #print("fffm",motivation)
            if "hungry" in self.states:
                motivation.scale_to_length(self.config.fox_max_speed)
            else:
                motivation.scale_to_length(self.speed)
        else:
            motivation = Vector2(0,0)

        return motivation

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
            print("eat rr")
            self.config.rabbit_num -= 1
            self.hungry_counter = 0
            print(self.hungry_counter)
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
                for i in range(1):
                    self.reproduce()
                    #self.config.fox_num += 1


    def out_of_cave(self):
        caves = (
            self.in_proximity_accuracy()
            .filter_kind(Cave)
            .first()
        )

        if caves is not None and caves[1] < 31:
            motivation = (self.pos - caves[0].pos)*100
            #move.scale_to_length(self.speed)
        else:
            motivation = Vector2(0,0)

        return motivation





    def change_position(self):

        if self.count:
            self.count = False
            self.config.fox_num += 1
            #hungry_counter = 0


        motivation = Vector2(0,0)


        near_foxes = list(self.in_proximity_accuracy()
                        .filter_kind(Fox)
                      )

        self.there_is_no_escape()
        self.hungry_counter += 1
        print("ff",self.hungry_counter)
        self.hungry()
        self.separetion(near_foxes)

        #print(self.states)

        if self.hungry_counter > self.config.fox_starving_thershold and self.config.energy_switch:
            self.kill()
            self.config.fox_num -= 1
        # fox die
        if random.random() < self.config.fox_die_rate:
            self.kill()
            self.config.fox_num -= 1
        # chasing the nearest rabbit at highest speed
        motivation += self.chase_rabbit()
        self.pregnant(near_foxes)
        # make sure the speed equal to max speed
        self.move.scale_to_length(self.speed)
        # eat the nearest rabbit in eat range
        self.eat()
        # move

        motivation += self.out_of_cave()


        if motivation.length() > 0:
            motivation.scale_to_length(self.speed)
            self.move += motivation + noise()

        #print("fm",motivation)
        #print("ff",self.move)
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
        if random.random() < self.config.grass_reproduction_rate and len(grass) < 10 and self.config.grass_num < 1000:
            self.reproduce()
            #self.config.grass_num += 1

class Cave(Agent):

    config: NatureConfig
    states = []

    def update(self):
        self.save_data("type", "cave")
        self.save_data("rabbit", None)
        self.save_data("fox", None)
        self.save_data("grass", None)
        self.save_data("energy","nope")

    def full(self):
        member = 0
        hiding_rabbits = list(self.in_proximity_accuracy()
                          .filter_kind(Rabbit)
                          )
        if len(hiding_rabbits) < 5 and "full" in self.states:
            self.states.remove("full")
        else:
            for i in hiding_rabbits:
                if i[1] < 20:
                    member += 1
        if member >= 5  and "full" not in self.states:
            self.states.append("full")


    def change_position(self):
        self.full()






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
                duration=1500)
        )
        # spawn agents
        .batch_spawn_agents(100, Rabbit, images=["images/rabbit.png"])
        .batch_spawn_agents(20, Fox, images=["images/fox.png"])
        .batch_spawn_agents(100, Grass, images=["images/grass.png"])
        .batch_spawn_agents(3, Cave, ["images/cave.png"])
        #.spawn_site("images/triangle@50px.png", x=300, y=300)

        # run simulation
        .run()
        .snapshots
        .groupby(["type","frame","rabbit","fox","grass"],maintain_order=True).count()
    )




if __name__ == '__main__':
    df = run()
    print(df)

    #export to excel
    df.write_excel('tt.xlsx')

