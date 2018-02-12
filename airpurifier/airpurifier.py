ATTR_TEMPERATURE = 'temperature'
ATTR_HUMIDITY = 'humidity'
ATTR_AIR_QUALITY_INDEX = 'aqi'
ATTR_MODE = 'mode'
ATTR_FILTER_HOURS_USED = 'filter_hours_used'
ATTR_FILTER_LIFE = 'filter_life_remaining'
ATTR_FAVORITE_LEVEL = 'favorite_level'
ATTR_BUZZER = 'buzzer'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_LED = 'led'
ATTR_LED_BRIGHTNESS = 'led_brightness'
ATTR_MOTOR_SPEED = 'motor_speed'
ATTR_AVERAGE_AIR_QUALITY_INDEX = 'average_aqi'
ATTR_PURIFY_VOLUME = 'purify_volume'

ATTR_BRIGHTNESS = 'brightness'
ATTR_LEVEL = 'level'

SUCCESS = ['ok']

SERVICE_SET_BUZZER_ON = 'xiaomi_miio_set_buzzer_on'
SERVICE_SET_BUZZER_OFF = 'xiaomi_miio_set_buzzer_off'
SERVICE_SET_LED_ON = 'xiaomi_miio_set_led_on'
SERVICE_SET_LED_OFF = 'xiaomi_miio_set_led_off'
SERVICE_SET_CHILD_LOCK_ON = 'xiaomi_miio_set_child_lock_on'
SERVICE_SET_CHILD_LOCK_OFF = 'xiaomi_miio_set_child_lock_off'
SERVICE_SET_FAVORITE_LEVEL = 'xiaomi_miio_set_favorite_level'
SERVICE_SET_LED_BRIGHTNESS = 'xiaomi_miio_set_led_brightness'

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend({
    vol.Required(ATTR_BRIGHTNESS):
        vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))
})

SERVICE_SCHEMA_FAVORITE_LEVEL = AIRPURIFIER_SERVICE_SCHEMA.extend({
    vol.Required(ATTR_LEVEL):
        vol.All(vol.Coerce(int), vol.Clamp(min=0, max=16))
})

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER_ON: {'method': 'async_set_buzzer_on'},
    SERVICE_SET_BUZZER_OFF: {'method': 'async_set_buzzer_off'},
    SERVICE_SET_LED_ON: {'method': 'async_set_led_on'},
    SERVICE_SET_LED_OFF: {'method': 'async_set_led_off'},
    SERVICE_SET_CHILD_LOCK_ON: {'method': 'async_set_child_lock_on'},
    SERVICE_SET_CHILD_LOCK_OFF: {'method': 'async_set_child_lock_off'},
    SERVICE_SET_FAVORITE_LEVEL: {
        'method': 'async_set_favorite_level',
        'schema': SERVICE_SCHEMA_FAVORITE_LEVEL},
    SERVICE_SET_LED_BRIGHTNESS: {
        'method': 'async_set_led_brightness',
        'schema': SERVICE_SCHEMA_LED_BRIGHTNESS},
}

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

class XiaomiAirPurifier(FanEntity):
    """Representation of a Xiaomi Air Purifier."""

    def __init__(self, name, air_purifier):
        """Initialize the air purifier."""
        self._name = name

        self._air_purifier = air_purifier
        self._state = None
        self._state_attrs = {
            ATTR_AIR_QUALITY_INDEX: None,
            ATTR_TEMPERATURE: None,
            ATTR_HUMIDITY: None,
            ATTR_MODE: None,
            ATTR_FILTER_HOURS_USED: None,
            ATTR_FILTER_LIFE: None,
            ATTR_FAVORITE_LEVEL: None,
            ATTR_BUZZER: None,
            ATTR_CHILD_LOCK: None,
            ATTR_LED: None,
            ATTR_LED_BRIGHTNESS: None,
            ATTR_MOTOR_SPEED: None,
            ATTR_AVERAGE_AIR_QUALITY_INDEX: None,
            ATTR_PURIFY_VOLUME: None,
        }

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def should_poll(self):
        """Poll the fan."""
        return True

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def available(self):
        """Return true when state is known."""
        return self._state is not None

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if fan is on."""
        return self._state

    @asyncio.coroutine
    def _try_command(self, mask_error, func, *args, **kwargs):
        """Call an air purifier command handling error messages."""
        from miio import DeviceException
        try:
            result = yield from self.hass.async_add_job(
                partial(func, *args, **kwargs))

            _LOGGER.debug("Response received from air purifier: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            return False

    @asyncio.coroutine
    def async_turn_on(self: ToggleEntity, speed: str=None, **kwargs) -> None:
        """Turn the fan on."""
        if speed:
            # If operation mode was set the device must not be turned on.
            yield from self.async_set_speed(speed)
            return

        yield from self._try_command(
            "Turning the air purifier on failed.", self._air_purifier.on)

    @asyncio.coroutine
    def async_turn_off(self: ToggleEntity, **kwargs) -> None:
        """Turn the fan off."""
        yield from self._try_command(
            "Turning the air purifier off failed.", self._air_purifier.off)

    @asyncio.coroutine
    def async_update(self):
        """Fetch state from the device."""
        from miio import DeviceException

        try:
            state = yield from self.hass.async_add_job(
                self._air_purifier.status)
            _LOGGER.debug("Got new state: %s", state)

            self._state = state.is_on
            self._state_attrs = {
                ATTR_TEMPERATURE: state.temperature,
                ATTR_HUMIDITY: state.humidity,
                ATTR_AIR_QUALITY_INDEX: state.aqi,
                ATTR_MODE: state.mode.value,
                ATTR_FILTER_HOURS_USED: state.filter_hours_used,
                ATTR_FILTER_LIFE: state.filter_life_remaining,
                ATTR_FAVORITE_LEVEL: state.favorite_level,
                ATTR_BUZZER: state.buzzer,
                ATTR_CHILD_LOCK: state.child_lock,
                ATTR_LED: state.led,
                ATTR_MOTOR_SPEED: state.motor_speed,
                ATTR_AVERAGE_AIR_QUALITY_INDEX: state.average_aqi,
                ATTR_PURIFY_VOLUME: state.purify_volume,
            }

            if state.led_brightness:
                self._state_attrs[
                    ATTR_LED_BRIGHTNESS] = state.led_brightness.value

        except DeviceException as ex:
            _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def speed_list(self: ToggleEntity) -> list:
        """Get the list of available speeds."""
        from miio.airpurifier import OperationMode
        return [mode.name for mode in OperationMode]

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            from miio.airpurifier import OperationMode

            return OperationMode(self._state_attrs[ATTR_MODE]).name

        return None

    @asyncio.coroutine
    def async_set_speed(self: ToggleEntity, speed: str) -> None:
        """Set the speed of the fan."""
        _LOGGER.debug("Setting the operation mode to: " + speed)
        from miio.airpurifier import OperationMode

        yield from self._try_command(
            "Setting operation mode of the air purifier failed.",
            self._air_purifier.set_mode, OperationMode[speed])

    @asyncio.coroutine
    def async_set_buzzer_on(self):
        """Turn the buzzer on."""
        yield from self._try_command(
            "Turning the buzzer of the air purifier on failed.",
            self._air_purifier.set_buzzer, True)

    @asyncio.coroutine
    def async_set_buzzer_off(self):
        """Turn the buzzer off."""
        yield from self._try_command(
            "Turning the buzzer of the air purifier off failed.",
            self._air_purifier.set_buzzer, False)

    @asyncio.coroutine
    def async_set_led_on(self):
        """Turn the led on."""
        yield from self._try_command(
            "Turning the led of the air purifier off failed.",
            self._air_purifier.set_led, True)

    @asyncio.coroutine
    def async_set_led_off(self):
        """Turn the led off."""
        yield from self._try_command(
            "Turning the led of the air purifier off failed.",
            self._air_purifier.set_led, False)

    @asyncio.coroutine
    def async_set_child_lock_on(self):
        """Turn the child lock on."""
        yield from self._try_command(
            "Turning the child lock of the air purifier on failed.",
            self._air_purifier.set_child_lock, True)

    @asyncio.coroutine
    def async_set_child_lock_off(self):
        """Turn the child lock off."""
        yield from self._try_command(
            "Turning the child lock of the air purifier off failed.",
            self._air_purifier.set_child_lock, False)

    @asyncio.coroutine
    def async_set_led_brightness(self, brightness: int=2):
        """Set the led brightness."""
        from miio.airpurifier import LedBrightness

        yield from self._try_command(
            "Setting the led brightness of the air purifier failed.",
            self._air_purifier.set_led_brightness, LedBrightness(brightness))

    @asyncio.coroutine
    def async_set_favorite_level(self, level: int=1):
        """Set the favorite level."""
        yield from self._try_command(
            "Setting the favorite level of the air purifier failed.",
            self._air_purifier.set_favorite_level, level)
