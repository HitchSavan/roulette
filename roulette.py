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
    def __init__(
            self, stage_type: Stages, duration: float,
            start_time: float = 0, start_speed: float = 0,
            end_speed: float = 0, total_spin_time : float = -1
            ) -> None:
        self.stage_type = stage_type

        if stage_type == Stages.STOP:
            return
        if duration < 0:
            raise ValueError("Stage duration cannot be negative")

        self.duration = duration
        if total_spin_time != -1:
            self.time_coefficient = self.duration / total_spin_time

        self.start_time = start_time
        self.start_speed = start_speed
        self.end_speed = end_speed
        self.acceleration = get_acceleration(self.start_speed, self.duration, self.end_speed)

    def get_end_time(self) -> float:
        return self.start_time + self.duration

    def is_active(self, cur_time: float) -> float:
        return cur_time >= self.start_time and cur_time < self.get_end_time()

    def update_total_time(
            self, start_time: float, total_time: float, time_coefficient: float
            ) -> None:
        self.time_coefficient = time_coefficient
        self.start_time = start_time
        self.duration = total_time * self.time_coefficient
        self.acceleration = get_acceleration(self.start_speed, self.duration, self.end_speed)

    def update_acceleration(self, start_speed: float, duration: float, end_speed: float) -> None:
        self.start_speed = start_speed
        self.duration = duration
        self.end_speed = end_speed
        self.acceleration = get_acceleration(self.start_speed, self.duration, self.end_speed)

STOP_ID = -1
STOP_STAGE = Stage(Stages.STOP, 0)

class StagesController:
    def __init__(self, total_spin_time: float, stage_order: "list[Stage]" = []) -> None:
        self.stage_order = stage_order
        self.active_stage_id = 0
        self.total_spin_time = total_spin_time
        self.total_stages_duration = 0

        self.stages_by_type = {}
        for stage in self.stage_order:
            self.stages_by_type[stage.stage_type] = stage

    def clear_stages(self) -> None:
        self.stage_order.clear()
        self.active_stage_id = 0
        self.total_stages_duration = 0

    def append_stage(self, stage: Stage) -> None:
        stage.start_time = (self.stage_order[-1].get_end_time()
                            if len(self.stage_order) > 0
                            else 0)
        self.stage_order.append(stage)
        self.total_stages_duration += stage.duration

        cur_stage_type = stage.stage_type
        self.stages_by_type[cur_stage_type] = stage

    def emplace_stage(
            self, stage_type: Stages, duration: float,
            start_speed: float = 0, end_speed: float = 0
            ) -> None:
        stage = Stage(stage_type, duration, 0, start_speed, end_speed, self.total_spin_time)
        self.append_stage(stage)

    def get_current_stage(self, cur_time: float) -> Stage:
        for stage_id in range(self.active_stage_id, len(self.stage_order)):
            if stage_id == STOP_ID:
                continue
            stage = self.stage_order[stage_id]
            if stage.is_active(cur_time):
                self.active_stage_id = stage_id
                return stage
        self.active_stage_id = STOP_ID
        return STOP_STAGE

    def update_total_time(self, new_total_time: float) -> None:
        start_time = 0
        self.total_stages_duration = 0
        for stage in self.stage_order:
            stage.update_total_time(
                start_time, new_total_time, stage.duration / self.total_spin_time
                )
            start_time = stage.get_end_time()
            self.total_stages_duration += stage.duration
        self.total_spin_time = new_total_time

    def next_stage(self, cur_time: float) -> Stage:
        self.get_current_stage(cur_time)
        next_id = self.active_stage_id + 1
        if next_id == len(self.stage_order):
            return STOP_STAGE
        return self.stage_order[next_id]

    def prev_stage(self, cur_time: float) -> Stage:
        self.get_current_stage(cur_time)
        return self.stage_order[self.active_stage_id - 1]

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
    Calculates wheel `initial speed` from the given `target
    angle`, `amount of spins`, `spin time` and `initial angle`
    """

    total_path = target_angle + 360 * spins_amount - initial_angle
    initial_speed = 2 * total_path / target_time

    return initial_speed

# for stages arrangement "acceleration-linear-decceleration"
def get_linear_stage_speed(
    target_angle: float, spins_amount: int, target_time: float,
    accelertation_end_time: float, linear_end_time: float,
    initial_angle: float = 0
) -> float:
    """
    Calculates wheel `initial speed` for linear movement stage from the given
    `target angle`, `amount of spins`, `spin time` and `initial angle`
    """

    total_path = target_angle + 360 * spins_amount - initial_angle

    t1 = accelertation_end_time
    t2 = linear_end_time
    t3 = target_time

    linear_speed = total_path / ( (t1 + t2 - t3) / 2 - t1 + t3 )

    return linear_speed


def get_acceleration(initial_speed: float, target_time: float, final_speed: float = 0) -> float:
    """
    Calculates wheel acceleration from the given `initial speed`,
    `target time` and `final speed`
    """

    acceleration = ((final_speed - initial_speed) / target_time
                             if target_time > 0
                             else 0)

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
