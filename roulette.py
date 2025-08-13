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
from enum import Enum
import logging

import utils

SPIN_COEF_MIN = 1
SPIN_COEF_MAX = 10
SPIN_COEF_MIN_NORM = 0.5
SPIN_COEF_MAX_NORM = 1.5

logging.basicConfig(filename="debug.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


class Stages(Enum):
    ACCELERATION_STAGE = 1
    LINEAR_STAGE = 0
    DECCELERATION_STAGE = -1
    STOP = 2

    def __eq__(self, r) -> bool:
        return self.value == r.value

    def __gt__(self, r) -> bool:
        return self.value > r.value

    def __hash__(self) -> int:
        return super().__hash__()


class Stage:
    def __init__(
            self, stage_type: Stages, duration: float,
            start_time: float = 0, start_speed: float = 0,
            end_speed: float = 0, total_spin_time: float = -1
    ) -> None:
        self.stage_type = stage_type

        if stage_type == Stages.STOP:
            return
        if duration < 0:
            logging.error("negative stage duration")
            raise ValueError("Stage duration cannot be negative")

        self.time_coefficient = -1

        self.duration = duration
        if total_spin_time != -1:
            self.time_coefficient = self.duration / total_spin_time

        self.start_time = start_time
        self.start_speed = start_speed
        self.end_speed = end_speed
        self.acceleration = get_acceleration(
            self.start_speed, self.duration, self.end_speed)

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
        self.acceleration = get_acceleration(
            self.start_speed, self.duration, self.end_speed)

    def update_acceleration(self, start_speed: float = -1,
                            duration: float = -1, end_speed: float = -1) -> None:
        if start_speed != -1:
            self.start_speed = start_speed
        if duration != -1:
            self.duration = duration
        if end_speed != -1:
            self.end_speed = end_speed
        self.acceleration = get_acceleration(
            self.start_speed, self.duration, self.end_speed)

    def get_total_path(self):
        return self.start_speed * self.duration + self.acceleration * pow(self.duration, 2) / 2


STOP_ID = -1
STOP_STAGE = Stage(Stages.STOP, 0)


class StagesController:
    def __init__(self, total_spin_time: float, stage_order: "list[Stage]" = []) -> None:
        self.stage_order = stage_order
        self.active_stage_id = 0
        self.total_spin_time = total_spin_time
        self.total_stages_duration = 0

        self.stages_by_type: dict[Stages, Stage] = {}
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
        stage = Stage(stage_type, duration, 0, start_speed,
                      end_speed, self.total_spin_time)
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
                start_time, new_total_time,
                (stage.time_coefficient
                 if stage.time_coefficient != -1
                 else stage.duration / self.total_spin_time)
            )
            start_time = stage.get_end_time()
            self.total_stages_duration += stage.duration
        if self.total_stages_duration != new_total_time:
            self.stage_order[-1].duration += new_total_time - \
                self.total_stages_duration
            logging.warning("total stages time updating mismatch")
            print('-----------=============time update mismatch=============-----------')
            self.total_stages_duration = new_total_time

        self.total_spin_time = new_total_time

    def next_stage(self, cur_time: float) -> Stage:
        self.get_current_stage(cur_time)
        next_id = self.active_stage_id + 1
        return (self.stage_order[next_id]
                if next_id != len(self.stage_order)
                else STOP_STAGE)

    def prev_stage(self, cur_time: float) -> Stage:
        self.get_current_stage(cur_time)
        return (self.stage_order[self.active_stage_id - 1]
                if self.active_stage_id != 0
                else STOP_STAGE)


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
    target_angle: float, spins_amount: int,
    stages_list: 'list[Stage]', initial_angle: float = 0
) -> float:
    """
    Calculates wheel `initial speed` from the `target angle`,
    `spins amount` and `stages list`
    """

    if len(stages_list) != 3:
        raise ValueError(
            f'Stages amount must be 3 ({len(stages_list)} is given)')

    total_path = target_angle + 360 * spins_amount - initial_angle

    t1 = stages_list[0].duration
    t2 = stages_list[1].duration
    t3 = stages_list[2].duration

    a1 = stages_list[0].acceleration
    a2 = stages_list[1].acceleration
    a3 = stages_list[2].acceleration

    initial_speed = (total_path - (
        a1*pow(t1, 2)/2 +
        a2*pow(t2, 2)/2 +
        a3*pow(t3, 2)/2 +
        a1*t1*t2 +
        a1*t1*t3 +
        a2*t2*t3)
    ) / (t1 + t2 + t3)

    v2 = initial_speed + a1*t1
    v3 = v2 + a2*t2

    logging.debug('''new
                  total path: %f
                  calc total path: %f

                  initial 1st phase speed: %f
                  1st phase duration: %f
                  1st phase accel: %f
                  1st phase total path: %f

                  initial 2nd phase speed: %f
                  2nd phase duration: %f
                  2nd phase accel: %f
                  2nd phase total path: %f

                  initial 3rd phase speed: %f
                  3rd phase duration: %f
                  3rd phase accel: %f
                  3rd phase total path: %f
--------------''', total_path,
                  initial_speed * t1 + a1 * pow(t1, 2) / 2 +
                  v2 * t2 + a2 * pow(t2, 2) / 2 +
                  v3 * t3 + a3 * pow(t3, 2) / 2,
                  initial_speed, t1, a1,
                  initial_speed * t1 + a1 * pow(t1, 2) / 2,
                  v2, t2, a2, v2 * t2 + a2 * pow(t2, 2) / 2,
                  v3, t3, a3, v3 * t3 + a3 * pow(t3, 2) / 2
                  )

    return initial_speed


def get_simple_initial_speed(
    target_angle: float, spins_amount: int,
    target_time: float, initial_angle: float = 0
) -> float:
    """
    Calculates wheel `initial speed` from the given `target
    angle`, `amount of spins`, `spin time` and `initial angle`
    """

    total_path = target_angle + 360 * spins_amount - initial_angle
    initial_speed = 2 * total_path / target_time

    return initial_speed


def get_linear_stage_speed(
    target_angle: float, spins_amount: int, target_time: float,
    linear_start_time: float, linear_end_time: float,
    initial_angle: float = 0
) -> float:
    # for stages arrangement "acceleration-linear-decceleration"
    """
    Calculates wheel `initial speed` for linear movement stage from the given
    `target angle`, `amount of spins`, `spin time` and `initial angle`
    """

    total_path = target_angle + 360 * spins_amount - initial_angle

    t1 = linear_start_time
    t2 = linear_end_time
    t3 = target_time

    linear_speed = total_path / ((t1 + t2 - t3) / 2 - t1 + t3)

    return linear_speed


def get_acceleration(initial_speed: float, target_time: float, final_speed: float = 0) -> float:
    """
    Calculates wheel acceleration from the given `initial speed`,
    `target time` and `final speed`
    """

    acceleration = (
        (final_speed - initial_speed) / target_time
        if target_time > 0
        else 0
    )

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
        initial_angle + initial_speed * cur_time +
            (acceleration * pow(cur_time, 2)) / 2
    )

    return angle % 360


def get_speed(initial_speed: float, acceleration: float, cur_time: float) -> float:
    """
    Returns `wheel speed` at the given `time` from the given `initial
    speed` and `acceleration`
    """

    cur_speed = initial_speed + acceleration * cur_time

    return cur_speed
