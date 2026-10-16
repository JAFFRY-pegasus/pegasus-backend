import html
import json
import os
import time
from collections import Counter
from datetime import date as _date
from itertools import combinations
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

try:
    import requests
except ImportError:
    requests = None

app = FastAPI()

# ==============================================================================
# 1. BASE HISTORIQUE COMPLÈTE
# ==============================================================================
HISTORIQUE_SGE_DATA = [
  {"id": "1", "arrivee": [11, 4, 15, 6, 12]}, {"id": "2", "arrivee": [8, 14, 5, 13, 2]},
  {"id": "3", "arrivee": [9, 3, 16, 7, 10]}, {"id": "4", "arrivee": [1, 12, 6, 14, 8]},
  {"id": "5", "arrivee": [15, 7, 2, 11, 13]}, {"id": "6", "arrivee": [4, 10, 8, 5, 9]},
  {"id": "7", "arrivee": [13, 6, 14, 3, 1]}, {"id": "8", "arrivee": [2, 11, 7, 12, 16]},
  {"id": "9", "arrivee": [12, 5, 9, 15, 4]}, {"id": "10", "arrivee": [6, 14, 3, 8, 11]},
  {"id": "11", "arrivee": [10, 2, 13, 7, 5]}, {"id": "12", "arrivee": [7, 15, 1, 12, 9]},
  {"id": "13", "arrivee": [3, 8, 11, 14, 6]}, {"id": "14", "arrivee": [16, 4, 12, 9, 2]},
  {"id": "15", "arrivee": [5, 13, 6, 10, 8]}, {"id": "16", "arrivee": [14, 9, 2, 7, 15]},
  {"id": "17", "arrivee": [8, 1, 10, 13, 4]}, {"id": "18", "arrivee": [11, 6, 15, 3, 12]},
  {"id": "19", "arrivee": [2, 12, 5, 14, 7]}, {"id": "20", "arrivee": [9, 7, 4, 8, 11]},
  {"id": "21", "arrivee": [13, 3, 8, 16, 5]}, {"id": "22", "arrivee": [6, 10, 14, 2, 12]},
  {"id": "23", "arrivee": [1, 15, 7, 11, 9]}, {"id": "24", "arrivee": [12, 4, 9, 13, 6]},
  {"id": "25", "arrivee": [8, 11, 2, 5, 14]}, {"id": "26", "arrivee": [15, 6, 13, 10, 3]},
  {"id": "27", "arrivee": [4, 14, 8, 12, 7]}, {"id": "28", "arrivee": [7, 2, 11, 9, 16]},
  {"id": "29", "arrivee": [10, 8, 5, 15, 1]}, {"id": "30", "arrivee": [3, 13, 12, 6, 14]},
  {"id": "31", "arrivee": [16, 5, 9, 4, 11]}, {"id": "32", "arrivee": [11, 9, 3, 7, 2]},
  {"id": "33", "arrivee": [6, 14, 8, 12, 15]}, {"id": "34", "arrivee": [2, 10, 13, 5, 4]},
  {"id": "35", "arrivee": [12, 7, 1, 16, 9]}, {"id": "36", "arrivee": [5, 13, 14, 8, 6]},
  {"id": "37", "arrivee": [9, 3, 6, 11, 10]}, {"id": "38", "arrivee": [14, 8, 10, 2, 7]},
  {"id": "39", "arrivee": [7, 12, 15, 4, 13]}, {"id": "40", "arrivee": [4, 1, 9, 14, 5]},
  {"id": "41", "arrivee": [13, 11, 2, 8, 12]}, {"id": "42", "arrivee": [8, 6, 16, 3, 10]},
  {"id": "43", "arrivee": [10, 15, 5, 7, 14]}, {"id": "44", "arrivee": [1, 4, 12, 9, 6]},
  {"id": "45", "arrivee": [15, 9, 7, 13, 2]}, {"id": "46", "arrivee": [3, 12, 14, 6, 11]},
  {"id": "47", "arrivee": [11, 2, 8, 
