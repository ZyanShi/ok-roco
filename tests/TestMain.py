import unittest

class SimpleMathTest(unittest.TestCase):
    def test_one_plus_one(self):
        result = 1 + 1
        self.assertEqual(result, 2)
        print("1 + 1 = 2，测试成功")

if __name__ == '__main__':
    unittest.main()