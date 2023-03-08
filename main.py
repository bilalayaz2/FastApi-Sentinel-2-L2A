from util import Sent
from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import Any, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import io
from imageio import v3 as iio
from fastapi.responses import JSONResponse

app = FastAPI()

class Track(BaseModel):
    st_date : str
    en_date : str
    points : list
    es: str
     

@app.post("/")
def root(track: Track):
    track_dict = track.dict()
    st = track_dict["st_date"]
    en = track_dict["en_date"]
    pt = track_dict["points"]
    es = track_dict["es"]
    data = Sent(st, en, pt, es).dat() 
    if es != "all_bands":
        with io.BytesIO() as buf:
            iio.imwrite(buf, data[0], plugin="pillow", format="png")
            im_bytes = buf.getvalue()
        return Response(im_bytes, media_type='image/png')
    else:
        return data