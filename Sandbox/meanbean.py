import numpy as np
import matplotlib.pyplot as plt
from random import randint
from pynput import keyboard
import time

seconds_per_frame = 0.1
frames_per_drop   = 3

# Bean Colors:
#
# nothing = 0
# black   = 1
# red     = 2
# blue    = 3
# yellow  = 4
# green   = 5
# purple  = 6

# Game Loop:
#
# 0 - Check for loss
# 1 - Set the new bean
# 2 - Horizontal movement and rotation
# 3 - Time increment
# GO TO 2 or 4
# 4 - Drop and check for contact
# 5 - Post-contact dropping
# 6 - Check for completions
# 7 - Remove beans and update score
# 8 - Drop
# GO TO 6 or 0

num_phases = 10

def new_bean():
    return randint(2,6)

bean_colors =  {0: np.array([255, 255, 255]),
                1: np.array([0, 0, 0]),
                2: np.array([255, 0, 0]),
                3: np.array([0, 0, 255]),
                4: np.array([255, 255, 0]),
                5: np.array([0, 255, 0]),
                6: np.array([255, 0, 255])}

orientation_dict = {'above':{-1:'left', 1:'right'},
                            'below':{-1:'right', 1:'left'},
                            'left':{-1:'below', 1:'above'},
                            'right':{-1:'above', 1:'below'}}

def get_color(bean_int):
    """
    Given the integer corresponding to a bean type, return its RGB array.
    """
    return bean_colors[bean_int]

class Machine():

    def __init__(self):

        self.field    = np.zeros((13, 6), dtype=int)
        self.score    = 0
        self.combo    = 0
        self.gameover = False

        self.next2 = new_bean()
        self.next1 = new_bean()

        # Set up and initialize display
        self.display = 255*np.ones((13, 8, 3), dtype=int)

        # Gray out the right and top edges of the display
        self.display[:, -2:, :] = 100
        self.display[0, :, :]   = 100

        # Show the next beans at the top
        self.display_next_beans()

        self.fig = plt.figure()
        self.img = plt.imshow(self.display)
        plt.ion()
        plt.show()

        # Set up the game
        self.phase_map =   {0: self.check_loss,
                            1: self.new_bean,
                            2: self.movement,
                            3: self.timer,
                            4: self.drop,
                            5: self.postdrop,
                            6: self.completion_check,
                            7: self.remove_beans,
                            8: self.completion_drop}
        self.phase     = 1
        self.timesteps = 0

        self.pressed_key = ''

        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        self.pressed_key = key.char

    def display_next_beans(self):
        r1, g1, b1 = get_color(self.next2)
        r2, g2, b2 = get_color(self.next1)

        self.display[0, -1, 0] = r1
        self.display[0, -1, 1] = g1
        self.display[0, -1, 2] = b1

        self.display[1, -1, 0] = r2
        self.display[1, -1, 1] = g2
        self.display[1, -1, 2] = b2

        self.timesteps = 0

    def update_display(self):
        self.img.set_data(self.display)
        plt.draw()
        plt.pause(0.001)

    def play(self):
        while not self.gameover:
            phase = self.phase_map[self.phase]
            phase()

    def check_loss(self):
        # Check if any beans are in top row
        topval = max(self.field[0, :])

        # Reset combo counter
        print(f"Score: {self.score} | Combo: {self.combo}")
        self.combo = 0

        if topval != 0:
            self.gameover = True

        self.phase += 1

    def bean_change(self, change_list):
        while len(change_list) > 0:
            y, x, c = change_list.pop(0)
            self.field[y, x] = c
            color = get_color(c)
            self.display[y, x, :] = color

    def new_bean(self):
        # Add the next bean to the field and set the new next bean
        change_list = [(0, 3, self.next2), (1, 3, self.next1)]
        self.bean_change(change_list)

        self.orientation = 'above'  # Placement of Bean 2 rel. to Bean 1
        self.bean2     = [0, 3, self.next2]
        self.bean1    = [1, 3, self.next1]

        self.next2 = new_bean()
        self.next1 = new_bean()

        self.display_next_beans()
        self.update_display()
        self.phase += 1

    def movement(self):

        # asd for movement, k to rotate counter, l to rotate clockwise

        if self.pressed_key == 'a':
            _ = self.move(-1)
        if self.pressed_key == 'd':
            _ = self.move(1)

        if self.pressed_key == 'k':
            _ = self.rotate(-1)

        if self.pressed_key == 'l':
            _ = self.rotate(1)

        if self.pressed_key == 'w':
            _ = self.hard_drop()

        self.pressed_key = ''

        self.update_display()
        self.phase += 1

    def move_update(self, x1, y1, x2, y2):
        """
        Update the field and display when the controlled beans
        move to positions (x1,y1) and (x2,y2).
        """
        # Clear old pixels
        change_1 = [self.bean1[0], self.bean1[1], 0]
        change_2 = [self.bean2[0], self.bean2[1], 0]
        # Change new pixels
        change_3 = [y2, x2, self.bean2[2]]
        change_4 = [y1, x1, self.bean1[2]]
        change_list = [change_1, change_2, change_3, change_4]
        self.bean_change(change_list)

        self.bean2[1] = x2
        self.bean2[0] = y2
        self.bean1[1] = x1
        self.bean1[0] = y1


    def move(self, direction):
        # See what the hypothetical new coordinates would be
        y2 = self.bean2[0]
        x2 = self.bean2[1]+direction
        y1 = self.bean1[0]
        x1 = self.bean1[1]+direction

        if min([x1, x2]) < 0:
            return 0

        if max([x1, x2]) > 5:
            return 0

        if y1==y2:
            x = direction*max([direction*x1, direction*x2])
            if self.field[y1, x] > 0:
                return 0
        else:
            if self.field[y1, x1] > 0:
                return 0
            if self.field[y2, x2] > 0:
                return 0

        self.move_update(x1, y1, x2, y2)

        return 1

    def rotate(self, direction):
        # Bean 2 rotates around Bean 1.
        # If there is a bean or wall where Bean 2 would go, 
        # Bean 1 is pushed away from it.
        # If Bean 1 cannot be pushed away, the rotation fails.

        y1 = self.bean1[0]
        x1 = self.bean1[1]

        if self.orientation == 'above':
            y2 = self.bean2[0]+1
            x2 = self.bean2[1]+direction
            y1m = self.bean1[0]
            x1m = self.bean1[1]-direction
        if self.orientation == 'below':
            y2 = self.bean2[0]-1
            x2 = self.bean2[1]-direction
            y1m = self.bean1[0]
            x1m = self.bean1[1]+direction
        if self.orientation == 'left':
            y2 = self.bean2[0]-direction
            x2 = self.bean2[1]+1
            y1m = self.bean1[0]+direction
            x1m = self.bean1[1]
        if self.orientation == 'right':
            y2 = self.bean2[0]+direction
            x2 = self.bean2[1]-1
            y1m = self.bean1[0]-direction
            x1m = self.bean1[1]

        # Check for collision on Bean 2
        if (x2 < 0) or (x2 > 5) or (y2 < 0) or (y2 > 12) or (self.field[y2,x2] > 0):
            # Check if Bean 1 can move away
            if self.field[y1m, x1m] > 0:
                return 0
            else:
                x2 = x1
                y2 = y1
                y1 = y1m
                x1 = x1m 

        self.move_update(x1, y1, x2, y2)

        self.orientation = orientation_dict[self.orientation][direction]

        return 1

    def hard_drop(self):
        y2 = self.bean2[0]+1
        x2 = self.bean2[1]
        y1 = self.bean1[0]+1
        x1 = self.bean1[1]

        if max([y1, y2]) > 12:
            return 0

        if x1 == x2:
            y = max([y1, y2])
            if self.field[y, x1] > 0:
                return 0
        else:
            if (self.field[y1,x1] > 0) or (self.field[y2,x2] > 0):
                return 0

        self.move_update(x1, y1, x2, y2)

        return 1

    def timer(self):
        time.sleep(seconds_per_frame)
        self.timesteps += 1

        if self.timesteps == frames_per_drop:
            self.timesteps = 0
            self.phase += 1

        else:
            self.phase -= 1

    def drop(self):
        collision = self.hard_drop()

        self.update_display()

        if collision == 0:
            self.phase += 1
        else:
            self.phase = 2

    def dropcheck(self, bean):
        y = bean[0]
        x = bean[1]
        return ((y+1)>12) or (self.field[y+1,x]>0)

    def postdrop(self):
        """
        Move any hanging beans down one space at a time.
        """
        flag1 = True
        flag2 = True

        x1 = self.bean1[1]
        x2 = self.bean2[1]
        y1 = self.bean1[0]
        y2 = self.bean2[0]

        while flag1 or flag2:
            if flag1 and not self.dropcheck(self.bean1):
                y1 += 1
            else:
                flag1 = False

            if flag2 and not self.dropcheck(self.bean2):
                y2 += 1
            else:
                flag2 = False

            time.sleep(seconds_per_frame)
            self.move_update(x1, y1, x2, y2)
            self.update_display()

        self.dropped_yx = [(y1, x1), (y2, x2)]

        self.phase += 1

    def check_neighbors(self, x, y, c):
        c1 = 0
        c2 = 0
        c3 = 0
        c4 = 0

        self.snap[y, x] = 0
        self.count += 1
        self.coords.append((y,x))

        y1 = y-1
        if y1 >= 0:
            c1 = self.snap[y1, x]
            if c1 == c: self.check_neighbors(x, y1, c)
            if c1 == 1: self.check_neighbors(x, y1, -1)
        
        y2 = y+1
        if y2 <= 12:
            c2 = self.snap[y2, x]
            if c2 == c: self.check_neighbors(x, y2, c)
            if c2 == 1: self.check_neighbors(x, y2, -1)

        x3 = x-1
        if x3 >= 0:
            c3 = self.snap[y, x3]
            if c3 == c: self.check_neighbors(x3, y, c)
            if c3 == 1: self.check_neighbors(x3, y, -1)

        x4 = x+1
        if x4 <= 5:
            c4 = self.snap[y, x4]
            if c4 == c: self.check_neighbors(x4, y, c)
            if c4 == 1: self.check_neighbors(x4, y, -1)

    def completion_single(self, x, y):
        c = self.snap[y,x]

        self.count  = 0
        self.coords = []
        
        if c > 1:
            self.check_neighbors(x, y, c)

        if self.count >= 4:
            self.eliminate += self.coords
            self.combo     += 1
            
    def completion_check(self):
        self.eliminate = []

        self.snap = self.field.copy()

        for y,x in self.dropped_yx:
            self.completion_single(x, y)

        self.dropped_yx = []
        self.phase += 1

    def remove_beans(self):
        change_list   = []
        orig_list     = []
        self.droplist = {}
        for (y,x) in self.eliminate:
            c = self.field[y,x]
            change = [y, x, 0]
            change_list.append(change)
            orig   = [y, x, c]
            orig_list.append(change)

            if x not in self.droplist:
                self.droplist[x] = [y,]
            else:
                self.droplist[x].append(y)

        self.score += self.combo*len(self.eliminate)

        self.bean_change(change_list)
        self.update_display()
        time.sleep(seconds_per_frame)
        self.bean_change(orig_list)
        self.update_display()
        time.sleep(seconds_per_frame)
        self.bean_change(change_list)
        self.update_display()
        time.sleep(seconds_per_frame)

        self.phase += 1

    def completion_drop(self):
        if len(self.droplist) == 0:
            self.phase = 0

        else:
            columns = list(self.droplist.keys())
            for column in columns:
                self.droplist[column] = sorted(self.droplist[column])

            while len(self.droplist) > 0:
                # Find all beans that need to drop at least one space
                droppers = []
                for column in columns:
                    if column not in self.droplist:
                        continue
                    
                    hi_row = self.droplist[column].pop(0)

                    for row in range(0, hi_row):
                        c = self.field[row, column]

                        if c != 0:
                            droppers.append((row, column, c))

                    if len(self.droplist[column]) == 0:
                        _ = self.droplist.pop(column)

                # Drop those beans one space
                change_list = []
                for y,x,c in droppers[::-1]:   # Drop beans from bottom to top

                    change_1 = [y, x, 0]
                    change_2 = [y+1, x, c]
                    change_list.append(change_1)
                    change_list.append(change_2)
                    self.dropped_yx.append([y+1, x])

                if len(change_list) > 0:
                    self.bean_change(change_list)
                    self.update_display()
                    time.sleep(seconds_per_frame)

            # Now that new beans have dropped, check for completion again
            self.phase = 6

if __name__ == '__main__':

    machine = Machine()
    machine.play()