from matplotlib import pyplot as plt
import numpy as np
from PIL import Image,ImageFilter
import pytesseract

from operator import itemgetter

def coords(arr,x0,y0,w,h):
    out = arr[y0:y0+h,x0:x0+w]
    return out

def read_string(arr,x0,y0,w,h):
    slicedarr = coords(arr,x0,y0,w,h)
    img = Image.fromarray(500*slicedarr).convert('LA')
    img = img.resize([img.width*5,img.height*5])
    img2 = img.filter(ImageFilter.GaussianBlur(2.7))
    #out =  pytesseract.image_to_string(img2,config='digits')
    out =  pytesseract.image_to_string(img2)
    return out

    
def _getTestName(instance,testnamecoords):
    return read_string(instance,*testnamecoords)

def _getPage(instance,pagecoords):
    return read_string(instance,*pagecoords)


    

class DailyQCparse:
    def __init__(self, data, results, action):

        try:
            self.params = action['params']
        except KeyError:
            self.params = {}
 


        print(self.params)
        self.testnamecoords = [int(elem) for elem in self.params['ocr_regions']['TestName']['xywh'].split(';')]
        self.pagecoords = [int(elem) for elem in self.params['ocr_regions']['PageName']['xywh'].split(';')]

        self.n1l = self.params['ocr_regions']['QuaNoise1']['prefix']
        self.n1c = self.params['ocr_regions']['QuaNoise1']['xywh'].split(';')
        self.n2l = self.params['ocr_regions']['QuaNoise2']['prefix']
        self.n2c = self.params['ocr_regions']['QuaNoise2']['xywh'].split(';')
        self.n3l = self.params['ocr_regions']['QuaNoise3']['prefix']
        self.n3c = self.params['ocr_regions']['QuaNoise3']['xywh'].split(';')
        self.n4l = self.params['ocr_regions']['QuaNoise4']['prefix']
        self.n4c = self.params['ocr_regions']['QuaNoise4']['xywh'].split(';')

        self.noisetestdict = {self.n1l:self.n1c,self.n2l:self.n2c,self.n3l:self.n3c,self.n4l:self.n4c}



        self.h1l = self.params['ocr_regions']['HomA1']['prefix']
        self.h1c = self.params['ocr_regions']['HomA1']['xywh'].split(';')
        self.h2l = self.params['ocr_regions']['HomA2']['prefix']
        self.h2c = self.params['ocr_regions']['HomA2']['xywh'].split(';')
        self.h3l = self.params['ocr_regions']['HomA3']['prefix']
        self.h3c = self.params['ocr_regions']['HomA3']['xywh'].split(';')
        self.h4l = self.params['ocr_regions']['HomA4']['prefix']
        self.h4c = self.params['ocr_regions']['HomA4']['xywh'].split(';')

        self.hom1testdict = {self.h1l:self.h1c,self.h2l:self.h2c,self.h3l:self.h3c,self.h4l:self.h4c}

        
        print(self.testnamecoords)


        self.data = data.getAllSeries()[0]

        self.acqtimesorted = []
        for instance in self.data:
            self.acqtimesorted.append((instance.AcquisitionTime,instance))

        self.acqtimesorted = sorted(self.acqtimesorted)

        self.qctests = {"Noise":self.acqtimesorted[2][1],"Homogeneity1":self.acqtimesorted[0][1],"Homogeneity2":self.acqtimesorted[1][1]}


        for key in self.qctests.keys():
            tmpoverlay = self.load_overlay(self.qctests[key])

            fig = plt.figure()
            ax = plt.gca()
            ax.set_facecolor('black')
            plt.imshow(tmpoverlay)
            
            varname = key+'_'+'Image'
            filename = varname+'.jpg'
            plt.savefig(filename)
            
            results.addObject(varname,filename)
            
            #testname = _getTestName(tmpoverlay,self.testnamecoords)
            #tmppage = _getPage(tmpoverlay,self.pagecoords)

            if  key == 'Noise':
               print ('Getting QuaNoise results')
               for test in self.noisetestdict.keys():
                   tmpc = [int(e) for e in self.testdict[test]]
                   print(test)
                   for i in range(6):
                       img = Image.fromarray(5000*coords(tmpoverlay,tmpc[0]+i*50,tmpc[1],tmpc[2],tmpc[3])).convert('LA')
                       img = img.resize([img.width*5,img.height*5])
                       img2 = img.filter(ImageFilter.GaussianBlur(2.7))
                       print(i,pytesseract.image_to_string(img2,config='digits'))
                       results.addFloat(str(test)+'_row_'+str(i),pytesseract.image_to_string(img2,config='digits'))
        

            if  key == 'Homogeneity1':
               print ('Getting Homogeneity results 1/2')
               for test in self.hom1testdict.keys():
                   tmpc = [int(e) for e in self.testdict[test]]
                   print(test)
                   for i in range(6):
                       img = Image.fromarray(5000*coords(tmpoverlay,tmpc[0]+i*50,tmpc[1],tmpc[2],tmpc[3])).convert('LA')
                       img = img.resize([img.width*5,img.height*5])
                       img2 = img.filter(ImageFilter.GaussianBlur(2.7))
                       print(i,pytesseract.image_to_string(img2,config='digits'))
                       results.addFloat(str(test)+'_row_'+str(i),pytesseract.image_to_string(img2,config='digits'))

                       
    def load_overlay(self,ds):

        overlay_data = ds[0x60003000].value
        rows = ds[0x60000010].value
        cols = ds[0x60000011].value
        overlay_frames = ds[0x60000015].value
        overlay_type = ds[0x60000040].value
        bits_allocated = ds[0x60000100].value

        np_dtype = np.dtype('uint8')
        length_of_pixel_array = len(overlay_data)
        expected_length = rows * cols

        if bits_allocated == 1:
            expected_bit_length = expected_length
            expected_length = int(expected_length / 8) + (expected_length % 8 > 0)

            bit = 0
            arr = np.ndarray(shape=(length_of_pixel_array * 8), dtype=np_dtype)

            for byte in overlay_data:
                for bit in range(bit, bit + 8):
                    arr[bit] = byte & 1
                    byte >>= 1
                    bit += 1

            arr = arr[:expected_bit_length]

        if overlay_frames == 1:
            arr = arr.reshape(rows, cols)

        return arr


