import unittest
import pyautogui

class TestEscKey(unittest.TestCase):
    def test_press_esc(self):
        """测试发送 ESC 键"""
        pyautogui.press('esc')
        # 如果没有异常，则测试通过
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()