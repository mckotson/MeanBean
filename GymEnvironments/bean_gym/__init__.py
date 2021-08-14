from gym.envs.registration import register

register(
    id='BeanGym-v0',
    entry_point='bean_gym.envs:BeanGymEnv'
)