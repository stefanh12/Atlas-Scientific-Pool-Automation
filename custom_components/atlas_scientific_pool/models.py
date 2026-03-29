"""Model objects for Atlas Scientific Pool integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class NodeConfig:
    """Connection settings for one ESPHome node."""

    role: str
    host: str
    port: int
    noise_psk: str | None


@dataclass(slots=True)
class NodeCommandMap:
    """Entity object-id mapping for controlled dosing."""

    chlorine_volume_number: str
    acid_volume_number: str
    chlorine_dose_button: str
    acid_dose_button: str
    chlorine_stop_button: str
    acid_stop_button: str
    chlorine_running_binary_sensor: str
    acid_running_binary_sensor: str
    fill_start_button_object_id: str
    fill_stop_button_object_id: str
    fill_running_binary_sensor_object_id: str
    pump_power_switch_object_id: str
    pump_speed_low_switch_object_id: str
    pump_speed_medium_switch_object_id: str
    pump_speed_high_switch_object_id: str


@dataclass(slots=True)
class SafetyConfig:
    """Safety limits for pump operations."""

    controls_enabled: bool
    max_dose_ml: float
    cooldown_seconds: int
    default_chlorine_dose_ml: float
    default_acid_dose_ml: float
    enable_orp_automation: bool
    default_target_orp: float
    orp_sensor_object_id: str
    orp_hysteresis_mv: float
    enable_level_automation: bool
    default_target_water_level_percent: float
    level_hysteresis_percent: float
    level_sensor_object_id: str
    max_fill_runtime_minutes: int
    pool_volume_liters: float
    chlorine_strength_percent: float
    max_ppm_increase_per_dose: float
    acid_strength_percent: float
    max_ph_drop_per_dose: float
    total_alkalinity_ppm: float
    enable_notifications: bool
    notify_service: str
    ph_sensor_object_id: str
    ph_min_threshold: float
    ph_max_threshold: float
    orp_alert_threshold: float
    notification_cooldown_minutes: int


@dataclass(slots=True)
class CooldownState:
    """Last action timestamps used for throttling."""

    chlorine_dose_at: datetime | None = None
    acid_dose_at: datetime | None = None
