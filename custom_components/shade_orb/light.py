"""LED BLE integration light platform."""
from __future__ import annotations

from typing import Any
import logging
from enum import Enum

from shadeorb import ORB

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_WHITE,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
# from homeassistant.util.color import percentage_to_ranged_value
# import math
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN  #, DEFAULT_EFFECT_SPEED
from .models import ORBData

_LOGGER = logging.getLogger(__name__)

# class ORBMount(Enum):
#     Hanging = 0
#     Standing = 1
#     Wall = 2

class ORBEntitySide(Enum):
    Inner = 0  # Cable side, up
    Outer = 1 # down
    Edge = 2    # Colored Edge

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for Shade ORB."""
    _LOGGER.debug("Setting up light platform for Shade ORB %s" , entry.title)
    data: ORBData = hass.data[DOMAIN][entry.entry_id]
    #async_add_entities([ORBEntity(data.coordinator, data.device, entry.title)])
    async_add_entities([
        ORBEntity(data.device, entry.title,ORBEntitySide.Inner),
        ORBEntity(data.device, entry.title,ORBEntitySide.Outer),
        ORBEntity(data.device, entry.title,ORBEntitySide.Edge),])


#class ORBEntity(CoordinatorEntity[DataUpdateCoordinator[None]], LightEntity):
class ORBEntity( LightEntity):
    """Representation of Shade ORB device."""

    _attr_has_entity_name = True
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self,
        #coordinator: DataUpdateCoordinator[None],
        device: ORB, name: str,
        side: ORBEntitySide,
    ) -> None:
        """Initialize an Shade ORB light."""
        #super().__init__(coordinator)
        self._device = device
        self._side = side
        self._attr_unique_id = device.address+side.name
        self._attr_device_info = DeviceInfo(
            name=name,
            model="ORB", # f"{device.model_data.description} {hex(device.model_num)}",
            sw_version="unkn",#hex(device.version_num),
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )
        self._async_update_attrs()

    @property
    def name(self):
        """Name of the entity."""
        return self._side.name
    @property
    def supported_color_modes(self):
        if self._side == ORBEntitySide.Edge:
            return {ColorMode.RGBW}
        else:
            return {ColorMode.WHITE}

    @property
    def color_mode(self):
        if self._side == ORBEntitySide.Edge:
            return ColorMode.RGBW
        else:
            return ColorMode.BRIGHTNESS
    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return self._device.effect_list

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        _LOGGER.debug("Updating attributes for device %s", self._device.address)

        device = self._device
        #self._attr_color_mode = ColorMode.RGBW # ColorMode.WHITE if device.w else ColorMode.RGB
        #self._attr_brightness = device.brightness
        #self._attr_rgb_color = device.rgb_unscaled
        # self._attr_is_on = device.on
        #self._attr_effect = device.effect
        #self._attr_effect_list = device.effect_list

    # async def _async_set_effect(self, effect: str, brightness: int) -> None:
    #     """Set an effect."""
    #     await self._device.async_set_effect(
    #         effect,
    #         self._device.speed or DEFAULT_EFFECT_SPEED,
    #         round(brightness / 255 * 100),
    #     )
    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._device.on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness)

        if effect := kwargs.get(ATTR_EFFECT):
            _LOGGER.debug("Setting effect %s",effect)
            await self._device.set_effect(effect, brightness)
            return
        # if ATTR_RGB_COLOR in kwargs:
        #     rgb = kwargs[ATTR_RGB_COLOR]
        #     await self._device.set_rgb(rgb, brightness)
        #     return
        if ATTR_RGBW_COLOR in kwargs:
            # Scaling to 12 bits, close enough for now
            rgbw = [ c << 4 | c >> 4 for c in kwargs[ATTR_RGBW_COLOR ]]
            await self._device.set_edge_rgbw(rgbw, brightness)
            return
        # if ATTR_BRIGHTNESS in kwargs:
        #     await self._device.set_brightness(brightness)
        #     return
        if ATTR_BRIGHTNESS in kwargs:
            _LOGGER.debug("ATTR_BRIGHTNESS for %s",self._side.name)
            w =  kwargs[ATTR_BRIGHTNESS ]
            #w = brightness
            if not w :
                return
            white =  w << 4 | w >> 4
            if self._side==ORBEntitySide.Inner :
                await self._device.set_inner_whites((white,white),brightness)
            else:
                await self._device.set_outer_whites((white,white),brightness)
            return
        await self._device.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._device.turn_off()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        #self.async_on_remove(
        #    self._device.register_callback(self._handle_coordinator_update)
        #)
        #return await super().async_added_to_hass()