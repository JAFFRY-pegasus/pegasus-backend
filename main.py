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
    import requests  # utilisé seulement si QUINTE_JSON_URL est défini
except ImportError:  # pragma: no cover
    requests = None

app = FastAPI()

# ==============================================================================
# 1. BASE HISTORIQUE COMPLÈTE (220 QUINTÉS)
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
 
