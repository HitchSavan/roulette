import datetime
import tkinter as tk
import math
import random
from colorsys import hls_to_rgb
from time import sleep

def get_target_sector_degrees(total_sectors_amount: int, total_degrees = 360):
    one_sector_degrees = total_degrees / total_sectors_amount

    # position of target sector in order on wheel, use info from created wheel
    target_sector_number = random.randrange(total_sectors_amount)

    target_sector_pos = (one_sector_degrees * target_sector_number, one_sector_degrees * (target_sector_number + 1))
    return target_sector_pos


def get_initial_speed(target_time, total_path):
    return 2 * total_path / target_time

# target_position ∈ (0, 360] (circle degree)
def get_spin_stats(target_time, total_path):
    initial_speed = get_initial_speed(target_time, total_path)
    deceleration = -initial_speed / target_time

    return deceleration, initial_speed

def get_pos(initial_wheel_position, cur_time, initial_speed, deceleration):
    cur_speed = initial_speed + deceleration * cur_time
    if cur_speed <= 0:
        cur_speed = 0

    position = initial_wheel_position + initial_speed * cur_time + (deceleration * pow(cur_time, 2)) / 2

    return position, cur_speed

if __name__ == '__main__':

    ### test params definition start #######################################################################

    sectors_amount = 7

    time_step = 0.7
    target_time = 100 * time_step
    wheel_degrees = 360 # wow

    initial_wheel_position = random.randrange(wheel_degrees) - wheel_degrees # wheel tilt upon the start

    full_spins_amount = 0

    ### test params definition end #########################################################################

    target_sector_degrees = get_target_sector_degrees(sectors_amount)
    target_position = random.uniform(target_sector_degrees[0], target_sector_degrees[-1])
    total_path = target_position + wheel_degrees * full_spins_amount - initial_wheel_position

    # if total_path < initial_wheel_position or total_path < target_position:
    #     total_path += wheel_degrees

    deceleration, initial_speed = get_spin_stats(target_time, total_path)

    time = 0.0
    while not False:
        position, speed = get_pos(initial_wheel_position, time, initial_speed, deceleration)
        print(position, speed)
        if (speed <= 0):
            break
        sleep(0.1)
        time += time_step

    print('\nstarting position: ', initial_wheel_position)
    print('target position: ', target_position)
    print('result position: ', position % wheel_degrees)
    print('\nresult path: ', position - initial_wheel_position)
    print('needed path: ', total_path)
    print('total time: ', time)
    print('target time: ', target_time)