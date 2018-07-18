import random
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
import time
from sc2.constants import *
import os
from glob import glob

# select random map
random_map = random.choice(glob("D:/Program Files/StarCraft II/Maps/*.SC2Map"))
# cut off extension of map name
random_map = os.path.basename(random_map)[:-7] 


close_to_main = 15.0

# Zerg bot =====
class ZergyZergZergBot(sc2.BotAI):

    def __init__(self):
        self.drone_counter = 0
        self.spawning_pool_started = False

    async def on_step(self, iteration):
        await self.distribute_workers() 
        await self.manage_resources()
        await self.build_more_overlords()
        await self.build_offensive_buildings()
        await self.build_offensive_army()
        await self.build_extractors()
        await self.expand()
        await self.send_the_attack()


    async def manage_resources(self, minerals = 1.0, gas_importance = 1.0, queen_importance = 1.0):


        total_vespene = 0
        total_queens = 0

        for hatch in self.units(HATCHERY).ready:

            # current numbers
            available_minerals = 0
            gas_miners = 0
            queen_count = 0

            worker_count = self.units(DRONE).closer_than(close_to_main, hatch).amount  
            larva_available = self.units(LARVA).closer_than(5.0, hatch).amount
            vaspenes = self.state.vespene_geyser.closer_than(close_to_main, hatch)
            extractors = self.units(EXTRACTOR).closer_than(close_to_main, hatch).ready.amount
            mf = self.state.mineral_field.closer_than(close_to_main, hatch).amount

            # build drones             

            if worker_count < (mf * 2 + extractors * 3 - len(self.units(DRONE).closer_than(close_to_main, hatch).not_ready)) \
            and self.can_afford(DRONE) \
            and self.supply_left > 2 \
            and larva_available > 0:
                await self.do(self.units(LARVA).closest_to(hatch).train(DRONE))

            if worker_count > worker_count < (mf * 2 + extractors * 3):
                # move to different hatch
                pass
  
  
    async def build_queens(self):

        for hatch in self.units(HATCHERY).ready:
            queen_count = self.units(QUEEN).closer_than(close_to_main, hatch).amount

            if queen_count == 0:
                await self.do(self.units(LARVA).closest_to(hatch).train(QUEEN))



    async def queen_behaviour(self):
        for hatch in self.units(HATCHERY).ready:
            larva_available = self.units(LARVA).closer_than(5.0, hatch).amount
            existing_tumors = self.units(CREEPTUMORBURROWED).ready
            for queen in self.units(QUEEN).closer_than(close_to_main, hatch).ready:
                abilities = self.get_available_abilities(queen)
                if AbilityId.EFFECT_INJECTLARVA in abilities and larva_available <= 3:
                    await self.do(queen(EFFECT_INJECTLARVA, hatch))
                elif AbilityId.BUILD_CREEPTUMOR in abilities:
                    for d in range(10, 25):
                        pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                        await self.do(queen(BUILD_CREEPTUMOR, pos))



    async def build_extractors(self):
        for hatch in self.units(HATCHERY).ready:           
            vaspenes = self.state.vespene_geyser.closer_than(close_to_main, hatch)
            for vaspene in vaspenes:                
                if (not self.can_afford(EXTRACTOR) and \
                    ((not self.units(EXTRACTOR).closer_than(1.0, vaspene).exists and self.drone_counter >= hatch.amount*14)) or \
                    (not self.already_pending(EXTRACTOR) and self.drone_counter >= hatch.amount*17)): 
                    break

                worker = self.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if (not self.units(EXTRACTOR).closer_than(1.0, vaspene).exists and self.can_afford(EXTRACTOR)): # check if assimilator exists on geyser
                    await self.do(worker.build(EXTRACTOR, vaspene))


    async def expand(self):
        if self.units(HATCHERY).amount < 3 and self.can_afford(HATCHERY):
            await self.expand_now()


    async def build_more_overlords(self):
        for hatch in self.units(HATCHERY).ready:
            if self.supply_left <= 2 and \
            not self.already_pending(OVERLORD) and \
            self.can_afford(OVERLORD) and \
            self.units(LARVA).closer_than(5.0, hatch).amount > 0:                
                await self.do(self.units(LARVA).closest_to(hatch).train(OVERLORD))


    async def build_offensive_buildings(self):
    # elif not self.spawning_pool_started:
        hatchery = self.units(HATCHERY).ready.first
        if self.can_afford(SPAWNINGPOOL) and not self.spawning_pool_started :
            for d in range(4, 15):
                pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                if await self.can_place(SPAWNINGPOOL, pos):
                    drone = self.workers.closest_to(pos)
                    err = await self.do(drone.build(SPAWNINGPOOL, pos))
                    if not err:
                        self.spawning_pool_started = True
                        break

    async def build_offensive_army(self):
        if self.units(SPAWNINGPOOL).ready.exists:
            for hatch in self.units(HATCHERY).ready:
                larva_available = self.units(LARVA).closer_than(5.0, hatch).amount              
                if larva_available > 0 and self.can_afford(ZERGLING):
                    await self.do(self.units(LARVA).closest_to(hatch).train(ZERGLING))


    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]


    async def send_the_attack(self):
        if self.units(ZERGLING).amount > 20:
            for s in self.units(ZERGLING).idle:
                await self.do(s.attack(self.find_target(self.state)))

        elif self.units(ZERGLING).amount > 8:
            if len(self.known_enemy_units) > 0:
                for s in self.units(ZERGLING).idle:
                    await self.do(s.attack(random.choice(self.known_enemy_units)))        



run_game(maps.get("CactusValleyLE"), [
    Bot(Race.Zerg, ZergyZergZergBot()),
    # Bot(Race.Zerg, ZergyZergZergBot()),
    Computer(Race.Random, Difficulty.Easy)
], realtime=False)



