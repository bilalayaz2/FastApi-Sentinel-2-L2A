from sentinelhub import SHConfig
import numpy as np
import os
import datetime
from sentinelhub import MimeType, CRS, BBox, SentinelHubRequest, SentinelHubDownloadClient, DataCollection, bbox_to_dimensions, DownloadRequest, Geometry





class Sent:
  def __init__(self, st_date, en_date, points=None, es = "rgb"):
    self.st_date = st_date
    self.en_date = en_date
    self.points = points
    self.es = es
    self.config = SHConfig()
    self.config.sh_client_secret = '.[rPT/|A?/I)({^z.)x2_,D{HhJ^;EHq[DYv~UQ['
    self.config.sh_client_id = '2bd35ae0-96d0-49d9-a575-b5b63a3c02f0'
    self.config.save()
    
  # if not config.sh_client_id or not config.sh_client_secret:
  #     print("Warning! To use Process API, please provide the credentials (OAuth client ID and client secret).")
  # else:
  #     print('Step 1: Initialization Completed Succesfully.')

  def swap(self,list,check):
      n = 2 if len(list)%2 == 0 else 3
      for i in range(0,len(list),n):
          list[i],list[i+1] = float(list[i+1]), float(list[i])
      if(check):
          list.append(list[0])
          list.append(list[1]) 
      return list

  def ev_s(self):
    true = """
    //VERSION=3
    function setup(){
      return{
        input: ["B02", "B03", "B04", "dataMask"],
        output: {bands: 4}
      }
    }

    function evaluatePixel(sample){
      // Set gain for visualisation
      let gain = 2.5;
      // Return RGB
      return [sample.B04 * gain, sample.B03 * gain, sample.B02 * gain, sample.dataMask];
    }
    """


    
    evalscript_ndvi_new = """
    var naturalColour = [3*B04, 3*B03, 3*B02];

    let ndviColorMap = [
      [-1.0, 0x000000],
      [-0.2, 0xA50026],
      [0.0,  0xD73027],
      [0.1,  0xF46D43],
      [0.2,  0xFDAE61],
      [0.3,  0xFEE08B],
      [0.4,  0xFFFFBF],
      [0.5,  0xD9EF8B],
      [0.6,  0xA6D96A],
      [0.7,  0x66BD63],
      [0.8,  0x1A9850],
        [0.9,  0x006837]
    ];

    function index(x, y) {
      return (x - y) / (x + y);
    }

    function toRGB(val) {
      return [val >>> 16, val >>> 8, val].map(x => (x & 0xFF) / 0xFF);
    }

    function findColor(colValPairs, val) {
      let n = colValPairs.length;
      for (let i = 1; i < n; i++) {
        if (val <= colValPairs[i][0]) {
          return toRGB(colValPairs[i-1][1]);
        }
      }
      return toRGB(colValPairs[n-1][1]);
    }

    return findColor(ndviColorMap, index(B8A, B04))
    """
    
    wat = """//
    VERSION=3
    //This script was converted from v1 to v3 using the converter API

    //ndwi
    var colorRamp1 = [
        [0, 0xFFFFFF],
        [1, 0x008000]
      ];
    var colorRamp2 = [
        [0, 0xFFFFFF],
        [1, 0x0000CC]
      ];

    let viz1 = new ColorRampVisualizer(colorRamp1);
    let viz2 = new ColorRampVisualizer(colorRamp2);

    function evaluatePixel(samples) {
      var val = index(samples.B03, samples.B08);

      if (val < -0) {
        return viz1.process(-val);
      } else {
        return viz2.process(Math.sqrt(Math.sqrt(val)));
      }
    }

    function setup() {
      return {
        input: [{
          bands: [
            "B03",
            "B08"
          ]
        }],
        output: {
          bands: 3
        }
      }
    }
    """
    if self.es == "rgb":
      return true
    
    if self.es == "ndvi":
      return evalscript_ndvi_new
      
    if self.es == "ndwi":
      return wat
    
  def evalscript_request(self,time_interval,evalscript,geometry, size):
      return SentinelHubRequest(
          evalscript=evalscript,
          input_data=[
              SentinelHubRequest.input_data(
                  data_collection = DataCollection.SENTINEL2_L2A,
                  time_interval = time_interval,
                  # mosaicking_order = 'leastCC',
                  other_args = {"dataFilter": {"maxCloudCoverage": 0}},
                  # maxcc = 10
              )
          ],
          responses=[
              SentinelHubRequest.output_response('default', MimeType.TIFF)
          ],
          geometry=geometry,
          size=size,
          config=self.config
      )
  # print('Step 3: Setup EvalScript Completed Successfully.')


  def dat(self):
      y1, m1, d1 = self.st_date.split(",")
      y2, m2, d2 = self.en_date.split(",")
      
      
      start =datetime.datetime(int(y1),int(m1),int(d1))
      end = datetime.datetime(int(y2),int(m2),int(d2))
            
      n_chunks = 2
      tdelta = (end - start) / n_chunks
      edges = [(start + i*tdelta).date().isoformat() for i in range(n_chunks)]
      slots = [(edges[i], edges[i+1]) for i in range(len(edges)-1)]
      # print("slots done")
      # return slots
      
      
      data = []
      geometry = Geometry(geometry={"type":"Polygon","coordinates":[np.reshape(self.swap(self.points,1), (-1, 2))]}, crs=CRS.WGS84)
      size = bbox_to_dimensions(geometry.bbox, resolution=10)
      list_of_requests = [self.evalscript_request(slot, self.ev_s(), geometry, size) for slot in slots]
      list_of_requests = [request.download_list[0] for request in list_of_requests]
      data.append(SentinelHubDownloadClient(config=self.config).download(list_of_requests, max_threads=5))
      # print("data downloaded")
      
      return data
    
    
if __name__ == '__main__':
  a = Sent("2020,3,12", "2020,4,13", ["30.396205893130897","73.5142720118165","30.396216593214966","73.51282797753811","30.394866638221142","73.5128889977932","30.394874157302326","73.51428642868996"], "rgb").dat()
  # print(a)
  
  