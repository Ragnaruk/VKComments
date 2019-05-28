import unittest
from main.vkcomments import VKComments


class TestVKComments(unittest.TestCase):
    def test_get_ids_from_url__correct(self):
        obj = VKComments()

        self.assertEqual(
            ('1009205', '456239050'), obj.get_ids_from_url("https://vk.com/video1009205_456239050")
        )

    def test_get_ids_from_url__too_many_numbers(self):
        obj = VKComments()

        with self.assertRaises(ValueError):
            obj.get_ids_from_url("https://vk.com/video1009205_456239050_12345")

    def test_get_ids_from_url__not_enough_numbers(self):
        obj = VKComments()

        with self.assertRaises(ValueError):
            obj.get_ids_from_url("https://vk.com/video1009205")


if __name__ == '__main__':
    unittest.main()
