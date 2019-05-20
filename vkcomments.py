import vk
import re
import getpass
import logging
import configparser
import os


CONFIG_FILE_NAME = "config.ini"
POSSIBLE_INPUT_VALUES = ["y", "n", "Y", "N", "yes", "no", "Yes", "No"]
YES_INPUT_VALUES = ["y", "Y", "yes", "Yes"]
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
sleep_time = 2
"""


class VKComments:
    def __init__(self):
        """
        :param opt: options of api requests
        """

        logging.basicConfig(filename="info.log", level=logging.INFO, filemode="w")

        self.offset = 0
        self.config = self.get_config()

        # Configparser doesn't support lists, so value needs to be split
        self.return_fields = list(filter(None, (
            x.strip() for x in (self.config["OPTIONS"]["return_fields"]).splitlines())))

        inp = ""
        if self.config["USER"]["username"] and self.config["USER"]["password"]:
            while inp not in POSSIBLE_INPUT_VALUES:
                inp = input("Войти как %s? [y/n]: " % self.config["USER"]["username"])

        if inp in YES_INPUT_VALUES:
            username = self.config["USER"]["username"]
            password = self.config["USER"]["password"]
        else:
            username = input("Логин: ")
            password = getpass.getpass("Пароль: ")

        self.api = vk.API(
            vk.AuthSession(int(self.config["APPLICATION"]["app_id"]), username, password, scope="video")
        )

        print("Авторизация прошла успешно.")
        logging.debug("Успешная авторизация как: " +
                      str(username) +
                      ".")

        open(self.config["OUTPUT"]["file_name"], "w")

    def get_config(self):
        """
        :return: config read from a file
        """

        if not os.path.isfile(CONFIG_FILE_NAME):
            self.print_default_config()

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE_NAME)

        return config

    def print_default_config(self):
        with open(CONFIG_FILE_NAME, "w") as configfile:
            print(DEFAULT_CONFIG, file=configfile)

            print("Файл конфигураций создан.")
            logging.info("Файл конфигураций c именем: " +
                          DEFAULT_CONFIG +
                          " создан.")

    def parse_url(self, url):
        """
        :param url: url to parse
        :return: parsed owner_id and post_id from a post url
        """

        # Parsing url with regex
        t = re.split(
            "[a-zA-Zа-яА-ЯёЁ:/.?%=&_]+",
            url
        )

        owner_id = t[-2]
        post_id = t[-1]

        if len(owner_id) == 0 or len(post_id) == 0:
            raise ValueError("Ошибка при распознавании url.")

        logging.debug("url: " +
                      url +
                      ".")
        logging.debug("owner_id / post_id: " +
                     str(owner_id) +
                     " / " +
                     str(post_id) +
                     ".")

        return owner_id, post_id

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

        logging.info("Комментариев получено/всего: " +
                     str(comments_number["count"] - self.offset) +
                     "/" +
                     str(comments_number["count"]) +
                     ".")

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
            with open(self.config["OUTPUT"]["file_name"], "a") as f:
                for i in range(0, len(data)):
                    print("\"" + "\",\"".join(str(x) for x in data[i]) + "\"", end=";\n", file=f)

            logging.info("Комментарии записаны в файл: " + str(self.config["OUTPUT"]["file_name"]) + ".")
        else:
            logging.info("Новых комментариев нет.")
