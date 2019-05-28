import configparser
import getpass
import logging
import os
import re
import sys

import vk
from vk.exceptions import VkAuthError


class VKComments:
    # Detecting whether application is a script file or frozen exe
    LOCATION = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(
        os.path.abspath(__file__))

    POSSIBLE_INPUT_VALUES = ["y", "n", "Y", "N", "yes", "no", "Yes", "No"]
    YES_INPUT_VALUES = ["y", "Y", "yes", "Yes"]
    CONFIG_FILE_NAME = "config.ini"
    LOG_FILE_NAME = "log.log"

    DEFAULT_CONFIG = """## Файл с настройками приложения
# Удалите этот файл для получения настроек по умолчанию

[APPLICATION]
# Id приложения, от которого идут запросы к api
app_id = 6947304

[OPTIONS]
# Версия используемого api
api_version = 5.95
# Требуется ли возвращать кол-во лайков к комментариям (0 — нет, 1 — да)
need_likes = 1
# Кол-во комментариев, возвращаемых в одном запросе (Натуральное число от 1 до 100)
count = 100
# В каком порядке сортировать комментарии (asc — от старых к новым, desc — от новых к старым)
sort = asc
# Возвращаемые поля комментариев
return_fields = 
    from_id
    date
    text
    likes

[OUTPUT]
# Название выходного файла
file_name = comments.csv

[USER]
# Логин и пароль, по которым происходит вход
username = 
password = 

[SLEEP]
# Время ожидания между запросами к api в секундах
sleep_time = 2"""

    def __init__(self):
        # Enabling logging on the level INFO
        logging.basicConfig(filename=os.path.join(self.LOCATION, self.LOG_FILE_NAME), level=logging.INFO, filemode="w")
        self.logger = logging.getLogger('VKComments')

        self.offset = 0

        self.config = None
        self.return_fields = None

        self.api = None

    def authorize(self):
        ready = False
        while not ready:
            try:
                username, password = self.get_credentials()
                self.api = vk.API(self.get_vk_session(username, password))

                print("Авторизация прошла успешно.")
                self.logger.info("Успешная авторизация как: {0}.".format(str(username)))
            except VkAuthError as e:
                input("Авторизация неуспешна. Нажмите [ENTER] для новой попытки.")
            else:
                ready = True

    def load_config(self):
        # Creating default config if it doesn't exist
        if not os.path.isfile(os.path.join(self.LOCATION, self.CONFIG_FILE_NAME)):
            self.print_default_config()

        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(self.LOCATION, self.CONFIG_FILE_NAME))

        # Configparser doesn't support lists, so value needs to be split
        self.return_fields = list(filter(None, (
            x.strip() for x in (self.config["OPTIONS"]["return_fields"]).splitlines())))

    def remove_comments_file(self):
        if os.path.exists(os.path.join(self.LOCATION, self.config["OUTPUT"]["file_name"])):
            os.remove(os.path.join(self.LOCATION, self.config["OUTPUT"]["file_name"]))

    def get_credentials(self):
        inp = ""
        if self.config["USER"]["username"] and self.config["USER"]["password"]:
            while inp not in self.POSSIBLE_INPUT_VALUES:
                inp = input("Войти как {0}? [y/n]: ".format(self.config["USER"]["username"]))

        if inp in self.YES_INPUT_VALUES:
            username = self.config["USER"]["username"]
            password = self.config["USER"]["password"]
        else:
            username = input("Логин: ")
            password = getpass.getpass("Пароль: ")

        return username, password

    def get_vk_session(self, username, password):
        return vk.AuthSession(int(self.config["APPLICATION"]["app_id"]), username, password, scope="video")

    def print_default_config(self):
        with open(os.path.join(self.LOCATION, self.CONFIG_FILE_NAME), "w") as configfile:
            print(self.DEFAULT_CONFIG, file=configfile)

        input("Файл конфигураций создан. Нажмите [ENTER] для продолжения работы.")
        self.logger.info("Файл конфигураций c именем: {0} создан.".format(self.CONFIG_FILE_NAME))

    def get_ids_from_url(self, url):
        """
        :param url: url to parse
        :return: parsed owner_id and post_id from a post url
        """

        # Parsing url with regex
        t = re.split(
            "[a-zA-Zа-яА-ЯёЁ:/.?%=&_]+",
            url
        )

        # Removing empty strings
        t = list(filter(None, t))

        if len(t) != 2 or len(t[-1]) == 0 or len(t[-2]) == 0:
            raise ValueError("Ошибка при распознавании url.")

        owner_id = t[-2]
        post_id = t[-1]

        self.logger.debug("url: {0}.".format(str(url)))
        self.logger.debug("owner_id / post_id: {0} / {1}.".format(str(owner_id), str(post_id)))

        return owner_id, post_id

    def check_url(self, owner_id, post_id):
        self.api.video.getComments(
            v=self.config["OPTIONS"]["api_version"],

            owner_id=owner_id,
            video_id=post_id,

            count=1
        )

    def get_comments(self, owner_id, post_id):
        """
        :param owner_id: id of the owner
        :param post_id: id of the post
        :return: comments from the post
        """

        data = []

        # Getting number of comments of a post
        comments_number = self.api.video.getComments(
            v=self.config["OPTIONS"]["api_version"],

            owner_id=owner_id,
            video_id=post_id,

            count=1
        )

        # Getting all comments of a post
        for i in range(self.offset, comments_number["count"], 100):
            comments = self.api.video.getComments(
                v=self.config["OPTIONS"]["api_version"],
                need_likes=self.config["OPTIONS"]["need_likes"],
                count=self.config["OPTIONS"]["count"],
                sort=self.config["OPTIONS"]["sort"],

                owner_id=owner_id,
                video_id=post_id,

                offset=i
            )

            # Getting all needed fields from comments
            for j in range(0, len(comments["items"])):

                line = []

                for k in self.return_fields:
                    if k == "likes":
                        line.append(comments["items"][j][k]["count"])
                    else:
                        line.append(comments["items"][j][k])

                data.append(line)

        self.logger.info("Комментариев получено/всего: {0}/{1}.".format(str(comments_number["count"] - self.offset),
                                                                        str(comments_number["count"])))

        self.offset = comments_number["count"]

        return data

    def get_usernames(self, data):
        """
        :param data: list of lists containing comments with user_ids
        :return: list of lists containing comments with usernames
        """

        # Method api.users.get() accepts a maximum of a thousand user_ids in one call
        user_ids_array = []
        for i in range(0, len(data), 1000):
            user_ids_array.append(",".join(str(x[0]) for x in data[i:i + 1000:1]))

        # Method api.users.get() doesn't return repeating users
        user_dictionary = {}
        for user_ids in user_ids_array:
            users = self.api.users.get(
                v=self.config["OPTIONS"]["api_version"],
                user_ids=user_ids,
                fields="photo_50"
            )

            # Get first and last name, plus a link to a downscaled avatar
            for user in users:
                user_dictionary[user["id"]] = [user["first_name"] + " " + user["last_name"], user["photo_50"]]

        # Replacing user_ids with usernames and appending avatar links
        for d in data:
            d.append(user_dictionary[d[0]][1])
            d[0] = user_dictionary[d[0]][0]

        return data

    def print_csv(self, data):
        """
        :param data: list of lists containing comments
        """

        if len(data) > 0:
            with open(os.path.join(self.LOCATION, self.config["OUTPUT"]["file_name"]), "a") as f:
                for i in range(0, len(data)):
                    print("\"" + "\",\"".join(str(x) for x in data[i]) + "\"", end=";\n", file=f)

            self.logger.info("Комментарии записаны в файл: {0}.".format(self.config["OUTPUT"]["file_name"]))
        else:
            self.logger.info("Новых комментариев нет.")
