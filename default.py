# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with Kodi; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html

import sys
import xbmcaddon
import xbmcgui
import xbmc
import random
import json
from utils import *
#https://pypi.org/project/ExifRead/
import exifread

#img is the widget used to display the picture
#picture is the image read from the disk

ADDON = xbmcaddon.Addon()
__scriptname__ = ADDON.getAddonInfo("name")
__path__ = ADDON.getAddonInfo("path")

class Screensaver(xbmcgui.WindowXMLDialog):

    class ExitMonitor(xbmc.Monitor):
        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def onScreensaverDeactivated(self):
            xbmc.log("ExitMonitor: sending exit_callback")
            self.exit_callback()

    def onInit(self):
        xbmc.log("Picture Grid Screensaver: onInit")
        self.abort_requested = False
        self.slideshow_random = ADDON.getSettingBool("random")
        #type:0=video fanart;1=music fanarts;2=folder
        self.slideshow_type=ADDON.getSettingInt("type")
        #in case of a folder: this is its path
        self.slideshow_path=ADDON.getSettingString("path")
        #black border around pictures
        self.black_border=ADDON.getSettingInt("black_border")
        #delay between 2 changes (in ms)
        self.tempo=ADDON.getSettingInt("time")
        #will be 3 for a 3x3 grid, 2 for a 2x2 grid and 1 for a single image display
        self.grid_size=ADDON.getSettingInt("grid")
        #if we choose a random grid size, then we start with a 2x2 grid
        if ADDON.getSettingInt("grid")==0:
            self.grid_size=2        
        #keep aspect ratio or scale ?
        self.keepratio=ADDON.getSettingBool("keepratio")
        #if there's a commentaires.csv file containing lines like:
        #IMG_20140823_113529~01_DxO.jpg, my wonderful comment
        self.display_comments = ADDON.getSettingBool("comments")
        #skin (or addon?) virtual resolution (there's no way in kodi to query this). All positions are related
        #to this, not to the actual screen size
        self.skin_virtual_width=ADDON.getSettingInt("skin_virtual_width")
        self.skin_virtual_height=ADDON.getSettingInt("skin_virtual_height")
        
        #We can use up to 9 pictures
        #control id are defined in resources/skins/default/720p/script-main.xml
        self.img0 = self.getControl(101)
        self.img1 = self.getControl(102)
        self.img2 = self.getControl(103)
        self.img3 = self.getControl(104)
        self.img4 = self.getControl(105)
        self.img5 = self.getControl(106)
        self.img6 = self.getControl(107)
        self.img7 = self.getControl(108)
        self.img8 = self.getControl(109)
        if not self.keepratio:
            self.img0 = self.getControl(201)
            self.img1 = self.getControl(202)
            self.img2 = self.getControl(203)
            self.img3 = self.getControl(204)
            self.img4 = self.getControl(205)
            self.img5 = self.getControl(206)
            self.img6 = self.getControl(207)
            self.img7 = self.getControl(208)
            self.img8 = self.getControl(209)
        #just to remember the syntax
        #self.img0.setVisible(False)
        #to display comments:
        self.legend1=self.getControl(301)
        self.legend1.setVisible(False)
        
        self.monitor = self.ExitMonitor(self.exit)
        self.start_slideshow()
        
    def grid_order(self):
        """
        calculates the possible positions on the x and y axis for the images
        calculates the image sizes
        creates the img_index_list with the reference to the image position
        """
        self.posx=[0+self.black_border,int(self.skin_virtual_width/self.grid_size)+self.black_border,2*int(self.skin_virtual_width/self.grid_size)+self.black_border]
        self.posy=[0+self.black_border,int(self.skin_virtual_height/self.grid_size)+self.black_border,2*int(self.skin_virtual_height/self.grid_size)+self.black_border]
        self.img_width=int(self.skin_virtual_width/self.grid_size)-2*self.black_border
        self.img_height=int(self.skin_virtual_height/self.grid_size)-2*self.black_border

        if self.grid_size==3:
        #0 1 2
        #3 4 5
        #6 7 8
            self.img=[self.img0,self.img1,self.img2,self.img3,self.img4,self.img5,self.img6,self.img7,self.img8]
            self.img_index_list=[0,1,2,3,4,5,6,7,8]
        if self.grid_size==2:
        #0 1
        #2 3
            self.img=[self.img0,self.img1,self.img2,self.img3]
            self.img_index_list=[0,1,2,3]
        if self.grid_size==1:
            self.img=[self.img0]
            self.img_index_list=[0]      
        
    def positions(self):
        """
        depending on the grid size, the picture of img_index will be displayed top right, or bottom right.
        """
        #the first 2 positions are independent of the grid size
        if self.img_index==0:
            self.img_posx,self.img_posy=self.posx[0],self.posy[0]
        if self.img_index==1:
            self.img_posx,self.img_posy=self.posx[1],self.posy[0]
        
        if self.grid_size==2:
            if self.img_index==2:
                self.img_posx,self.img_posy=self.posx[0],self.posy[1]
            if self.img_index==3:
                self.img_posx,self.img_posy=self.posx[1],self.posy[1]
        
        if self.grid_size==3:
            if self.img_index==2:
                self.img_posx,self.img_posy=self.posx[2],self.posy[0]
            if self.img_index==3:
                self.img_posx,self.img_posy=self.posx[0],self.posy[1]
            if self.img_index==4:
                self.img_posx,self.img_posy=self.posx[1],self.posy[1]
            if self.img_index==5:
                self.img_posx,self.img_posy=self.posx[2],self.posy[1]
            if self.img_index==6:
                self.img_posx,self.img_posy=self.posx[0],self.posy[2]
            if self.img_index==7:
                self.img_posx,self.img_posy=self.posx[1],self.posy[2]
            if self.img_index==8:
                self.img_posx,self.img_posy=self.posx[2],self.posy[2]

    def _get_items(self, update=False):
        #code from screensaver.picture.slideshow from ronie
        xbmc.log('slideshow type: %i' % self.slideshow_type)
        # check if we have an image folder, else fallback to video fanart
        self.dict_from_csv = {} #for comments
        if self.slideshow_type == 2:
            hexfile = checksum(self.slideshow_path.encode('utf-8')) # check if path has changed, so we can create a new cache at startup
            xbmc.log('image path: %s' % self.slideshow_path)
            xbmc.log('update: %s' % update)
            if (not xbmcvfs.exists(CACHEFILE % hexfile)) or update: # create a new cache if no cache exits or during the background scan
                xbmc.log('create cache')
                create_cache(self.slideshow_path, hexfile)
            self.items = self._read_cache(hexfile)
            xbmc.log('items: %s' % len(self.items))
            if not self.items:
                self.slideshow_type = 0
                # delete empty cache file
                if xbmcvfs.exists(CACHEFILE % hexfile):
                    xbmcvfs.delete(CACHEFILE % hexfile)
            #comments from the file commentaires.csv            
            self.comments_csv_path=self.slideshow_path+'commentaires.csv'            
            #try:
            if self.display_comments:
                #we can t just use the csv module from python, because we also need to acces smb files for example
                #so we use xmbcvfs and convert manualy the csv to a dictionnary
                if xbmcvfs.exists(self.comments_csv_path):
                    with xbmcvfs.File(self.comments_csv_path) as inp:
                        file1=inp.read()
                        for item1 in file1.splitlines():
                            i = item1.split(', ')
                            self.dict_from_csv[i[0]] = i[1]
                        
	    # video fanart
        if self.slideshow_type == 0:
            methods = [('VideoLibrary.GetMovies', 'movies'), ('VideoLibrary.GetTVShows', 'tvshows')]
	    # music fanart
        elif self.slideshow_type == 1:
            methods = [('AudioLibrary.GetArtists', 'artists')]
        # query the db
        if not self.slideshow_type == 2:
            self.items = []
            for method in methods:
                json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "' + method[0] + '", "params": {"properties": ["art"]}, "id": 1}')
                json_response = json.loads(json_query)
                if 'result' in json_response and json_response['result'] != None and method[1] in json_response['result']:
                    for item in json_response['result'][method[1]]:
                        if 'fanart' in item['art']:
                            #self.items.append(item["art"]["fanart"])
                            self.items.append([item['art']['fanart'], item['label']])
        # randomize
        if self.slideshow_random:
            random.shuffle(self.items)
        #we need just the 1st column of this nested list
        self.paths=[element[0] for element in self.items]
        
    def _read_cache(self, hexfile):
         # code from screensaver.picture.slideshow from ronie
        try:
            cache = xbmcvfs.File(CACHEFILE % hexfile)
            images = json.load(cache)
            cache.close()
        except:
            images = []
        return images
    
    def start_slideshow(self):
        xbmc.log("get picture paths")
        #find the locations (paths) of the pictures
        self._get_items(update=True)
        xbmc.log("starting slide show")
        #calculates positions, sizes, img_index_list depending on the grid_size
        self.slideshow_init()
        #choose which image
        self.path_index=0
        self.path_index_max=len(self.paths)-1
        self.nb_repetitions=1
        while not self.abort_requested:
            #picture path. We reshuffle if we're at the end
            self.picture_path=self.paths[self.path_index]
            if self.path_index<self.path_index_max:
                self.path_index+=1
            else:
                self.path_index=0
                if self.slideshow_random:
                    random.shuffle(self.paths)
            #position of the picture (topleft, middle center,...):
            #the img_index_list is a shuffled list of the positions [0,2,3,1] for example
            self.img_index=self.img_index_list[self.img_count]
            cur_img=self.img[self.img_index]
            self.positions()
                        
            cur_img.setPosition(self.img_posx,self.img_posy)
            cur_img.setHeight(self.img_height)
            cur_img.setWidth(self.img_width)
            #If we don't want to use the cache
            #cur_img.setImage(picture_path,False)
            cur_img.setImage(self.picture_path)
            #exif test
            self.exif_orientation(cur_img)            
            
            cur_img.setVisible(True)
            #display the legend if it is present in commentaires.commentaires.csv (only when we have 1 picture full screen)
            if self.display_comments and (self.grid_size==1):
                self.display_legend()
            xbmc.sleep(self.tempo)
            #have we changed all the different pictures ? if yes, reshuffle
            if self.img_count<self.img_index_max:
                self.img_count+=1
            else:
                self.img_count=0
                random.shuffle(self.img_index_list)
            #random grid changes: every 12 or 24 or 36 pictures, we change the grid type
            nb_pict_modulo=12
            self.nb_pict_before_change=[1,nb_pict_modulo,2*nb_pict_modulo,3*nb_pict_modulo]
            if (ADDON.getSettingInt("grid")==0) and (self.path_index%(self.nb_pict_before_change[self.grid_size])==0):
                self.img_count=0
                old_grid_size=self.grid_size
                while old_grid_size==self.grid_size:
                    self.grid_size=random.randint(1,3)
                for widget in [self.img0,self.img1,self.img2,self.img3,self.img4,self.img5,self.img6,self.img7,self.img8]:
                    widget.setVisible(False)
                if self.grid_size==1:
                    self.tempo=2*ADDON.getSettingInt("time")
                else:
                    self.tempo=ADDON.getSettingInt("time")

                #now we re-initialise some parameters of the slideshow:
                self.slideshow_init()
    
    def exif_orientation(self,cur_img):
        """
        From exiftool documentation
        1 = Horizontal (normal)
        2 = Mirror horizontal
        3 = Rotate 180
        4 = Mirror vertical
        5 = Mirror horizontal and rotate 270 CW
        6 = Rotate 90 CW
        7 = Mirror horizontal and rotate 90 CW
        8 = Rotate 270 CW
        """
        exiffile = BinaryFile(self.picture_path)
        #print("exiffile",exiffile)
        self.orientation=[1]
        #self.exif_width=self.img_width
        #self.exif_length=self.img_height
        try:
            #exiftags = exifread.process_file(exiffile, details=False, stop_tag='DateTimeOriginal')
            #exiftags = exifread.process_file(exiffile, details=False, stop_tag='Image Orientation')
            exiftags = exifread.process_file(exiffile, details=False)
            #if 'EXIF DateTimeOriginal' in exiftags:
                #datetime = exiftags['EXIF DateTimeOriginal'].values
            if 'Image Orientation' in exiftags:
                self.orientation = exiftags['Image Orientation'].values
            #if 'Image ImageWidth' in exiftags:
                #self.exif_width = exiftags['Image ImageWidth'].values
            #if 'Image ImageLength' in exiftags:
                #self.exif_length = exiftags['Image ImageLength'].values
            #if 'EXIF ExifImageWidth' in exiftags:
                #self.exif_width = exiftags['EXIF ExifImageWidth'].values
            #if 'EXIF ExifImageLength' in exiftags:
                #self.exif_length = exiftags['EXIF ExifImageLength'].values
            
            #print(exiftags)

            #Image ImageWidth': (0x0100) Long=1578 @ 18, 'Image ImageLength': (0x0101) Long=2660
            #print(datetime)
            #zoom1=int(100*(self.img_height/self.exif_width[0]))
            #zoom1=int(100*(9/16)*(self.exif_width[0]))
            #zoom1=int(100*self.exif_length[0]*self.img_width/self.exif_width[0])
            #print("orientation",self.orientation,"width",self.exif_width[0],"zoom1",zoom1)
            
            
        except:
            pass     
        
        zoom1=int(100*(self.img_width-self.img_height-2*self.black_border)/self.img_height)
        #maybe I should do some rotatex or rotatey for the mirros in exif...
        if (self.orientation==[2]) or (self.orientation==[3]):            
            cur_img.setAnimations([('conditional','effect=rotate  center=auto start=0% end=180%  condition=true',),('conditional','effect=zoom  center=auto end='+str(zoom1)+'  time=0 condition=true',)])
        elif (self.orientation==[6]) or (self.orientation==[5]):
            cur_img.setAnimations([('conditional','effect=rotate  center=auto start=0% end=270%  condition=true',),('conditional','effect=zoom  center=auto end='+str(zoom1)+'  time=0 condition=true',)])
        elif (self.orientation==[8]) or (self.orientation==[7]):
            cur_img.setAnimations([('conditional','effect=rotate  center=auto start=0% end=90%  condition=true',),('conditional','effect=zoom  center=auto end='+str(zoom1)+'  time=0 condition=true',)])
        else:
            cur_img.setAnimations([('conditional','effect=rotate  center=auto start=0% end=0%  condition=true',)])
       
        ##print(self.picture_path,"orientation",self.orientation)
        #print("orientation",self.orientation,"width",self.exif_width,type(self.exif_width),self.exif_length,zoom1)
    
    def display_legend(self):
        """
        We can have some comments in the commentaires.csv file located in the same folder as pictures
        The format is
        relative_file_name, written comment. Example:
        IMG_20140823_113529.jpg, my wonderful comment
        This is a workaround for Google Photos not saving comments in the picture's exif
        but in a database (which can be converted to a csv file with the appropriate tool)
        """
        self.legend1.setVisible(False)
        self.legend1_label=self.dict_from_csv.get(os.path.basename(self.picture_path),"nothing")
        self.legend1_width=(len(self.legend1_label)+2)*13
        self.legend1_posx=int(self.skin_virtual_width/2-self.legend1_width/2)
        self.legend1_posy=int(0.9*self.skin_virtual_height)
        
        if self.legend1_label!="nothing":
            self.legend1.setLabel(self.legend1_label,textColor="0xFFFFFFFF")
            self.legend1.setWidth(self.legend1_width)
            self.legend1.setPosition(self.legend1_posx,self.legend1_posy)
            self.legend1.setVisible(True)

    def slideshow_init(self):
        #calculates positions, sizes, img_index_list depending on the grid_size
        self.grid_order()
        random.shuffle(self.img_index_list)
        ##choose where to display this image
        self.img_count=0
        self.img_index_max=len(self.img_index_list)-1
            
    def exit(self):
        self.abort_requested = True
        xbmc.log("Picture Grid Screensaver: Exit requested")
        self.close()
        
class BinaryFile(xbmcvfs.File):
    """
    useful for exifread
    """
    def read(self, numBytes: int = 0) -> bytes:
        if not numBytes:
            return b""
        return bytes(self.readBytes(numBytes))


if __name__ == "__main__":
    xbmc.log("Picture Grid Screensaver Main Started")
    screensaver_gui = Screensaver(
            "script-main.xml",
            __path__,
            "default",
        )
    screensaver_gui.doModal()
    xbmc.log("Picture Grid Screensaver Exited")
    del screensaver_gui
    sys.modules.clear()
