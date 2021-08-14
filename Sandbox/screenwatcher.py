import numpy as np
from PIL import ImageGrab
import cv2, win32gui, time, win32com.client

import matplotlib.pyplot as plt

winlist = []

# Bean window is 6 beans across by 12 beans across
bean_minx = 35
bean_maxx = 225
bean_miny = 80
bean_maxy = 488
bean_numx = 6
bean_numy = 12

# A single bean is roughly 30 px wide and 34 px tall
bean_width  = 32
bean_height = 35

def enum_cb(hwnd, results):
    winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    
def get_screens(screen_name):
    # wait for the program to start initially.
    win32gui.EnumWindows(enum_cb, winlist)
    screens = [(hwnd, title) for hwnd, title in winlist if screen_name in title.lower()]
    while len(screens) == 0:
        screens = [(hwnd, title) for hwnd, title in winlist if screen_name in title.lower()]
        win32gui.EnumWindows(enum_cb, winlist)

    return screens

keyword = 'robotnik'
screens = get_screens(keyword)

window = screens[0][0]
bbox   = win32gui.GetWindowRect(window)

def screen_watcher():
    t0 = time.time()

    while True:
        dt = time.time() - t0
        t0 = time.time()

        curr_screen = np.array(ImageGrab.grab(bbox=bbox))

        bean_screen = curr_screen[bean_miny:bean_maxy, bean_minx:bean_maxx]

        cv2.imshow('window',cv2.cvtColor(bean_screen, cv2.COLOR_BGR2RGB))
        cv2.waitKey(1)

        for m in range(bean_numy):
            y1 = m*bean_height
            y2 = y1+bean_height

            for n in range(bean_numx):
                x1 = n*bean_width
                x2 = x1+bean_width

                cell   = bean_screen[y1:y2, x1:x2]
                maxval = np.max(cell)

                # Beans' eyes are white, so use that to detect them
                if maxval > 200:
                    r = np.mean(cell[:,:,0])
                    g = np.mean(cell[:,:,1])
                    b = np.mean(cell[:,:,2])

                    color = 'dunno!'
                    if r > 80:
                        if g < 75:
                            color = 'red'
                        else:
                            color = 'yellow'
                    
                    elif b > 70:
                        if g > 50:
                            color = 'blue'
                        else:
                            color = 'purple'

                    elif g > 75:
                        color = 'green'

                    else:
                        color = 'black'

                    #print(m+1, n+1, color, r, g, b)




        print(dt)

if __name__ == '__main__':
    screen_watcher()