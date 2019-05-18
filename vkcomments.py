import vk
import re
import options
import getpass
import logging


class VKComments:
    def __init__(self, opt={}):
        """
        :param opt: options of api requests
        """

        self.options = options
        self.offset = 0

        if "api_version" in opt:
            self.options.api_version = opt["api_version"]
        if "need_likes" in opt:
            self.options.need_likes = opt["need_likes"]
        if "count" in opt:
            self.options.count = opt["count"]
        if "sort" in opt:
            self.options.sort = opt["sort"]
        if "return_fields" in opt:
            self.options.return_fields = opt["return_fields"]
        if "file_name" in opt:
            self.options.file_name = opt["file_name"]
        if "username" in opt:
            self.options.username = opt["username"]
        if "password" in opt:
            self.options.password = opt["password"]

        logging.basicConfig(filename="info.log", level=logging.INFO, filemode="w")
        open(self.options.file_name, "w")

        # self.api = vk.API(
        #     vk.Session(access_token=self.options.access_token)
        # )

        inp = ""
        if self.options.username and self.options.password:
            while inp not in ["y", "n", "Y", "N", "yes", "no", "Yes", "No"]:
                inp = input("Войти как %s? [y/n]: " % self.options.username)

        if inp in ["y", "Y", "yes", "Yes"]:
            username = self.options.username
            password = self.options.password
        else:
            username = input("Логин: ")
            password = getpass.getpass("Пароль: ")

        self.api = vk.API(
            vk.AuthSession(options.app_id, username, password, scope="wall, video")
        )

        print("Авторизация прошла успешно.")

    def parse_url(self, url):
        """
        :param url: url to parse
        :return: parsed owner_id and post_id from a post url
        """

        # t = list(
        #     filter(
        #         None,
        #         re.split(
        #             # "https://vk\.com/.*\?[a-zA-Z]*=[a-zA-Z]*",
        #             "[a-zA-Zа-яА-ЯёЁ:/.?%=&_]*",
        #             self.url
        #         )
        #     )
        # )
        #
        # t = re.split(
        #     "[^-0-9]",
        #     t
        # )

        t = re.split(
            # "https://vk\.com/.*\?[a-zA-Z]*=[a-zA-Z]*",
            "[a-zA-Zа-яА-ЯёЁ:/.?%=&_]+",
            url
        )

        owner_id = t[-2]
        post_id = t[-1]

        if len(owner_id) == 0 or len(post_id) == 0:
            raise ValueError("Ошибка при распознавании url.")

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
            v=self.options.api_version,

            owner_id=owner_id,
            video_id=post_id,

            count=1
        )

        # Getting all comments of a post
        for i in range(self.offset, comments_number["count"], 100):
            comments = self.api.video.getComments(
                v=self.options.api_version,
                need_likes=self.options.need_likes,
                count=self.options.count,
                sort=self.options.sort,

                owner_id=owner_id,
                video_id=post_id,

                offset=i
            )

            for j in range(0, len(comments["items"])):

                line = []

                for k in self.options.return_fields:
                    if k == "likes":
                        line.append(comments["items"][j][k]["count"])
                    else:
                        line.append(comments["items"][j][k])

                data.append(line)

        logging.info("Комментариев получено / Комментариев всего: " +
                     str(comments_number["count"] - self.offset) +
                     " / " +
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

        # Method api.users.get() doesn't return repetitions
        user_dictionary = {}
        for user_ids in user_ids_array:
            users = self.api.users.get(
                v=self.options.api_version,
                user_ids=user_ids,
                fields="photo_50"
            )

            for user in users:
                user_dictionary[user["id"]] = [user["first_name"] + " " + user["last_name"], user["photo_50"]]

        for d in data:
            d.append(user_dictionary[d[0]][1])
            d[0] = user_dictionary[d[0]][0]

        return data

    def print_csv(self, data):
        """
        :param data: list of lists containing comments
        """
        if len(data) > 0:
            with open(self.options.file_name, "a") as f:
                for i in range(0, len(data)):
                    print("\"" + "\",\"".join(str(x) for x in data[i]) + "\"", end=";\n", file=f)

            logging.info("Комментарии записаны в файл: " + str(self.options.file_name) + ".")
        else:
            logging.info("Новых комментариев нет.")
