from .IDb import IDb


class InMemoryDb(IDb):
    def __init__(self):
        self.__queues = {}
        self.__now_playings = {}

    def get_queues(self):
        return self.__queues

    def get_all_now_playings(self):
        return self.__now_playings

    def get_queue_with_guild_id(self, guild_id):
        if guild_id in self.__queues:
            return self.__queues[guild_id]
        return None

    def get_now_playing_with_guild_id(self, guild_id):
        if guild_id in self.__now_playings:
            return self.__now_playings
        return None

    def add_to_queue(self, guild_id, item):
        if guild_id in self.__queues:
            self.__queues[guild_id].append(item)
        else:
            self.__queues[guild_id] = [item]

    def add_to_now_playing(self, guild_id, item):
        if guild_id in self.__now_playings:
            self.__now_playings[guild_id].append(item)
        else:
            self.__now_playings[guild_id] = [item]

    def set_queue(self, guild_id, queue):
        self.__queues[guild_id] = [queue]

    def set_now_playing(self, guild_id, now_playing):
        self.__now_playings[guild_id] = now_playing

    def delete_queue(self, guild_id):
        if guild_id in self.__queues:
            del self.__queues[guild_id]

    def delete_now_playing(self, guild_id):
        if guild_id in self.__now_playings:
            del self.__now_playings[guild_id]

    def guild_id_in_queues(self, guild_id):
        return guild_id in self.__queues

    def guild_id_in_now_playings(self, guild_id):
        return guild_id in self.__now_playings

    def queue_size(self, guild_id):
        if guild_id in self.__queues:
            return len(self.__queues[guild_id])
        return None
