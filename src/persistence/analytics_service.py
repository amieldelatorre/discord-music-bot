from .analytics_repository import AnalyticsRepositoryInterface


class EventAnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepositoryInterface):
        self.analytics_repository = analytics_repository
        self.base_index = "event_history"


class SongAnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepositoryInterface):
        self.analytics_repository = analytics_repository
        self.base_index = "song_info"
