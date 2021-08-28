from abc import ABCMeta, abstractmethod


class IReplay:

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_play_data(self):
        raise NotImplementedError


    @abstractmethod
    def get_time_data(self):
        raise NotImplementedError


    @abstractmethod
    def get_press_data(self):
        raise NotImplementedError

    
    @abstractmethod
    def get_xpos_data(self):
        raise NotImplementedError


    @abstractmethod
    def get_ypos_data(self):
        raise NotImplementedError


    @abstractmethod
    def get_mania_keys(self):
        raise NotImplementedError