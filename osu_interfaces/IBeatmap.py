from abc import ABCMeta, abstractmethod


class IBeatmap:

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_diff_data(self):
        raise NotImplementedError


    @abstractmethod
    def get_hitobjects(self):
        raise NotImplementedError