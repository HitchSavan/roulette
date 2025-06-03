"""
Roulette modeling module.

Contains functions for calculating roulette wheel moving.

Full wheel life cycle (from start to stop) consists of three stages:
1. Acceleration stage - initial speed is zero, spins sime time with
    positive acceleration until calculated speed is met;
2. Linear stage - spin some time with 0 acceleration and constant speed;
3. Decceleration stage - initial speed equals speed from stage 2,
    acceleration is negative, wheel spins until full stop.
"""
from enum import Enum, auto

import utils

SPIN_COEF_MIN = 1
SPIN_COEF_MAX = 10
SPIN_COEF_MIN_NORM = 0.5
SPIN_COEF_MAX_NORM = 1.5

class Stages(Enum):
    ACCELERATION_STAGE = auto()
    LINEAR_STAGE = auto()
    DECCELERATION_STAGE = auto()
    STOP = auto()

class Stage:
    # duration is percentage of full spin time; total sum must be not greater than 1
    def __init__(self, stage_type: Stages, start_time: float, duration: float):
        self.stage_type = stage_type
        self.duration = duration
        self.start_time = start_time

    def get_end_time(self) -> float:
        return self.start_time + self.duration

    def is_active(self, cur_time: float) -> float:
        return cur_time >= self.start_time and cur_time < self.get_end_time()

total_time_template = 100
accel_stage = Stage(Stages.ACCELERATION_STAGE, 0, total_time_template * 0.3)
linear_stage = Stage(Stages.LINEAR_STAGE, accel_stage.get_end_time(), total_time_template * 0.3)
deccel_stage = Stage(Stages.DECCELERATION_STAGE, linear_stage.get_end_time(), total_time_template - linear_stage.get_end_time())
stages_order = [
        accel_stage,
        linear_stage,
        deccel_stage
    ]

def get_current_stage(cur_time: float) -> Stage:
    for stage in stages_order:
        if stage.is_active(cur_time):
            return stage
    return Stage(Stages.STOP, 0, 0)


def get_spins_amount(spins_amount_coeff: int, spin_time: float) -> int:
    """
    Calculates wheel `spins amount` from the given `spin time`
    and `spin coeff`
    """

    normalized_coeff = utils.interpolate(
        spins_amount_coeff,
        SPIN_COEF_MIN,
        SPIN_COEF_MAX,
        SPIN_COEF_MIN_NORM,
        SPIN_COEF_MAX_NORM,
    )
    spins_amount = int(normalized_coeff * spin_time)

    return spins_amount


def get_initial_speed(
    target_angle: float, spins_amount: int, target_time: float, initial_angle: float = 0
) -> float:
    """
    Clalculates wheel `initial speed` from the given `target
    angle`, `amount of spins`, `spin time` and `initial angle`
    """

    total_path = target_angle + 360 * spins_amount - initial_angle
    initial_speed = 2 * total_path / target_time

    return initial_speed


def get_linear_stage_speed(
    target_angle: float, spins_amount: int, target_time: float, initial_angle: float = 0
) -> float:
    """
    Clalculates wheel `initial speed` for linear movement stage from the given
    `target angle`, `amount of spins`, `spin time` and `initial angle`
    """

    total_path = target_angle + 360 * spins_amount - initial_angle

    t1 = target_time * accel_stage.get_end_time()
    t2 = target_time * linear_stage.get_end_time()
    t3 = target_time

    linear_speed = total_path / ( (t1 + t2 - t3) / 2 - t1 + t3 )

    return linear_speed


def get_acceleration(initial_speed: float, target_time: float, final_speed: float = 0) -> float:
    """
    Calculates wheel acceleration from the given `initial speed`,
    `target time` and `final speed`
    """

    acceleration = (final_speed - initial_speed) / target_time

    return acceleration


def get_angle(
    initial_speed: float, acceleration: float, cur_time: float, initial_angle: float = 0
) -> float:
    """
    Returns `wheel position` (angle in degrees between 0 and 360)
    at the given `time` from the given `acceleration`, `initial
    speed`, and `initial angle`
    """

    angle = (
        initial_angle + initial_speed * cur_time + (acceleration * pow(cur_time, 2)) / 2
    )

    return angle % 360


def get_speed(initial_speed: float, acceleration: float, cur_time: float) -> float:
    """
    Returns `wheel speed` at the given `time` from the given `initial
    speed` and `acceleration`
    """

    cur_speed = initial_speed + acceleration * cur_time

    return cur_speed
