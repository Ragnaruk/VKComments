import unittest
from main.vkcomments import VKComments


class TestVKComments(unittest.TestCase):
    def test_get_ids_from_url__correct_person(self):
        obj = VKComments()

        self.assertEqual(
            ('123123', '456456'), obj.get_ids_from_url("https://vk.com/video123123_456456")
        )

    def test_get_ids_from_url__correct_group(self):
        obj = VKComments()

        self.assertEqual(
            ('-123123', '456456'), obj.get_ids_from_url("https://vk.com/video-123123_456456")
        )

    def test_get_ids_from_url__too_many_numbers(self):
        obj = VKComments()

        with self.assertRaises(ValueError):
            obj.get_ids_from_url("https://vk.com/video123123_456456_123456")

    def test_get_ids_from_url__not_enough_numbers(self):
        obj = VKComments()

        with self.assertRaises(ValueError):
            obj.get_ids_from_url("https://vk.com/video123123")


if __name__ == '__main__':
    unittest.main()
