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
