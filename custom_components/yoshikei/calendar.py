"""Yoshikei calendar functionality for Home Assistant."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, Yoshikei

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CalDav calendar platform for a config entry."""
    client: Yoshikei = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            YoshikeiCalender(
                hass,
                entry.title,
                client,
            )
        ],
        True,
    )


class YoshikeiCalender(CalendarEntity):
    """YoshikeiCalender represents a calendar entity for Yoshikei integration."""

    def __init__(self, hass: HomeAssistant, name: str, client: Yoshikei) -> None:
        """Initialize YoshikeiCalender."""
        self.hass = hass
        self.name = name
        self._client = client
        self._event = None
        self.entity_id = f"calendar.{name.lower().replace(' ', '_')}"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return self._event

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Retrieve a list of calendar events between the specified start and end dates.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            start_date (datetime): The start date of the event range.
            end_date (datetime): The end date of the event range.

        Returns:
            list[CalendarEvent]: A list of calendar events.
        """
        self._event = await self._client.get_events(
            start=start_date.date(), end=end_date.date()
        )
        return self._event
