import abc


class IDb(abc.ABC):
    def get_queues(self):
        pass

    def get_all_now_playings(self):
        pass

    def get_queue_with_guild_id(self, guild_id):
        pass

    def get_now_playing_with_guild_id(self, guild_id):
        pass

    def add_to_queue(self, guild_id, item):
        pass

    def set_queue(self, guild_id, queue):
        pass

    def set_now_playing(self, guild_id, now_playing):
        pass

    def delete_queue(self, guild_id):
        pass

    def delete_now_playing(self, guild_id):
        pass

    def guild_id_in_queues(self, guild_id):
        pass

    def guild_id_in_now_playings(self, guild_id):
        pass

    def queue_size(self, guild_id):
        pass

    def clean_up_for_guild_id(self, guild_id):
        pass

    def is_there_item_in_queue_for_guild_id(self, guild_id):
        pass

    def is_index_valid(self, index, guild_id):
        pass

    def pop_index_from_queue(self, index, guild_id):
        pass

    def queue_swap(self, guild_id, index1, index2):
        pass

    def queue_jump(self, guild_id, index):
        pass

    def queue_move(self, guild_id, original_index, new_index):
        pass
