import threading
import time
import os
import pandas as pd # type: ignore
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
import pyrealsense2 as rs
import uhd
from ultralytics import YOLO # type: ignore

from math import atan2, degrees
import datetime
import serial # type: ignore
import socket
from collections import deque
import subprocess
import joblib # type: ignore
import argparse

# Import custom modules

from usrp_control import *
from controlrotor import *
from sivers_control import *


# Add the root path so we can import the configurations module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from configurations.utils import *
from configurations.config import *
