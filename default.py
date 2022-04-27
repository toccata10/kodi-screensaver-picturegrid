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
#import os
from utils import *
import threading

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
        xbmc.log("2 Screensaver: onInit")
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
        #keep aspect ratio or scale ?
        self.keepratio=ADDON.getSettingBool("keepratio")
        #skin (or addon?) virtual resolution (there's no way in kodi to query this). All positions are related
        #to this, not to the actual screen size
        self.skin_virtual_width=ADDON.getSettingInt("skin_virtual_width")
        self.skin_virtual_height=ADDON.getSettingInt("skin_virtual_height")
        self.img_width=int(self.skin_virtual_width/self.grid_size)-2*self.black_border
        self.img_height=int(self.skin_virtual_height/self.grid_size)-2*self.black_border
        #possible positions on the x and y axis for the images
        self.posx=[0+self.black_border,int(self.skin_virtual_width/self.grid_size)+self.black_border,2*int(self.skin_virtual_width/self.grid_size)+self.black_border]
        self.posy=[0+self.black_border,int(self.skin_virtual_height/self.grid_size)+self.black_border,2*int(self.skin_virtual_height/self.grid_size)+self.black_border]
        
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
        
        self.monitor = self.ExitMonitor(self.exit)
        self.start_slideshow()
        
    def positions(self):
        if self.grid_size==3:
            if self.img_index==0:
                self.img_posx=self.posx[0]
                self.img_posy=self.posy[0]
            if self.img_index==1:
                self.img_posx=self.posx[1]
                self.img_posy=self.posy[0]
            if self.img_index==2:
                self.img_posx=self.posx[2]
                self.img_posy=self.posy[0]
            if self.img_index==3:
                self.img_posx=self.posx[0]
                self.img_posy=self.posy[1]
            if self.img_index==4:
                self.img_posx=self.posx[1]
                self.img_posy=self.posy[1]
            if self.img_index==5:
                self.img_posx=self.posx[2]
                self.img_posy=self.posy[1]
            if self.img_index==6:
                self.img_posx=self.posx[0]
                self.img_posy=self.posy[2]
            if self.img_index==7:
                self.img_posx=self.posx[1]
                self.img_posy=self.posy[2]
            if self.img_index==8:
                self.img_posx=self.posx[2]
                self.img_posy=self.posy[2]

        if self.grid_size==2:
            if self.img_index==0:
                self.img_posx=self.posx[0]
                self.img_posy=self.posy[0]
            if self.img_index==1:
                self.img_posx=self.posx[1]
                self.img_posy=self.posy[0]
            if self.img_index==2:
                self.img_posx=self.posx[0]
                self.img_posy=self.posy[1]
            if self.img_index==3:
                self.img_posx=self.posx[1]
                self.img_posy=self.posy[1]

        if self.grid_size==1:
                self.img_posx=self.posx[0]
                self.img_posy=self.posy[0]

    def _get_items(self, update=False):
        #code from screensaver.picture.slideshow from ronie
        xbmc.log('slideshow type: %i' % self.slideshow_type)
	    # check if we have an image folder, else fallback to video fanart
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
        
        #choose which image
        self.path_index=0
        self.path_index_max=len(self.paths)-1
        #choose where to display this image
        self.img_count=0
        self.img_index_max=len(self.img_index_list)-1
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
            #the img_index_list is a shuffled list of the positions
            self.img_index=self.img_index_list[self.img_count]
            cur_img=self.img[self.img_index]
            self.positions()
            cur_img.setPosition(self.img_posx,self.img_posy)
            cur_img.setHeight(self.img_height)
            cur_img.setWidth(self.img_width)
            #If we don't want to use the cache
            #cur_img.setImage(picture_path,False)
            cur_img.setImage(self.picture_path)
            #have we changed all the different pictures ? if yes, reshuffle
            if self.img_count<self.img_index_max:
                self.img_count+=1
            else:
                self.img_count=0
                random.shuffle(self.img_index_list)

            xbmc.sleep(self.tempo)
            
    def exit(self):
        self.abort_requested = True
        xbmc.log("4 Screensaver: Exit requested")
        self.close()

if __name__ == "__main__":
    xbmc.log("1 Python Screensaver Started")
    screensaver_gui = Screensaver(
            "script-main.xml",
            __path__,
            "default",
        )
    screensaver_gui.doModal()
    xbmc.log("5 Python Screensaver Exited")
    del screensaver_gui
    sys.modules.clear()
