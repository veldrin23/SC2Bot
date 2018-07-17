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

            worker_count = self.units(DRONE).closer_than(15.0, hatch).amount  
            larva_available = self.units(LARVA).closer_than(5.0, hatch).amount
            vaspenes = self.state.vespene_geyser.closer_than(15.0, hatch)
            extractors = self.units(EXTRACTOR).closer_than(15.0, hatch).ready.amount
            mf = self.state.mineral_field.closer_than(15, hatch).amount

            # build drones             

            if worker_count < (mf * 2 + extractors * 3 - len(self.units(DRONE).closer_than(15.0, hatch).not_ready)) \
            and self.can_afford(DRONE) \
            and self.supply_left > 2 \
            and larva_available > 0:
                await self.do(self.units(LARVA).closest_to(hatch).train(DRONE))

            if worker_count > worker_count < (mf * 2 + extractors * 3):
                # move to different hatch
                pass
  

    async def build_extractors(self):
        for hatch in self.units(HATCHERY).ready:           
            vaspenes = self.state.vespene_geyser.closer_than(15.0, hatch)
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

# Protoss bot =====
class ProtyProtoss(sc2.BotAI):

    def __init__(self):
        self.probe_counter = 0


    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.back_to_work()
        await self.mine_gas()
        await self.offense_force_buildings()
        await self.build_offensive_force()
        await self.attack_bitches()

    async def build_workers(self):
    	for nexus in self.units(NEXUS).ready.noqueue:    		
    		if self.can_afford(PROBE) and self.probe_counter <= self.units(NEXUS).ready.amount * 16: ## check
    			await self.do(nexus.train(PROBE))


    async def build_pylons(self):
    	if (self.supply_left  <= 2 or  (self.supply_left / self.supply_cap) > .8) and not self.already_pending(PYLON): ## hoeveel???
    		nexus = self.units(NEXUS)
    		if nexus.exists:
    			if self.can_afford(PYLON):
    				await self.build(PYLON, near=nexus.first) ## waar????


    async def build_assimilators(self):
    	for nexus in self.units(NEXUS).ready:    		
    		vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus)
    		for vaspene in vaspenes:
    			#if not self.can_afford(ASSIMILATOR) and ((not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists and self.probe_counter >= self.units(NEXUS).amount*14) or (self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists and self.probe_counter >= self.units(NEXUS).amount*17)):
    			if (not self.can_afford(ASSIMILATOR) and \
    				((not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists and self.probe_counter >= self.units(NEXUS).amount*14)) or \
    				(not self.already_pending(ASSIMILATOR) and self.probe_counter >= self.units(NEXUS).amount*17)): 
    				break

    			worker = self.select_build_worker(vaspene.position)
    			if worker is None:
    				break
    			if (not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists and self.can_afford(ASSIMILATOR)): # check if assimilator exists on geyser
    				await self.do(worker.build(ASSIMILATOR, vaspene))


    async def back_to_work(self):
    	for idle_worker in self.workers.idle:
    		mf = self.state.mineral_field.closest_to(idle_worker)
    		await self.do(idle_worker.gather(mf))


    async def mine_gas(self):
    	for a in self.units(ASSIMILATOR):
    		if a.assigned_harvesters < a.ideal_harvesters:
    			w = self.workers.closer_than(20, a)
    			if w.exists:
    				await self.do(w.random.gather(a))


    async def expand(self):
    	if self.units(NEXUS).amount < 3 and self.can_afford(NEXUS):
    		await self.expand_now()


    async def offense_force_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = random.choice(self.units(PYLON).ready)
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, pylon)

            elif len(self.units(GATEWAY)) < self.units(NEXUS).amount*3:
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)


    async def build_offensive_force(self, what_to_build = .5):

        what_to_build = random.uniform(0, 1)        
        no_of_nexus = len(self.units(NEXUS).ready)
        army_count = self.supply_used - len(self.units(PROBE).ready)

        if army_count / no_of_nexus < 30:
            if what_to_build > .75:
                if self.units(GATEWAY).ready.exists and len(self.units(ZEALOT).ready) <= 5:
                    for gw in self.units(GATEWAY).ready.noqueue:
                        if self.can_afford(ZEALOT) and self.supply_left >= 2:
                            await self.do(gw.train(ZEALOT))
            else:
                if self.units(GATEWAY).ready.exists and self.units(CYBERNETICSCORE).ready.exists and len(self.units(STALKER)) < 20:
                    for gw in self.units(GATEWAY).ready.noqueue:
                        if self.can_afford(STALKER) and self.supply_left >= 2:
                            await self.do(gw.train(STALKER))


    # def find_target(self, state):
    #     if len(self.known_enemy_units) > 0:
    #         return random.choice(self.known_enemy_units)
    #     elif len(self.known_enemy_structures) > 0:
    #         return random.choice(self.known_enemy_structures)
    #     else:
    #         return random.choice(self.enemy_start_locations)

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack_bitches(self):
        if self.units(STALKER).amount > 15:
            for s in self.units(STALKER).idle:
                await self.do(s.attack(self.find_target(self.state)))

        elif self.units(STALKER).amount > 3:
            if len(self.known_enemy_units) > 0:
                for s in self.units(STALKER).idle:
                    await self.do(s.attack(random.choice(self.known_enemy_units)))
                    
    # async def attack_bitches(self):

        # army_count = self.supply_used - len(self.units(PROBE).ready)

        # if army_count > 15:
        #     for s in self.units(STALKER).idle:
        #         await self.do(s.attack(self.find_target(self.state)))
        #     for z in self.units(ZEALOT).idle:
        #         await self.do(z.attack(self.find_target(self.state)))


        # elif army_count > 5:
        #     if len(self.known_enemy_units) > 0:
        #         for s in self.units(STALKER).idle:
        #             await self.do(s.attack(random.choice(self.known_enemy_units)))
        #         for z in self.units(ZEALOT).idle:
        #             await self.do(z.attack(random.choice(self.known_enemy_units)))


run_game(maps.get("CactusValleyLE"), [
    Bot(Race.Zerg, ZergyZergZergBot()),
    # Bot(Race.Zerg, ZergyZergZergBot()),
    Computer(Race.Random, Difficulty.Easy)
], realtime=False)



