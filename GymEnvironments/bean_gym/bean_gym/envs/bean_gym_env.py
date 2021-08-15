"""
bean_gym_env.py

Author: MCK

This is the OpenAI Gym interface for the MeanBean game.
"""

import gym
from gym import spaces, logger
from gym.utils import seeding

from bean_machine import BeanMachine

bean_colors =  {0: (1., 1., 1.),    # Nothing (blank space)
                1: (0., 0., 0.),    # Black
                2: (1., 0., 0.),    # Red
                3: (0., 0., 1.),    # Blue
                4: (0.8, 0.8, 0.),  # Yellow
                5: (0., 1., 0.),    # Green
                6: (1., 0., 1.)}    # Purple

class BeanGymEnv(gym.Env):
    """
    OpenAI Gym environment for the MeanBean game.

    Observation:
        TBD

    Actions:
        Type: Discrete(6)
        Num  Action
        0    Do Nothing
        1    Move beans left
        2    Move beans right
        3    Rotate beans counter-clockwise
        4    Rotate beans clockwise
        5    Drop beans down one space

    Rewards:
        - A reward of 1 is given for every step taken.
        - A reward of 1 is given for every hard drop.
        - Upon erasing beans, a reward is calculated 
        based on the number of beans erased and a combo
        multiplier

    Starting State:
        There are no beans on the playing field, and 
        a random pair of controllable beans is generated.

    Episode Termination:
        A bean is placed on the top row (Game Over).
    """

    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 50
    }

    def __init__(self):

        seed = self.seed()

        # TEMPORARY HARD-CODED INPUT VALUES
        self.BeanMachine = BeanMachine(seed=seed[0], seconds_per_frame=0.1,
                                        frames_per_drop=3)

        # Set up action and observation spaces
        self.action_space      = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=0, high=6, shape=(13, 6), dtype=int)

        self.viewer = None
        self.state  = None

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        err_msg = "%r (%s) invalid" % (action, type(action))
        assert self.action_space.contains(action), err_msg

        reward = 0

        score_before = self.BeanMachine.score

        self.BeanMachine.action = action
        self.BeanMachine.step()
        self.BeanMachine.action = 0   # Reset action

        score_after = self.BeanMachine.score
        reward += score_after - score_before

        self.state = self.BeanMachine.field

        done = self.BeanMachine.gameover

        reward += (not done)   # +0 if Game Over, else +1

        return self.state, reward, done, {}

    def reset(self):
        self.BeanMachine.reset()
        self.state = self.BeanMachine.field

        return self.state

    def render(self, mode='human'):
        # Field is 6x13 (For now, 'next beans' are invisible)
        world_width   = 6
        world_height  = 13
        scale         = 50
        screen_width  = world_width*scale
        screen_height = world_height*scale

        if self.viewer is None:
            from gym.envs.classic_control import rendering
            self.viewer = rendering.Viewer(screen_width, screen_height)

            # Set up the 6x13 grid of squares that will make our playing field
            self.blocks = []

            for x in range(6):
                self.blocks.append([])
                for y in range(13):
                    l = x*scale
                    r = (x+1)*scale
                    b = 13*scale - (y+1)*scale
                    t = 13*scale - y*scale

                    block = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])

                    self.viewer.add_geom(block)
                    self.blocks[x].append(block)

        if self.state is None:
            return None

        # Color each block according to its field value
        for x in range(6):
            for y in range(13):
                c = self.state[y,x]   # Color index

                red,green,blue = bean_colors[c]

                self.blocks[x][y].set_color(red, green, blue)

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None