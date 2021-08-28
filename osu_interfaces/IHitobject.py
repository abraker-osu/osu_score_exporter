from abc import ABCMeta, abstractmethod


class IHitobject:

    __metaclass__ = ABCMeta

    CIRCLE  = 1 << 0
    SLIDER  = 1 << 1
    NCOMBO  = 1 << 2
    SPINNER = 1 << 3
    # ???
    MANIALONG = 1 << 7

    @abstractmethod
    def pos_x(self):
        raise NotImplementedError


    @abstractmethod
    def pos_y(self):
        raise NotImplementedError


    @abstractmethod
    def start_time(self):
        raise NotImplementedError


    @abstractmethod
    def end_time(self):
        raise NotImplementedError