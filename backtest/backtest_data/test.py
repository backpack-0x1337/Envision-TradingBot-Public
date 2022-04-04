from os import path
import pandas as pd

class TimeFrameData:
    def __init__(self,time,green,red,blue,white):
        self.white = white
        self.blue = blue
        self.red = red
        self.green = green
        self.time = time


def changeClassData(tf):
    tf.white = 1

def main():
    tf = TimeFrameData(None,None,None,None,None)
    changeClassData(tf)
    print(tf.white)

if __name__ == '__main__':
    main()