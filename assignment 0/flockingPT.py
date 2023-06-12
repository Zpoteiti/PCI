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
    separation_weight: float = 1.5
    avoid_crash_weight: float = 1

    delta_time: float = 3

    mass: int = 20

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig

    def move(self):
        return self.move


    def change_position(self):
        # Pac-man-style teleport to the other end of the screen when trying to escape
        self.there_is_no_escape()
        #YOUR CODE HERE -----------

        c = self.obstacle_intersections()

        #for c in self.obstacle_intersections(scale=1):

        #  print("CCCCCCC",c)

        neighbors = list(self.in_proximity_accuracy())




        speed = [agent.move for agent, len in neighbors]
        speed_sum = Vector2(0,0)
        for i in speed:
            speed_sum += i
        # print(len(neighbors))
        alignment = (speed_sum / len(neighbors))-self.move if len(neighbors) > 0 else self.move
        # print("out",speed_sum)
        # print(alignment)
        #alignment = alignment.normalize()


        # Calculate separation
        separation = Vector2(0,0)
        nearest = Vector2(0,0)
        if len(neighbors) > 0:
            dist_list = [(len,index) for index, (agent, len) in enumerate(neighbors)]
            dist = 50
            for i in dist_list:
                if i[0] < dist:
                    dist = i[0]
                    index = i[1]
                    nearest = neighbors[i[1]][0].pos
            #print('n1',neighbors)

            # if len(neighbors) > 1:
            #    neighbors.remove(neighbors[index])

            #if self.pos != nearest:

            direction = self.pos - nearest
            separation = (50 - direction.length())* direction.normalize()

            #print("n2",neighbors)



        # Calculate cohesion
        pos = [agent.pos for agent, len in neighbors]
        pos_sum = Vector2(0,0)
        for i in pos:
            pos_sum += i
        cohesion = (
            (pos_sum / len(neighbors)) - self.pos if len(neighbors) > 0
            else pos_sum
        )
        # print(pos_sum)
        # print("cc",cohesion)


        #dist_sum = sum(agent.pos for agent, dist in neighbors)
        #separation = (
        #    dist_sum / len(neighbors) if len(neighbors) > 0
        #    else dist_sum
        #)


        avoid_crash = Vector2(0, 0)

        hit_distances = [x for x in c]
        if hit_distances != []:
            # print("list",hit_distances)
            lengths = [self.pos.distance_to(i) for i in hit_distances]
            x = min(lengths)
            hit_point = hit_distances[lengths.index(x)]
            avoid_crash = (self.pos - hit_point)*100



        # Apply weights
        #print('ss', separation)
        if len(neighbors) > 0:

            alignment = alignment * self.config.alignment_weight
            cohesion *= self.config.cohesion_weight
            separation *= self.config.separation_weight
            avoid_crash *= self.config.avoid_crash_weight

            # print("a:",alignment," c:",cohesion," s:",separation)
            # print("C L :",cohesion.length())
            # print("A L :", alignment.length())
            # print("S L :", separation.length())
            # Calculate final steering force
            steering = (alignment + cohesion + separation + avoid_crash) /self.config.mass

            # Apply steering force to velocity

            self.move = steering * self.config.delta_time + self.move
            #print( self.move.length())








        #update movements

        #if self.move.length() > max_velocity:
        self.move = self.move.normalize() * 7

        # for i in c:
        #     print("yesyes",i)
        #     self.move = (self.pos - i)

        #print("final:",self.move.length())
        self.pos += self.move

        # if self.pos.x == 250:
        #    if 250 < self.pos.y and self.pos.y < 450:
        #        self.pos = Vector2(100, 100)
        #
        # if self.pos.y == 250:
        #    if 250 < self.pos.x and self.pos.x < 450:
        #        self.pos = Vector2(600, 600)




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
        # print(f"A: {a:.1f} - C: {c:.1f} - S: {s:.1f}")


(
    FlockingLive(
        FlockingConfig(
            image_rotation=True,
            movement_speed=1,
            radius=100,
            seed=1,
        )
    )
    #.spawn_site("C:/Users/PTFaust/Desktop/images/white.png", x=100, y=600)
    .spawn_obstacle(r"C:\Users\zpote\OneDrive\文档\VU code\images\bubble-full.png", 350, 350)
    .batch_spawn_agents(200, Bird, images=[r"C:\Users\zpote\OneDrive\文档\VU code\images\bird.png"])
    .run()
)
