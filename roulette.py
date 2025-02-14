# needs configuring
def get_spins_amount(spins_amount_coeff, spin_time):
    spins_amount = spins_amount_coeff * spin_time
    return spins_amount

def get_initial_speed(target_angle, spins_amount, target_time, initial_angle = 0):
    total_path = target_angle + 360 * spins_amount - initial_angle
    initial_speed = 2 * total_path / target_time
    return initial_speed

def get_acceleration(initial_speed, target_time):
    return -initial_speed / target_time

def get_pos(initial_speed, acceleration, cur_time, initial_angle=0):
    cur_speed = initial_speed + acceleration * cur_time
    if cur_speed <= 0:
        cur_speed = 0

    position = initial_angle + initial_speed * cur_time + (acceleration * pow(cur_time, 2)) / 2

    return position % 360, cur_speed

def angle_to_sectors_amount(angle, sectors_amount):
    sector_size = 360 / sectors_amount
    return int((360 - angle) / (sector_size)) % sectors_amount