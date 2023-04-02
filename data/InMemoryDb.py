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
            return self.__now_playings[guild_id]
        return None

    def add_to_queue(self, guild_id, item):
        if guild_id in self.__queues:
            self.__queues[guild_id].append(item)
        else:
            self.__queues[guild_id] = [item]

    def set_queue(self, guild_id, queue):
        self.__queues[guild_id] = queue

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

    def clean_up_for_guild_id(self, guild_id):
        self.delete_queue(guild_id)
        self.delete_now_playing(guild_id)

    def is_there_item_in_queue_for_guild_id(self, guild_id):
        return self.guild_id_in_queues(guild_id) and self.queue_size(guild_id) > 0

    def is_index_valid(self, index, guild_id):
        return 1 <= index <= self.queue_size(guild_id)

    def pop_index_from_queue(self, index, guild_id):
        if not self.is_there_item_in_queue_for_guild_id(guild_id) or not self.is_index_valid(index, guild_id):
            return None
        return self.__queues[guild_id].pop(index - 1)

    def queue_swap(self, guild_id, index1, index2):
        if (not self.is_there_item_in_queue_for_guild_id(guild_id) or not self.is_index_valid(index1, guild_id)
                or not self.is_index_valid(index2, guild_id)):
            return False

        position1 = index1 - 1
        position2 = index2 - 1

        temp = self.__queues[guild_id][position1]
        self.__queues[guild_id][position1] = self.__queues[guild_id][position2]
        self.__queues[guild_id][position2] = temp
        return True

    def queue_jump(self, guild_id, index):
        if not self.is_there_item_in_queue_for_guild_id(guild_id) or not self.is_index_valid(index, guild_id):
            return False

        del self.__queues[guild_id][:index - 1]
        return True

    def queue_move(self, guild_id, original_index, new_index):
        if (not self.is_there_item_in_queue_for_guild_id(guild_id) or not self.is_index_valid(original_index, guild_id)
                or not self.is_index_valid(new_index, guild_id)):
            return False

        player = self.__queues[guild_id].pop(original_index - 1)
        self.__queues[guild_id].insert(new_index - 1, player)
        return True

    def player_in_any_queue(self, player):
        for queue in self.__queues.values():
            for item in queue:
                if player.title == item.title and player.data["original_url"] == item.data["original_url"]:
                    return True
        return False

    def player_in_any_now_playing(self, player):
        return any(player.title == queue_item.title and player.data["original_url"] == queue_item.data["original_url"]
                   for queue_item in self.__now_playings.values())
