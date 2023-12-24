"""Constants for the yoshikei integration."""
import atexit
from datetime import date, timedelta
import logging
import re

import aiohttp

from homeassistant.components.calendar import CalendarEvent
from homeassistant.exceptions import HomeAssistantError

DOMAIN = "yoshikei"


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class Yoshikei:
    """Class for authentication and data retrieval from Yoshikei."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize Yoshikei object.

        Args:
            username (str): The ID for authentication.
            password (str): The password for authentication.
        """
        self.username = username
        self.password = password
        self.session = aiohttp.ClientSession()
        atexit.register(self.close)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Yoshikei object initialized")
        # self.authenticate()

    async def authenticate(self) -> bool:
        """Authenticate the Yoshikei object.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        await self.session.get(
            "https://www2.yoshikei-dvlp.co.jp/webodr/apl/10/100201_D.aspx"
        )
        async with self.session.post(
            url="https://www2.yoshikei-dvlp.co.jp/webodr/apl/10/100201_P.aspx",
            data={
                "params": f"txtWeb_Login_Id={self.username}&pwdPassword={self.password}&nexturl=&device=pc"
            },
        ) as response:
            data = await response.json(content_type="text/html")
            self.logger.debug("Authentication response: %s", data)
            if data["errorcode"] != "":
                raise InvalidAuth("Authentication failed")

            return data["errorcode"] == ""

    async def __get_data(self, start: date) -> list[dict[str, str]]:
        """Get data from Yoshikei.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the data.
        """
        url = "https://www2.yoshikei-dvlp.co.jp/webodr/apl/10/100301_A.aspx"
        date_str = start.strftime("%Y/%m/%d").replace("/", "%2F")
        async with self.session.post(
            url,
            data={
                "params": f"position=0&changeWeekLower=4&changeWeekUpper=5&calStartDate={date_str}+0%3A00%3A01&hdnMode=&hdnClsf=&hdnQuant=&device=pc"
            },
        ) as response:
            if len(response.history):
                self.logger.debug("don't have access to data")
                raise InvalidAuth("Authentication is invalid")
            data = await response.json(content_type="text/html")
            self.logger.debug("data response: %s", data)
            return data["resultlist"]

    async def get_data(self, start: date) -> list[dict[str, str]]:
        """Retrieve data from the Yoshikei API for the specified date range.

        Args:
            start (date): The start date of the range.
            end (date): The end date of the range.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the retrieved data.
        """
        try:
            data = await self.__get_data(start)
        except InvalidAuth:
            self.logger.debug("Invalid authentication, re-authenticating")
            await self.authenticate()
            data = await self.__get_data(start)

        for index, day in enumerate(data):
            date_str = re.sub(
                r"(\d+)/(\d+)/(\d+) .*", "\\1-\\2-\\3", day["deliverydate"], 1
            )
            data[index]["deliverydate"] = date.fromisoformat(date_str)
        return data

    async def get_events(self, start: date, end: date) -> list[CalendarEvent]:
        """Retrieve a list of calendar events from Yoshikei."""
        data = await self.get_data(start)
        events = []
        while start <= end:
            day = next((item for item in data if item["deliverydate"] == start), None)
            if day is None:
                data += await self.get_data(start)
                day = next(
                    (item for item in data if item["deliverydate"] == start), None
                )
            for item in day["orderitems"]:
                events.append(
                    CalendarEvent(
                        start=day["deliverydate"],
                        end=day["deliverydate"],
                        summary=item["itemname"],
                        description="https://www2.yoshikei-dvlp.co.jp/webodr/apl/10/"
                        + item["link"],
                        location=item["menuname"],
                        uid=item["link"],
                    )
                )
            start += timedelta(days=1)
        return events

    async def close(self) -> None:
        """Close the session."""
        await self.session.close()
        self.logger.debug("Session closed")
