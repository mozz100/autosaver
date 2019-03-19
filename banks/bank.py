import json
import os
import uuid
from abc import ABCMeta, abstractmethod


class Bank(metaclass=ABCMeta):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_balance(self):  # pragma: no cover
        pass

    @abstractmethod
    def get_goal_data(self):  # pragma: no cover
        pass

    @abstractmethod
    def save_goal(self, data):  # pragma: no cover
        pass

    def get_unique_str(self):
        return str(uuid.uuid4())
