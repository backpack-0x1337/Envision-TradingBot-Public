import enum

class Candle(enum.Enum):
    up_bar = 0
    down_bar = 1
    inside_bar = 2
    outside_bar = 3



# Function return the current bar type
# input a directory contain previous high previous low latest high latest low
# output type of Candle
def get_bar_type(info_list):
    ph, pl, ch, cl = info_list
    return