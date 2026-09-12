from typing import Union
from datetime import datetime

# Time step 't' can be an index (int) or timestamp (datetime).
# Marked as Union pending final timezone/ID architecture decisions.
TimeStep = Union[int, datetime]