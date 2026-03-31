import re

from ok import BaseTask

class MyBaseTask(BaseTask):
    # 参考分辨率，用于坐标缩放
    REF_RESOLUTION = (1920, 1080)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def operate(self, func):
        self.executor.interaction.operate(func, block=True)

    def do_mouse_down(self, key):
        self.executor.interaction.do_mouse_down(key=key)

    def do_mouse_up(self, key):
        self.executor.interaction.do_mouse_up(key=key)

    def do_send_key_down(self, key):
        self.executor.interaction.do_send_key_down(key)

    def do_send_key_up(self, key):
        self.executor.interaction.do_send_key_up(key)

    def _get_scaled_coordinates(self, ref_x, ref_y):
        """
        将参考分辨率(1920x1080)的坐标缩放到当前游戏窗口的实际分辨率。
        如果无法获取当前帧，则返回原始坐标。
        """
        frame = self.frame
        if frame is None:
            return ref_x, ref_y
        height, width = frame.shape[:2]
        scale_x = width / self.REF_RESOLUTION[0]
        scale_y = height / self.REF_RESOLUTION[1]
        return int(ref_x * scale_x), int(ref_y * scale_y)