"""Deep Deterministic Policy Gradient (DDPG).

From https://raw.githubusercontent.com/cmu-db/ottertune/master/server/analysis/ddpg/ddpg.py with additional comments.
"""

import pickle

import numpy as np
import torch
torch.set_num_threads(1)
import torch.nn as nn
import torch.optim as optimizer

from torch.autograd import Variable

from cybernetics.tuning.ddpg.prioritized_replay_memory import PrioritizedReplayMemory


class Actor(nn.Module):
    """
    Policy network.
    """
    def __init__(self, n_states: int, n_actions: int, hidden_sizes: list, use_default: bool):
        super(Actor, self).__init__()

        if use_default:
            self.layers = nn.Sequential(
                nn.Linear(n_states, 128),
                nn.LeakyReLU(negative_slope=0.2),
                nn.BatchNorm1d(hidden_sizes[0]),
                nn.Linear(128, 128),
                nn.Tanh(),
                nn.Dropout(0.3),
                nn.Linear(128, 128),
                nn.Tanh(),
                nn.Linear(128, 64),
                nn.Linear(64, n_actions)
            )
        else:
            self.layers = nn.Sequential(
                nn.Linear(n_states, hidden_sizes[0]),
                nn.LeakyReLU(negative_slope=0.2),
                nn.BatchNorm1d(hidden_sizes[0]),
                nn.Linear(hidden_sizes[0], hidden_sizes[1]),
                nn.Tanh(),
                nn.Dropout(0.3),
                nn.BatchNorm1d(hidden_sizes[1]),
                nn.Linear(hidden_sizes[1], hidden_sizes[2]),
                nn.Tanh(),
                nn.Dropout(0.3),
                nn.BatchNorm1d(hidden_sizes[2]),
                nn.Linear(hidden_sizes[2], n_actions)
            )

        # This act layer maps the output to (0, 1)
        self.sigmoid = nn.Sigmoid()
        self._init_weights()

    def _init_weights(self):
        for m in self.layers:
            if isinstance(m, nn.Linear):
                m.weight.data.normal_(0.0, 1e-2)
                m.bias.data.uniform_(-0.1, 0.1)

    def forward(self, states): # pylint: disable=arguments-differ
        print(states.shape)
        actions = self.sigmoid(self.layers(states))
        return actions


class Critic(nn.Module):
    """
    Q-function network.
    """
    def __init__(self, n_states: int, n_actions: int, hidden_sizes: list, use_default: bool):
        super(Critic, self).__init__()

        if use_default:
            self.state_input = nn.Linear(n_states, 128)
            self.action_input = nn.Linear(n_actions, 128)
            self.layers = nn.Sequential(
                nn.Linear(256, 256),
                nn.LeakyReLU(negative_slope=0.2),
                nn.BatchNorm1d(256),
                nn.Linear(256, 256),
                nn.Linear(256, 64),
                nn.Tanh(),
                nn.Dropout(0.3),
                nn.BatchNorm1d(64),
                nn.Linear(64, 1)
            )
        else:
            self.state_input = nn.Linear(n_states, hidden_sizes[0])
            self.action_input = nn.Linear(n_actions, hidden_sizes[0])
            self.layers = nn.Sequential(
                nn.Linear(hidden_sizes[0] * 2, hidden_sizes[1]),
                nn.LeakyReLU(negative_slope=0.2),
                nn.Dropout(0.3),
                nn.BatchNorm1d(hidden_sizes[1]),
                nn.Linear(hidden_sizes[1], hidden_sizes[2]),
                nn.Tanh(),
                nn.Dropout(0.3),
                nn.BatchNorm1d(hidden_sizes[2]),
                nn.Linear(hidden_sizes[2], 1)
            )

        self.tanh = nn.Tanh()
        self._init_weights()

    def _init_weights(self):
        self.state_input.weight.data.normal_(0.0, 1e-2)
        self.state_input.bias.data.uniform_(-0.1, 0.1)

        self.action_input.weight.data.normal_(0.0, 1e-2)
        self.action_input.bias.data.uniform_(-0.1, 0.1)

        for m in self.layers:
            if isinstance(m, nn.Linear):
                m.weight.data.normal_(0.0, 1e-2)
                m.bias.data.uniform_(-0.1, 0.1)

    def forward(self, states, actions): # pylint: disable=arguments-differ
        states = self.tanh(self.state_input(states))
        actions = self.tanh(self.action_input(actions))

        _input = torch.cat([states, actions], dim=1)
        value = self.layers(_input)
        return value


class OUProcess:
    """
    To make DDPG policies explore better, add noise to their actions at training time. The authors of the original DDPG paper recommended time-correlated OU noise.
    """
    def __init__(self, n_actions: int, theta: float=0.15, mu: float=0, sigma: float=0.1):
        self.n_actions = n_actions
        self.theta = theta
        self.mu = mu
        self.sigma = sigma
        self.current_value = np.ones(self.n_actions) * self.mu

    def reset(self, sigma: float=0, theta: float=0):
        self.current_value = np.ones(self.n_actions) * self.mu
        if sigma != 0:
            self.sigma = sigma
        if theta != 0:
            self.theta = theta

    def noise(self):
        x = self.current_value
        dx = self.theta * (self.mu - x) + self.sigma * np.random.randn(len(x))
        self.current_value = x + dx
        return self.current_value


class DDPG(object):
    """
    DDPG algorithm.
    """
    def __init__(self, n_states: int, n_actions: int, model_name: str="",
                 alr: float=0.001, clr: float=0.001, gamma:float=0.9,
                 batch_size: int=32, tau: float=0.002,
                 shift: float=0, memory_size: int=100000,
                 a_hidden_sizes: list=[128, 128, 64],
                 c_hidden_sizes: list=[128, 256, 64],
                 use_default: bool=False):
        self.n_states = n_states
        self.n_actions = n_actions
        self.alr = alr
        self.clr = clr
        self.model_name = model_name
        self.batch_size = batch_size
        self.gamma = gamma
        self.tau = tau
        self.a_hidden_sizes = a_hidden_sizes
        self.c_hidden_sizes = c_hidden_sizes
        self.shift = shift
        self.use_default = use_default

        self._build_network()

        self.replay_memory = PrioritizedReplayMemory(capacity=memory_size)
        self.noise = OUProcess(n_actions)

    @staticmethod
    def totensor(x):
        return torch.tensor(x, dtype=torch.float, requires_grad=True)

    def _build_network(self):
        self.actor = Actor(self.n_states, self.n_actions, self.a_hidden_sizes,
                           self.use_default)
        self.target_actor = Actor(self.n_states, self.n_actions,
                                  self.a_hidden_sizes, self.use_default)
        self.critic = Critic(self.n_states, self.n_actions,
                             self.c_hidden_sizes, self.use_default)
        self.target_critic = Critic(self.n_states, self.n_actions,
                                    self.c_hidden_sizes, self.use_default)

        # Copy actor"s parameters
        self._update_target(self.target_actor, self.actor, tau=1.0)

        # Copy critic"s parameters
        self._update_target(self.target_critic, self.critic, tau=1.0)

        self.loss_criterion = nn.MSELoss()
        self.actor_optimizer = optimizer.Adam(lr=self.alr,
                                              params=self.actor.parameters(),
                                              weight_decay=1e-5)
        self.critic_optimizer = optimizer.Adam(lr=self.clr,
                                               params=self.critic.parameters(),
                                               weight_decay=1e-5)

    @staticmethod
    def _update_target(target, source, tau):
        for (target_param, param) in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                target_param.data * (1 - tau) + param.data * tau
            )

    def reset(self, sigma, theta):
        self.noise.reset(sigma, theta)

    def _sample_batch(self):
        batch, idx = self.replay_memory.sample(self.batch_size)
        states = list(map(lambda x: x[0].tolist(), batch)) # pylint: disable=W0141
        actions = list(map(lambda x: x[1].tolist(), batch)) # pylint: disable=W0141
        rewards = list(map(lambda x: x[2], batch)) # pylint: disable=W0141
        next_states = list(map(lambda x: x[3].tolist(), batch)) # pylint: disable=W0141

        return idx, states, next_states, actions, rewards

    def add_sample(self, state, action, reward, next_state):
        self.critic.eval()
        self.actor.eval()
        self.target_critic.eval()
        self.target_actor.eval()
        
        batch_state = self.totensor(np.expand_dims(state, axis=0))
        batch_next_state = self.totensor(np.expand_dims(next_state, axis=0))
        current_value = self.critic(
            batch_state,
            self.totensor(np.expand_dims(action, axis=0))
        )
        target_action = self.target_actor(batch_next_state)
        target_value = self.totensor([reward]) + \
            self.target_critic(batch_next_state, target_action) * self.gamma
        error = float(torch.abs(current_value - target_value).data.numpy()[0])

        self.target_actor.train()
        self.actor.train()
        self.critic.train()
        self.target_critic.train()
        self.replay_memory.add(error, (state, action, reward, next_state))

    def update(self):
        idxs, states, next_states, actions, rewards = self._sample_batch()
        batch_states = self.totensor(states)
        batch_next_states = self.totensor(next_states)
        batch_actions = self.totensor(actions)
        batch_rewards = self.totensor(rewards)

        target_next_actions = self.target_actor(batch_next_states).detach()
        target_next_value = self.target_critic(batch_next_states, target_next_actions).detach()
        current_value = self.critic(batch_states, batch_actions)
        batch_rewards = batch_rewards[:, None]
        next_value = batch_rewards + target_next_value * self.gamma + self.shift

        # update prioritized memory
        if isinstance(self.replay_memory, PrioritizedReplayMemory):
            error = torch.abs(current_value - next_value).data.numpy()
            for i in range(self.batch_size):
                idx = idxs[i]
                self.replay_memory.update(idx, error[i][0])

        # Update Critic
        loss = self.loss_criterion(current_value, next_value)
        self.critic_optimizer.zero_grad()
        loss.backward()
        self.critic_optimizer.step()

        # Update Actor
        self.critic.eval()
        policy_loss = -self.critic(batch_states, self.actor(batch_states))
        policy_loss = policy_loss.mean()
        self.actor_optimizer.zero_grad()
        policy_loss.backward()

        self.actor_optimizer.step()
        self.critic.train()

        self._update_target(self.target_critic, self.critic, tau=self.tau)
        self._update_target(self.target_actor, self.actor, tau=self.tau)

        return loss.data, policy_loss.data

    def choose_action(self, states):
        self.actor.eval()
        act = self.actor(self.totensor(
            np.expand_dims(states, axis=0))).squeeze(0)
        self.actor.train()
        action = act.data.numpy()
        action += self.noise.noise()
        return action.clip(0, 1)

    def set_model(self, actor_dict, critic_dict):
        self.actor.load_state_dict(pickle.loads(actor_dict))
        self.critic.load_state_dict(pickle.loads(critic_dict))

    def get_model(self):
        return pickle.dumps(self.actor.state_dict()), pickle.dumps(self.critic.state_dict())
