import vk
import re
import options
import getpass


class VKComments:
    def __init__(self, url, opt={}):
        """
        :param url: url of the post from which comments should be taken
        :param opt: options of api requests
        """

        self.options = options
        self.url = url

        if "access_token" in opt:
            self.options.access_token = opt["access_token"]
        if "api_version" in opt:
            self.options.api_version = opt["api_version"]
        if "need_likes" in opt:
            self.options.need_likes = opt["need_likes"]
        if "count" in opt:
            self.options.count = opt["count"]
        if "sort" in opt:
            self.options.sort = opt["sort"]
        if "thread_items_count" in opt:
            self.options.thread_items_count = opt["thread_items_count"]
        if "return_fields" in opt:
            self.options.return_fields = opt["return_fields"]
        if "file_name" in opt:
            self.options.file_name = opt["file_name"]

        # self.api = vk.API(
        #     vk.Session(access_token=self.options.access_token)
        # )

        self.api = vk.API(
            vk.AuthSession(options.app_id, input("Username: "), getpass.getpass(), scope='wall, video')
        )

    def parse_url(self):
        """
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

        # TODO
        t = re.split(
            # "https://vk\.com/.*\?[a-zA-Z]*=[a-zA-Z]*",
            "[a-zA-Zа-яА-ЯёЁ:/.?%=&_]+",
            self.url
        )

        owner_id = t[-2]
        post_id = t[-1]

        print("DEBUG: ", "owner_id: ", owner_id, "; post_id: ", post_id, sep="")

        return owner_id, post_id

    def get_comments(self):
        """
        :return: list of lists containing comments
        """
        data = []

        owner_id, post_id = self.parse_url()

        # Getting number of comments of a post
        # comments = self.api.wall.getComments(
        comments_number = self.api.video.getComments(
            v=self.options.api_version,

            owner_id=owner_id,
            # post_id=post_id,
            video_id=post_id,

            count=1
        )

        # Getting all comments of a post
        for i in range(0, comments_number["count"], 100):
            # comments = self.api.wall.getComments(
            comments = self.api.video.getComments(
                v=self.options.api_version,
                need_likes=self.options.need_likes,
                count=self.options.count,
                sort=self.options.sort,
                # thread_items_count=self.options.thread_items_count,

                owner_id=owner_id,
                # post_id=post_id,
                video_id=post_id,

                offset=i
            )

            for j in range(0, len(comments["items"])):

                line = []

                for k in self.options.return_fields:
                    line.append(comments["items"][j][k])

                data.append(line)

        print("DEBUG: ", "Comments received: ", comments_number["count"], sep="")

        return data

    def print_csv(self, data):
        """
        :param data: list of lists containing comments
        """
        if len(data) > 0:
            with open(self.options.file_name, "w") as f:
                for i in range(0, len(data)):
                    for j in range(0, len(data[i])):
                        if j != 0:
                            print(",", end="", file=f)
                        print("\"", data[i][j], end="\"", sep="", file=f)
                    print(";", file=f)

            print("Output written to file: ", self.options.file_name, sep="")
        else:
            print("No comments received.")
