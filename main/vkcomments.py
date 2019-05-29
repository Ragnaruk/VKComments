import configparser
import logging
import os
import re
import sys
from time import sleep

import vk


class VKVideoCommentsGetter:
    # Detecting whether application is a script file or frozen exe
    LOCATION = os.path.dirname(os.path.abspath(sys.executable)) \
        if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    POSSIBLE_INPUT_VALUES = ["y", "n", "Y", "N", "yes", "no", "Yes", "No"]
    YES_INPUT_VALUES = ["y", "Y", "yes", "Yes"]

    CONFIG_FILE_NAME = "config.ini"
    CONFIG_FILE_PATH = os.path.join(LOCATION, CONFIG_FILE_NAME)
    LOG_FILE_NAME = "log.log"
    LOG_FILE_PATH = os.path.join(LOCATION, LOG_FILE_NAME)
    COMMENTS_FILE_NAME = None
    COMMENTS_FILE_PATH = None

    DEFAULT_CONFIG = (
        "## Файл с настройками приложения\n"
        "# Удалите этот файл для получения настроек по умолчанию\n"
        "\n"
        "[APPLICATION]\n"
        "# ID приложения, от которого идут запросы к api\n"
        "app_id = 6947304\n"
        "\n"
        "[OPTIONS]\n"
        "# Версия используемого api\n"
        "api_version = 5.95\n"
        "# Требуется ли возвращать кол-во лайков к комментариям (0 — нет, 1 — да)\n"
        "need_likes = 1\n"
        "# Кол-во комментариев, возвращаемых в одном запросе (Натуральное число от 1 до 100."
        " Уменьшение этого числа может сильно влиять на производительность)\n"
        "count = 100\n"
        "# В каком порядке сортировать комментарии (asc — от старых к новым, desc — от новых к старым)\n"
        "sort = asc\n"
        "# Возвращаемые поля комментариев (Полный список: https://vk.com/dev/objects/comment)\n"
        "return_fields = \n"
        "    from_id\n"
        "    date\n"
        "    text\n"
        "# Максимальное кол-во возвращаемых комментариев (0 - вернуть все."
        " Увеличение этого числа может сильно влиять на производительность)\n"
        "max_count = 1000\n"
        "\n"
        "[OUTPUT]\n"
        "# Название выходного файла\n"
        "file_name = comments.csv\n"
        "\n"
        "[USER]\n"
        "# Логин и пароль, по которым происходит вход\n"
        "username = \n"
        "password = \n"
        "\n"
        "[SLEEP]\n"
        "# Время ожидания между запросами к api в секундах\n"
        "sleep_time = 2\n"
    )

    def __init__(self):
        # Enabling logging with specified settings
        logging.basicConfig(
            filename=self.LOG_FILE_PATH,
            level=logging.INFO,
            filemode="w",
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Getting a logger with specified name
        self.logger = logging.getLogger('VKVideoCommentsGetter')

        self.offset = 0

        self.config = None
        self.return_fields = None

        self.api = None

    # TODO (?) Combine all remove file functions
    def remove_config_file(self):
        if self.CONFIG_FILE_PATH and os.path.exists(self.CONFIG_FILE_PATH):
            os.remove(self.CONFIG_FILE_PATH)
            
            return True

        return False

    def remove_comments_file(self):
        if self.COMMENTS_FILE_PATH and os.path.exists(self.COMMENTS_FILE_PATH):
            os.remove(self.COMMENTS_FILE_PATH)
            
            return True

        return False

    def remove_log_file(self):
        if self.LOG_FILE_PATH and os.path.exists(self.LOG_FILE_PATH):
            os.remove(self.LOG_FILE_PATH)
            
            return True
        
        return False

    def authorize(self, username, password):
        self.api = vk.API(vk.AuthSession(
            int(self.config["APPLICATION"]["app_id"]), 
            username, 
            password, 
            scope="video")
        )

        self.logger.info("Успешная авторизация как: {0}.".format(str(username)))

        return True

    # TODO config validation and versioning
    def load_config(self):
        # Insurance
        self.print_default_config()

        self.config = configparser.ConfigParser()
        self.config.read(self.CONFIG_FILE_PATH)

        # Configparser doesn't support lists, so value needs to be split
        self.return_fields = list(filter(None, (
            x.strip() for x in (self.config["OPTIONS"]["return_fields"]).splitlines())))

        self.COMMENTS_FILE_NAME = self.config["OUTPUT"]["file_name"]
        self.COMMENTS_FILE_PATH = os.path.join(self.LOCATION, self.config["OUTPUT"]["file_name"])

        return True

    def print_default_config(self):
        # Creating default config if it doesn't exist
        if not os.path.isfile(self.CONFIG_FILE_PATH):
            with open(self.CONFIG_FILE_PATH, "w") as configfile:
                print(self.DEFAULT_CONFIG, end="", file=configfile)

            self.logger.info("Файл конфигураций c именем: {0} создан.".format(self.CONFIG_FILE_NAME))

            return True

        return False

    def get_ids_from_url(self, url):
        """
        :param url: url to parse
        :return: parsed owner_id and video_id from a video url
        """

        # Parsing url with regex
        t = re.split(
            "[a-zA-Zа-яА-ЯёЁ:/.?%=&_]+",
            url
        )

        # Removing empty strings
        t = list(filter(None, t))

        if len(t) != 2 or len(t[0]) == 0 or len(t[1]) == 0:
            raise ValueError("Ошибка при распознавании url.")

        owner_id = t[0]
        video_id = t[1]

        self.logger.info("Полученный url: {0}.".format(str(url)))
        self.logger.info("Распознанные owner_id/video_id: {0}/{1}.".format(str(owner_id), str(video_id)))

        return owner_id, video_id

    def get_comments_number(self, owner_id, video_id):
        comments_number = self.api.video.getComments(
            v=self.config["OPTIONS"]["api_version"],

            owner_id=owner_id,
            video_id=video_id,

            count=1
        )["count"]

        return comments_number

    def get_comments(self, owner_id, video_id):
        data = []

        comments_number = self.get_comments_number(owner_id, video_id)

        # Setting max number of received comments
        if self.offset == 0 and comments_number > int(self.config["OPTIONS"]["max_count"]) > 0:
            self.offset = comments_number - int(self.config["OPTIONS"]["max_count"])

        # WIP: VK API execute method
        # code = """
        # var c = API.video.getComments({'v':{v},'owner_id':{owner_id},'video_id':{video_id},'count':1});
        # var i = 0;
        # var a = [];
        # while (i < count) {
        #     a = API.video.getComments({'v':{v},'owner_id':{owner_id},'video_id':{video_id},'count':100});
        #     i = i + 1;
        # }
        # return a;
        # """.format(
        #     v=str(self.config["OPTIONS"]["api_version"]),
        #     owner_id=str(owner_id),
        #     video_id=str(video_id)
        # )

        # Getting all comments of a video
        for i in range(self.offset, comments_number, 100):
            # VK Api is limited to 3 requests per second for users
            sleep(0.34)

            comments = self.api.video.getComments(
                v=self.config["OPTIONS"]["api_version"],
                need_likes=self.config["OPTIONS"]["need_likes"],
                count=self.config["OPTIONS"]["count"],
                sort=self.config["OPTIONS"]["sort"],

                owner_id=owner_id,
                video_id=video_id,

                offset=i
            )

            # Getting all needed fields from comments
            for j in range(0, len(comments["items"])):

                line = []

                for k in self.return_fields:
                    line.append(comments["items"][j][k])

                if self.config["OPTIONS"]["need_likes"] == "1":
                    line.append(comments["items"][j]["likes"]["count"])

                data.append(line)

        self.logger.info("Комментариев получено/всего: {0}/{1}."
                         .format(str(comments_number - self.offset), str(comments_number)))

        self.offset = comments_number

        return data

    def get_usernames(self, data):
        # Method api.users.get() accepts a maximum of a thousand user_ids in one call
        user_ids_array = []
        for i in range(0, len(data), 1000):
            user_ids_array.append(",".join(str(x[0]) for x in data[i:i + 1000:1]))

        # Method api.users.get() doesn't return repeating users
        username_dictionary = {}
        avatar_dictionary = {}
        for user_ids in user_ids_array:
            # VK Api is limited to 3 requests per second for users
            sleep(0.34)

            # Doesn't return anything for a deleted user
            users = self.api.users.get(
                v=self.config["OPTIONS"]["api_version"],
                user_ids=user_ids,
                fields="photo_50"
            )

            # Get first and last name, plus a link to a downscaled avatar
            for user in users:
                username_dictionary[user["id"]] = user["first_name"] + " " + user["last_name"]
                avatar_dictionary[user["id"]] = user["photo_50"]

        # Replacing user_ids with usernames and appending avatar links
        for d in data:
            user_id = d[0]

            if user_id in username_dictionary:
                d[0] = username_dictionary[user_id]

            if user_id in avatar_dictionary:
                d.append(avatar_dictionary[user_id])
            else:
                d.append("")

        return data

    def print_comments(self, data):
        if len(data) > 0:
            with open(os.path.join(self.LOCATION, self.config["OUTPUT"]["file_name"]), "a", encoding="utf8") as f:
                for i in range(0, len(data)):
                    print("\"" + "\",\"".join(str(x) for x in data[i]) + "\"", end=";\n", file=f)

            self.logger.info("Комментарии записаны в файл: {0}.".format(self.config["OUTPUT"]["file_name"]))

        return True
