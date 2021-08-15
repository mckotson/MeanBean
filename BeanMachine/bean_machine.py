"""
bean_machine.py

Author: MCK

The classes and methods contained here contain the core 
of the MeanBean game, including movement, scoring, 
and bean field management.

Visualization of the bean field (self.display) must be 
handled by external methods.

The main class, BeanMachine, is designed to interface 
with openAI Gym environments.

Game Loop:
0 - Check for loss
1 - Set the new bean
2 - Horizontal movement and rotation
3 - Time increment
GO TO 2 or 4
4 - Drop and check for contact
5 - Post-contact dropping
6 - Check for completions
7 - Remove beans and update score
8 - Drop
"""

import numpy as np
import random, time

#bean_colors =  {0: np.array([255, 255, 255]),   # Nothing (blank space)
#                1: np.array([0, 0, 0]),         # Black
#                2: np.array([255, 0, 0]),       # Red
#                3: np.array([0, 0, 255]),       # Blue
#                4: np.array([200, 200, 0]),     # Yellow
#                5: np.array([0, 255, 0]),       # Green
#                6: np.array([255, 0, 255])}     # Purple
#
#def get_color(bean_int):
#    """
#    Given the integer corresponding to a bean type, return its RGB array.
#    """
#    return bean_colors[bean_int]

# Mapping used to track how orientation of controlled bean changes with rotation
orientation_dict = {'above':{-1:'left', 1:'right'},
                            'below':{-1:'right', 1:'left'},
                            'left':{-1:'below', 1:'above'},
                            'right':{-1:'above', 1:'below'}}

class BeanMachine():

    def __init__(self, seed: int=None, seconds_per_frame: float=0.1,
                    frames_per_drop: int=3):
        """
        Instantiation

        Args:
            seed (int, optional): Random seed to use. Defaults to None, 
                                    which will not seed the random generator.
            seconds_per_frame (float, optional): Seconds to pause during each frame 
                                    (NOT the exact framerate). Defaults to 0.1.
            frames_per_drop (int, optional): Number of frames to spend on the 
                                    animation when beans automatically drop. Defaults to 3.
        """

        # Prepare random seed
        self.seed = seed
        random.seed(self.seed)

        # Prepare framerate controls
        self.seconds_per_frame = seconds_per_frame
        self.frames_per_drop   = frames_per_drop

        # Set up playing field and game status trackers.
        self.field    = np.zeros((13, 6), dtype=int)
        self.score    = 0
        self.combo    = 0
        self.gameover = False

        # Set up and initialize display
        #self.display = 255*np.ones((13, 8, 3), dtype=int)

        # Gray out the right edge of the display (outside playing field)
        #self.display[:, -2:, :] = 100

        # Create the first controlled beans
        self.next2 = self.new_bean()
        self.next1 = self.new_bean()

        # Show the next beans at the top
        #self.display_next_beans()

        # Set up the game
        self.phase_map =   {0: self.check_loss,
                            1: self.next_bean,
                            2: self.movement,
                            3: self.timer,
                            4: self.drop,
                            5: self.postdrop,
                            6: self.completion_check,
                            7: self.remove_beans,
                            8: self.completion_drop}
        self.phase     = 1
        self.timesteps = 0

        # Create a container for the current action. See the movement method for options.
        self.action = 0

    def reset(self):
        """
        Reset the game, clearing the field and score.
        """
        self.field    = np.zeros((13, 6), dtype=int)
        self.score    = 0
        self.combo    = 0
        self.gameover = False

        # Create the first controlled beans
        self.next2 = self.new_bean()
        self.next1 = self.new_bean()

        self.phase     = 1
        self.timesteps = 0
        self.action    = 0

    def step(self):
        """
        Take the next gameplay step. To be called by OpenAI Gym environments.
        """
        if not self.gameover:
            phase = self.phase_map[self.phase]
            phase()

    def new_bean(self):
        """
        Randomly select a new bean color. (Does not include black)

        Returns:
            [int]: Integer corresponding to a bean color (see bean_colors dict).
        """
        return random.randint(2,6)

    def display_next_beans(self):
        """
        Display the next controllable bean on the right of the playing field.
        """
    #    r1, g1, b1 = get_color(self.next2)
    #    r2, g2, b2 = get_color(self.next1)
    #
    #    self.display[0, -1, 0] = r1
    #    self.display[0, -1, 1] = g1
    #    self.display[0, -1, 2] = b1
    #
    #    self.display[1, -1, 0] = r2
    #    self.display[1, -1, 1] = g2
    #    self.display[1, -1, 2] = b2

        self.timesteps = 0

    def check_loss(self):
        """
        Check if the Game Over state has been reached.
        """
        # Check if any beans are in top row
        topval = max(self.field[0, :])

        # Reset combo counter
        print(f"Score: {self.score} | Combo: {self.combo}")
        self.combo = 0

        if topval != 0:
            self.gameover = True

        self.phase += 1

    def bean_change(self, change_list):
        """
        Change the positions of beans on the field as they move 
        and update the display accordingly.

        Args:
            change_list (list[tuples]): List of changes to make.

        The change tuples are structured as (Y, X, C), where
            Y = y-coordinate of pixel to change
            X = x-coordinate of pixel to change
            C = New color (bean type) of pixel
        """
        while len(change_list) > 0:
            y, x, c = change_list.pop(0)
            self.field[y, x] = c
            #color = get_color(c)
            #self.display[y, x, :] = color

    def next_bean(self):
        """
        Add the next bean to the field and set the new next bean.
        """
        change_list = [(0, 3, self.next2), (1, 3, self.next1)]
        self.bean_change(change_list)

        self.orientation = 'above'  # Placement of Bean 2 rel. to Bean 1
        self.bean2     = [0, 3, self.next2]
        self.bean1    = [1, 3, self.next1]

        self.next2 = self.new_bean()
        self.next1 = self.new_bean()

        self.display_next_beans()
        self.phase += 1

    def movement(self):
        """
        Move the controllable bean according to the current action.

        Action | Effect
        0      | Do nothing (for OpenAI Gym)
        1      | Move bean left
        2      | Move bean right
        3      | Rotate counter-clockwise
        4      | Rotate clockwise
        5      | Drop the bean one space down
        """

        if self.action == 1:
            _ = self.move(-1)
        if self.action == 2:
            _ = self.move(1)
        
        if self.action == 3:
            _ = self.rotate(-1)
        if self.action == 4:
            _ = self.rotate(1)

        if self.action == 5:
            _ = self.hard_drop()

        # Reset action
        self.action = 0

        # Move to next phase
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

    def move(self, direction: int):
        """
        Move the controllable beans horizontally.

        Args:
            direction (int): 1 or -1 (right or left, respectively)

        Returns:
            [int]: 0 for failed movement (blocked by other beans or 
                    field boundaries). 1 for successful movement.
        """
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

    def rotate(self, direction: int):
        """
        Rotate the controllable beans.

        Bean 2 rotates around Bean 1. If there is a bean or wall where 
        Bean 2 would go, Bean 1 is pushed away from it. If Bean 1 cannot 
        be pushed away, the rotation fails.

        Args:
            direction (int): 1 or -1 (clockwise or counter)

        Returns:
            [int]: 0 for failed movement (blocked by other beans or 
                    field boundaries). 1 for successful movement.
        """

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
        """
        Move the controllable beans down one space, if the 
        space that the beans would occupy is free.

        Returns:
            [int]: 1 if the movement succeeds, otherwise 0.
        """
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

        # You get a point for hard dropping!
        self.score += 1

        return 1

    def timer(self):
        """
        Pause the game according to the specified framerate. If 
        beans are in the middle of automatically dropping, wait 
        the specified number of frames before moving them.
        """
        time.sleep(self.seconds_per_frame)
        self.timesteps += 1

        if self.timesteps == self.frames_per_drop:
            self.timesteps = 0
            self.phase += 1

        else:
            self.phase -= 1

    def drop(self):
        """
        Drop the controllable beans one space, if possible.
        """
        collision = self.hard_drop()

        if collision == 0:
            self.phase += 1
        else:
            self.phase = 2

    def dropcheck(self, bean):
        """
        Given a bean tuple (Y, X, color), check if it 
        can be dropped one space down without collision.

        Args:
            bean ([tuple]): (Y-coordinate, X-coordinate, Color) of bean.

        Returns:
            [bool]: False if the bean CAN drop, otherwise True.
        """
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

            time.sleep(self.seconds_per_frame)
            self.move_update(x1, y1, x2, y2)

        self.dropped_yx = [(y1, x1), (y2, x2)]

        self.phase += 1

    def completion_check(self):
        """
        Check for beans that have formed a group of 4 or 
        more neighbors.
        """

        # Create a list of beans to erase because they've formed complete groups
        self.eliminate = []

        # Take a snapshot of the playing field's current state
        self.snap = self.field.copy()

        # Check ONLY the beans that have just dropped to 
        # see if they have just formed a complete group.
        for y,x in self.dropped_yx:
            self.completion_single(x, y)

        self.dropped_yx = []    # Reset list of dropped beans
        self.phase += 1         # Move onto the next phase

    def completion_single(self, x, y):
        """
        Check a single bean to see if it is part of a complete group.

        Args:
            x ([int]): x-coordinate of bean
            y ([int]): y-coordinate of bean
        """
        c = self.snap[y,x]   # Snapshot of playing field before removing beans

        self.count  = 0     # Number of beans in group
        self.coords = []    # Coordinates of beans in group
        
        if c > 1:
            self.check_neighbors(x, y, c)

        if self.count >= 4:
            self.eliminate += self.coords
            self.combo     += 1

    def check_neighbors(self, x, y, c):
        """
        Check if the given bean has neighbors of the same color. This 
        method will recurse until it has found all connected beans 
        with the same color (a "group").

        Args:
            x ([int]): x-coordinate of bean
            y ([int]): y-coordinate of bean
            c ([int]): color of bean
        """
        c1 = 0
        c2 = 0
        c3 = 0
        c4 = 0

        # Set this bean's color in the snapshot to "Blank"
        # to prevent double-counting
        self.snap[y, x] = 0

        # Add this bean to the current group
        self.count += 1
        self.coords.append((y,x))

        # Check lower neighbor
        y1 = y-1
        if y1 >= 0:
            c1 = self.snap[y1, x]
            if c1 == c: self.check_neighbors(x, y1, c)
            if c1 == 1: self.check_neighbors(x, y1, -1)
        
        # Check upper neighbor
        y2 = y+1
        if y2 <= 12:
            c2 = self.snap[y2, x]
            if c2 == c: self.check_neighbors(x, y2, c)
            if c2 == 1: self.check_neighbors(x, y2, -1)

        # Check left neighbor
        x3 = x-1
        if x3 >= 0:
            c3 = self.snap[y, x3]
            if c3 == c: self.check_neighbors(x3, y, c)
            if c3 == 1: self.check_neighbors(x3, y, -1)

        # Check right neighbor
        x4 = x+1
        if x4 <= 5:
            c4 = self.snap[y, x4]
            if c4 == c: self.check_neighbors(x4, y, c)
            if c4 == 1: self.check_neighbors(x4, y, -1)

    def remove_beans(self):
        """
        Remove any beans that are part of a completed group, and 
        find any beans that need to drop because spaces beneath 
        them have opened up.
        """
        change_list   = []  # Spaces to change.
        self.droplist = {}  # Beans to drop.

        for (y,x) in self.eliminate:
            change = [y, x, 0]
            change_list.append(change)

            if x not in self.droplist:
                self.droplist[x] = [y,]
            else:
                self.droplist[x].append(y)

        self.score += self.combo*len(self.eliminate)

        self.bean_change(change_list)
        time.sleep(self.seconds_per_frame)

        self.phase += 1

    def completion_drop(self):
        """
        Drop any beans that have open spaces somewhere below them 
        after beans have been removed from the field.
        """
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
                    time.sleep(self.seconds_per_frame)

            # Now that new beans have dropped, check for completion again
            self.phase = 6