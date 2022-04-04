from db import datebase as db
import json, os.path
import pandas as pd
from flask import Flask, request, jsonify
from os import path
from db import create_CSV
from util import convertors as cv

password = "123"


def main(dataList, time_frame_data_array):
    # validate password
    if dataList['Password'] != password:
        return "ERROR_PASSWORD"

    time_frame_data_array[0] = cv.roundStringToDecimal(dataList['G'], 2)
    time_frame_data_array[1] = cv.roundStringToDecimal(dataList['R'], 2)
    time_frame_data_array[2] = cv.roundStringToDecimal(dataList['B'], 2)
    time_frame_data_array[3] = cv.roundStringToDecimal(dataList['W'], 2)

    return time_frame_data_array
