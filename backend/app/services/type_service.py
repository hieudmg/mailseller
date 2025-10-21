from app.core.config import settings, DataType

_cache: dict[str, DataType] = settings.DATA_TYPES


class TypeService:
    """Service for managing and validating data types across storages."""

    @staticmethod
    def get_type_config(data_type: str) -> DataType | None:
        """
        Get full configuration for a data type from in-memory cache.
        Cache is refreshed by background scheduler.

        Args:
            data_type: Type name

        Returns:
            DataType configuration or None if type doesn't exist
        """
        # Always read from cache - no DB queries, no async overhead
        global _cache
        return _cache.get(data_type) if data_type in _cache else None

    @staticmethod
    def get_type_storage(data_type: str) -> str | None:
        """
        Get storage type for a given data type.

        Args:
            data_type: Type name

        Returns:
            Storage type ('redis' or 'db') or None if type doesn't exist
        """
        type_config = TypeService.get_type_config(data_type)
        if type_config:
            return type_config.get("storage")

        return None

    @staticmethod
    def get_all_types() -> dict[str, DataType]:
        """
        Get all data types from in-memory cache.

        Returns:
            Dictionary of all data types and their configurations
        """
        global _cache
        return _cache.copy()
