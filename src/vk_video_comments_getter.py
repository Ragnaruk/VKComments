import configparser
import logging
import os.path
import re
import sys
from time import sleep

import vk


class URLParserError(Exception):
    pass


class ConfigValidationError(Exception):
    pass


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

        # Disabling built-in logging of vk package
        logger = logging.getLogger('vk')
        logger.disabled = True

        # For config
        self.config = configparser.ConfigParser(allow_no_value=True)
        # To allow case-sensitive keys
        self.config.optionxform = str

        # For getting comments
        self.offset = 0
        self.return_fields = None

        # For VK and Google Sheets
        self.vk_api = None
        self.google_sheets_service = None

    def remove_config_file(self):
        if self.CONFIG_FILE_PATH and os.path.exists(self.CONFIG_FILE_PATH):
            os.remove(self.CONFIG_FILE_PATH)
            
            return True

        return False

    def remove_comments_file(self):
        if os.path.join(
                self.LOCATION,
                self.config["FILE_OUTPUT"]["file_name"]
        ) and os.path.exists(
            os.path.join(
                self.LOCATION,
                self.config["FILE_OUTPUT"]["file_name"])
        ):
            os.remove(os.path.join(self.LOCATION, self.config["FILE_OUTPUT"]["file_name"]))
            
            return True

        return False

    def remove_log_file(self):
        if self.LOG_FILE_PATH and os.path.exists(self.LOG_FILE_PATH):
            os.remove(self.LOG_FILE_PATH)
            
            return True
        
        return False

    def authorize_vk(self, username, password):
        self.vk_api = vk.API(vk.AuthSession(
            int(self.config["APPLICATION"]["app_id"]), 
            username, 
            password, 
            scope="video")
        )

        self.logger.info("Успешная авторизация как: {0}.".format(str(username)))

        return True

    def load_config(self):
        # Stop working if config is not valid
        if not self.validate_config_keys():
            with open(self.CONFIG_FILE_PATH, "w") as configfile:
                self.config.write(configfile)

            raise ConfigValidationError()

        return True

    def validate_config_keys(self):
        """
        :return: True if config was updated and False if it was not
        """
        new_config = configparser.ConfigParser(allow_no_value=True)
        new_config.optionxform = str

        new_config.read(self.CONFIG_FILE_PATH)

        config_is_valid = True

        # Validate new config and print warnings for all missing fields
        for section in self.config.sections():
            if section in new_config.sections():
                for key in self.config[section]:
                    # Ignore comments
                    if key[0] not in ["#", ";"]:
                        if key in new_config[section]:
                            self.config[section][key] = new_config[section][key]
                        else:
                            config_is_valid = False

                            print("Не найден ключ {0} в секции {1} в файле конфигураций.".format(key, section))
                            self.logger.info("Ключ {0} в секции {1} в файле конфигураций создан.".format(key, section))
            else:
                config_is_valid = False

                print("Не найдена секция {0} в файле конфигураций.".format(section))
                self.logger.info("Секция {0} в файле конфигураций создана.".format(section))

        return config_is_valid

    def load_default_config(self):
        self.config["APPLICATION"] = {
            "# ID приложения, от которого идут запросы к api"
            " (Ссылка на описание: https://vk.com/dev/first_guide)": None,
            "app_id": "6947304",
            "# Время ожидания между запросами к api в секундах": None,
            "sleep_time": "2"
        }

        self.config["VK_OPTIONS"] = {
            "# Версия используемого api": None,
            "api_version": "5.95",
            "# Требуется ли возвращать кол-во лайков к комментариям (0 — нет, 1 — да)": None,
            "need_likes": "1",
            "# Кол-во комментариев, возвращаемых в одном запросе (Натуральное число от 1 до 100."
            " Уменьшение этого числа может сильно влиять на производительность))": None,
            "count": "100",
            "# В каком порядке сортировать комментарии (asc — от старых к новым, desc — от новых к старым)": None,
            "sort": "asc",
            "# Возвращаемые поля комментариев (Полный список: https://vk.com/dev/objects/comment)": None,
            "return_fields": ("\n"
                              "from_id\n"
                              "date\n"
                              "text"),
            "# Максимальное кол-во возвращаемых комментариев"
            " (0 - вернуть все. Увеличение этого числа может сильно влиять на производительность))": None,
            "max_count": "1000"
        }

        self.config["FILE_OUTPUT"] = {
            "# Название выходного файла": None,
            "file_name": "comments.csv"
        }

        self.config["USER"] = {
            "# Логин и пароль, по которым происходит вход VK": None,
            "username": "",
            "password": ""
        }

        # Creating default config if it doesn't exist
        if not os.path.isfile(self.CONFIG_FILE_PATH):
            with open(self.CONFIG_FILE_PATH, "w") as configfile:
                self.config.write(configfile)

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
            raise URLParserError()

        owner_id = t[0]
        video_id = t[1]

        self.logger.info("Полученный url: {0}.".format(str(url)))
        self.logger.info("Распознанные owner_id/video_id: {0}/{1}.".format(str(owner_id), str(video_id)))

        return owner_id, video_id

    def get_comments_number(self, owner_id, video_id):
        comments_number = self.vk_api.video.getComments(
            v=self.config["VK_OPTIONS"]["api_version"],

            owner_id=owner_id,
            video_id=video_id,

            count=1
        )["count"]

        return comments_number

    def get_return_fields(self):
        # Configparser doesn't support lists, so value needs to be split
        return list(filter(None, (x.strip() for x in (self.config["VK_OPTIONS"]["return_fields"]).splitlines())))

    def get_comments(self, owner_id, video_id):
        data = []

        comments_number = self.get_comments_number(owner_id, video_id)
        return_fields = self.get_return_fields()

        # Setting max number of received comments
        if self.offset == 0 and comments_number > int(self.config["VK_OPTIONS"]["max_count"]) > 0:
            self.offset = comments_number - int(self.config["VK_OPTIONS"]["max_count"])

        # TODO VK API execute method
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
        #     v=str(self.config["VK_OPTIONS"]["api_version"]),
        #     owner_id=str(owner_id),
        #     video_id=str(video_id)
        # )

        # Getting all comments of a video
        for i in range(self.offset, comments_number, int(self.config["VK_OPTIONS"]["count"])):
            # VK Api is limited to 3 requests per second for ordinary users
            sleep(0.34)

            # Setting a limit on received comments to avoid getting comments which appeared
            # between the time of the start of the function and now
            if comments_number - i < int(self.config["VK_OPTIONS"]["count"]):
                count = comments_number - i
            else:
                count = int(self.config["VK_OPTIONS"]["count"])

            comments = self.vk_api.video.getComments(
                v=self.config["VK_OPTIONS"]["api_version"],
                need_likes=self.config["VK_OPTIONS"]["need_likes"],
                count=count,
                sort=self.config["VK_OPTIONS"]["sort"],

                owner_id=owner_id,
                video_id=video_id,

                offset=i
            )

            # Getting all needed fields from comments
            for j in range(0, len(comments["items"])):

                line = []

                for k in return_fields:
                    line.append(comments["items"][j][k])

                if self.config["VK_OPTIONS"]["need_likes"] == "1":
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
            users = self.vk_api.users.get(
                v=self.config["VK_OPTIONS"]["api_version"],
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
            with open(
                    os.path.join(
                        self.LOCATION,
                        self.config["FILE_OUTPUT"]["file_name"]),
                    "a",
                    encoding="utf8"
            ) as f:
                for i in range(0, len(data)):
                    print("\"" + "\",\"".join(str(x) for x in data[i]) + "\"", end=";\n", file=f)

            self.logger.info("Комментарии записаны в файл: {0}.".format(self.config["FILE_OUTPUT"]["file_name"]))

        return True
