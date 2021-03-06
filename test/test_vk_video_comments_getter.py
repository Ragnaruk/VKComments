import os
import unittest

from vk.exceptions import VkAuthError

from src.vk_video_comments_getter import VKVideoCommentsGetter, URLParserError


class TestVKVideoCommentsGetter(unittest.TestCase):
    # Launching before every test
    def setUp(self):
        self.obj = VKVideoCommentsGetter()
        self.obj.load_default_config()

        # Removing all files
        self.obj.remove_config_file()
        self.obj.remove_comments_file()
        self.obj.remove_log_file()

    # Launching after every test
    def tearDown(self):
        # Removing all files
        self.obj.remove_config_file()
        self.obj.remove_comments_file()
        self.obj.remove_log_file()
    
    def test__get_ids_from_url__correct_person(self):
        self.assertEqual(
            ('123123', '456456'), 
            self.obj.get_ids_from_url("https://vk.com/video123123_456456"),
            msg="Видео выложено от имени человека."
        )

    def test__get_ids_from_url__correct_group(self):
        self.assertEqual(
            ('-123123', '456456'), 
            self.obj.get_ids_from_url("https://vk.com/video-123123_456456"), 
            msg="Видео выложено от имени группы."
        )

    def test__get_ids_from_url__too_many_numbers(self):
        with self.assertRaises(URLParserError, msg="Слишком много чисел в url."):
            self.obj.get_ids_from_url("https://vk.com/video123123_456456_123456")

    def test__get_ids_from_url__not_enough_numbers(self):
        with self.assertRaises(URLParserError, msg="Слишком мало чисел в url."):
            self.obj.get_ids_from_url("https://vk.com/video123123")

    def test__load_default_config__creation(self):
        self.obj.load_default_config()

        self.assertTrue(
            os.path.isfile(self.obj.CONFIG_FILE_PATH),
            msg="Создание файла конфигураций."
        )

    def test__remove_config_file(self):
        with open(self.obj.CONFIG_FILE_PATH, "w") as config_file:
            print("Hello World", file=config_file)

        self.obj.remove_config_file()

        self.assertFalse(
            os.path.isfile(self.obj.CONFIG_FILE_PATH),
            msg="Удаление файла конфигураций."
        )

    def test__remove_comments_file(self):
        with open(os.path.join(self.obj.LOCATION, self.obj.config["FILE_OUTPUT"]["file_name"]), "w") as comments_file:
            print("Hello World", file=comments_file)

        self.obj.remove_comments_file()

        self.assertFalse(
            os.path.isfile(self.obj.LOG_FILE_PATH),
            msg="Удаление файла комментариев."
        )

    def test__remove_log_file(self):
        with open(self.obj.LOG_FILE_PATH, "w") as log_file:
            print("Hello World", file=log_file)

        self.obj.remove_log_file()
        
        self.assertFalse(
            os.path.isfile(self.obj.LOG_FILE_PATH),
            msg="Удаление файла лога."
        )

    def test__authorize_vk__correct(self):
        self.assertTrue(
            self.obj.authorize_vk("", ""),
            msg="Верные логин и пароль для авторизации."
        )

    def test__authorize_vk__incorrect(self):
        with self.assertRaises(VkAuthError, msg="Неверные логин и пароль для авторизации."):
            self.obj.authorize_vk("123", "123")


if __name__ == '__main__':
    unittest.main()
