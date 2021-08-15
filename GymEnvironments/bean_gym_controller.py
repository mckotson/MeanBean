"""
bean_gym_controller.py

Author: MCK

Human-usable controller for playing MeanBean via the Gym environment.
"""

import sys, gym, time
from gym import wrappers
import bean_gym

env  = gym.make('BeanGym-v0')
mode = 'human'

if mode == 'rgb_array':
    env = wrappers.Monitor(env, './DataProducts/Videos/', force=True)

env._max_episode_steps = 10000   # Max steps before env returns done=True

# Action being taken by human
human_agent_action = 0

# Pause and restart controls
human_wants_restart = False
human_sets_pause    = False

def key_press(key, mod):
    # Check for key press and apply the appropriate actions
    global human_agent_action, human_sets_pause, human_wants_restart

    # TEMPORARY
    print(f'Key pressed: {key}')

    if key==0xff0d: human_wants_restart = True   # Enter key
    if key==32: human_sets_pause = True   # Space bar

    if key==65361: human_agent_action = 1   # Left arrow key
    if key==65363: human_agent_action = 2   # Right arrow key
    if key==65364: human_agent_action = 5   # Down arrow key

    print(f'Action: {human_agent_action}')

def key_release(key, mod):
    global human_agent_action, human_sets_pause, human_wants_restart
    if key in [65361, 65363, 65364]: human_agent_action = 0

# Set up Gym environment and interactions
env.reset()
env.render(mode=mode)
env.unwrapped.viewer.window.on_key_press   = key_press
env.unwrapped.viewer.window.on_key_release = key_release

def rollout(env):
    global human_agent_action, human_sets_pause, human_wants_restart
    human_wants_restart = False
    env.reset()

    total_reward = 0
    total_steps  = 0

    while True:
        total_steps += 1

        obser, r, done, info = env.step(human_agent_action)

        total_reward += r

        window_still_open = env.render(mode=mode)

        if mode == 'rgb_array':
            window_still_open = True

        if window_still_open == False: return False

        if done or human_wants_restart:
            human_agent_action = 0
            break

        while human_sets_pause:
            env.render(mode=mode)

    print(f"Timesteps: {total_steps}\nReward: {total_reward}")

while 1:
    window_still_open = rollout(env)
    if window_still_open == False:
        env.close()
        break