import pdb
from typing import List

from ..lib.logger import bcolors, Logger
from ..models import Player
from ..types import PlayerAvailability, PlayerExperience, PlayerInterest, PlayerStats

LOG_ID = 'PlayersBuilder'

class PlayersBuilder():
    def __init__(self):
        self.stats = []
        self.availabilities = []
        self.experiences = []
        self.interests = []
        self.discord_ids = []

    def with_discord_ids(self, discord_ids):
        self.discord_ids = discord_ids
        return self

    def with_availabilities(self, availabilites: List[PlayerAvailability]):
        self.availabilities = availabilites
        return self

    def with_experiences(self, experiences: List[PlayerExperience]):
        self.experiences = experiences
        return self

    def with_interests(self, interests: List[PlayerInterest]):
        self.interests = interests
        return self

    def with_stats(self, stats: List[PlayerStats]):
        self.stats = stats
        return self

    def build_availabilities_index(self):
        availabilities_index = {}

        availabilities = self.availabilities.copy()

        # Ensure that players with the same identity have the same availability reference
        for availability in availabilities:
            identity = availability['identity']
            del availability['identity']
            availabilities_index[identity] = []

            Logger.instance(LOG_ID).info(f"{bcolors.OKBLUE}Building availability for {identity}{bcolors.ENDC}")
            for day in availability:
                hours = availability[day]
                if hours:
                    Logger.instance(LOG_ID).info(f"  {day}: {hours}")

                availabilities_index[identity] += list(map(lambda hour: f"{day.strip()}.{hour.strip()}", hours))
            
            Logger.instance(LOG_ID).info(f"{bcolors.OKGREEN}Final availability for {identity}: {availabilities_index[identity]}{bcolors.ENDC}")
        
        return availabilities_index

    def build_experiences_index(self):
        experiences_index = {}
        for experience in self.experiences:
            clone = {**experience}
            del clone['name']
            experiences_index[experience['name']] = clone
        return experiences_index

    def build_interests_index(self):
        interests_index = {}
        for interest in self.interests:
            clone = {**interest}
            del clone['name']
            interests_index[interest['name']] = clone
        return interests_index

    def build_discord_index(self):
        discord_index = {}
        if not self.discord_ids:  # Handle case when no discord IDs are provided
            return discord_index
        
        for row in self.discord_ids:
            if 'identity' in row and 'discord_id' in row:
                discord_index[row['identity'].strip()] = row['discord_id'].strip()
        
        return discord_index

    def build(self):
        availabilities_index = self.build_availabilities_index()
        experiences_index = self.build_experiences_index()
        interests_index = self.build_interests_index()
        discord_index = self.build_discord_index()

        players = []
        for stat in self.stats:
            try:
                availability = availabilities_index[stat['identity']]
            except KeyError:
                Logger.instance(LOG_ID).warn(f"{bcolors.WARNING}No availability found for {stat['name']}{bcolors.ENDC}")
                continue

            experience = experiences_index.get(stat['name'])
            interests = interests_index.get(stat['name'])
            discord_id = discord_index.get(stat['identity'])

            try:
                player = Player(
                    **stat,
                    availability=availability,
                    experience=experience or {},
                    interests=interests or {},
                    discord_id=discord_id
                )
                players.append(player)
            except ValueError as e:
                Logger.instance(LOG_ID).warn(f"{bcolors.WARNING}Failed to create player {stat['name']}: {e}{bcolors.ENDC}")
                continue

            if len(availability) == 0:
                Logger.instance(LOG_ID).warn(f"{bcolors.WARNING}{player.name} has no availability{bcolors.ENDC}")

            if not experience:
                Logger.instance(LOG_ID).warn(f"{bcolors.WARNING}Could not join {player.name} experience{bcolors.ENDC}")

            if not interests:
                Logger.instance(LOG_ID).warn(f"{bcolors.WARNING}Could not join {player.name} interests{bcolors.ENDC}")

            if not discord_id and self.discord_ids:
                Logger.instance(LOG_ID).warn(f"{bcolors.WARNING}Could not join {player.name} discord_id{bcolors.ENDC}")

        return players
