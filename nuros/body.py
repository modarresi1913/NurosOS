"""
Body Contract — Embodiment Abstraction.

A Body may be: physical robot, virtual avatar, simulation,
software environment, game world, API-connected agent,
neuromorphic hardware.

Body API exposes: sensors, actuators, state, constraints,
energy/resource availability, environment feedback.

Core principle: The same cognitive organism should be portable
between different bodies.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable


class BodyType(Enum):
    PHYSICAL_ROBOT = "physical_robot"
    VIRTUAL_AVATAR = "virtual_avatar"
    SIMULATION = "simulation"
    SOFTWARE_ENV = "software_environment"
    GAME_WORLD = "game_world"
    API_AGENT = "api_agent"
    NEUROMORPHIC_HW = "neuromorphic_hardware"
    ABSTRACT = "abstract"


@dataclass
class Sensor:
    """A sensor on the body."""
    name: str
    sensor_type: str  # "visual", "auditory", "olfactory", "tactile", "proprioceptive"
    dimensions: int = 1
    resolution: float = 1.0
    noise_level: float = 0.0
    last_reading: Optional[Any] = None
    last_timestamp: float = 0.0


@dataclass
class Actuator:
    """An actuator on the body."""
    name: str
    actuator_type: str  # "motor", "vocal", "emitter", "manipulator"
    degrees_of_freedom: int = 1
    max_force: float = 1.0
    precision: float = 1.0
    last_command: Optional[Any] = None


@dataclass
class BodyState:
    """Current state of the body."""
    position: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    velocity: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])
    energy: float = 1.0
    health: float = 1.0
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class BodyConstraints:
    """Physical and operational constraints on the body."""
    max_velocity: float = 1.0
    max_acceleration: float = 1.0
    max_force: float = 1.0
    spatial_bounds: Optional[list[list[float]]] = None  # [[x_min,y_min,z_min],[x_max,y_max,z_max]]
    energy_budget: float = 100.0
    allowed_actions: set[str] = field(default_factory=set)


class BodyContract:
    """
    The Body Contract — Embodiment Abstraction.

    Implements the Body portion of the Mind Contract Layer (MCL).
    Provides a portable interface between cognition and embodiment.
    The same cognitive organism can be connected to different bodies.
    """

    def __init__(self, body_type: BodyType = BodyType.ABSTRACT, body_id: str = ""):
        self._body_id = body_id or str(uuid.uuid4())
        self._body_type = body_type
        self._sensors: dict[str, Sensor] = {}
        self._actuators: dict[str, Actuator] = {}
        self._state = BodyState()
        self._constraints = BodyConstraints()
        self._sensor_callbacks: dict[str, Callable] = {}
        self._actuator_callbacks: dict[str, Callable] = {}
        self._connected: bool = False

    @property
    def body_id(self) -> str:
        return self._body_id

    @property
    def body_type(self) -> BodyType:
        return self._body_type

    @property
    def state(self) -> BodyState:
        return self._state

    @property
    def constraints(self) -> BodyConstraints:
        return self._constraints

    def add_sensor(self, name: str, sensor_type: str, dimensions: int = 1,
                   callback: Optional[Callable] = None) -> Sensor:
        sensor = Sensor(name=name, sensor_type=sensor_type, dimensions=dimensions)
        self._sensors[name] = sensor
        if callback:
            self._sensor_callbacks[name] = callback
        return sensor

    def add_actuator(self, name: str, actuator_type: str, dof: int = 1,
                     callback: Optional[Callable] = None) -> Actuator:
        actuator = Actuator(name=name, actuator_type=actuator_type, degrees_of_freedom=dof)
        self._actuators[name] = actuator
        if callback:
            self._actuator_callbacks[name] = callback
        return actuator

    def sense(self, sensor_name: str) -> Optional[Any]:
        """Read from a sensor."""
        sensor = self._sensors.get(sensor_name)
        if not sensor:
            return None
        if sensor_name in self._sensor_callbacks:
            reading = self._sensor_callbacks[sensor_name]()
            sensor.last_reading = reading
            sensor.last_timestamp = time.time()
            return reading
        return sensor.last_reading

    def act(self, actuator_name: str, command: Any) -> tuple[bool, str]:
        """Send a command to an actuator."""
        actuator = self._actuators.get(actuator_name)
        if not actuator:
            return False, f"Actuator '{actuator_name}' not found"
        actuator.last_command = command
        if actuator_name in self._actuator_callbacks:
            try:
                self._actuator_callbacks[actuator_name](command)
                return True, "Command executed"
            except Exception as e:
                return False, f"Command failed: {e}"
        return True, "Command queued (no callback)"

    def update_state(self, **kwargs) -> None:
        """Update body state fields."""
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def summary(self) -> dict:
        return {
            "body_id": self._body_id,
            "type": self._body_type.value,
            "connected": self._connected,
            "sensors": {n: s.sensor_type for n, s in self._sensors.items()},
            "actuators": {n: a.actuator_type for n, a in self._actuators.items()},
            "energy": self._state.energy,
            "health": self._state.health,
        }
