from vkcomments import VKComments
from time import sleep
from yaspin import yaspin
import options

# https://vk.com/video1009205_456239050

try:
    obj = VKComments()
except Exception as e:
    obj = None

if obj:
    ready = False
    owner_id, post_id = 0, 0

    while not ready:
        try:
            url = input("Введите url трансляции: ")

            if url == "0":
                owner_id = input("id пользователя: ")
                post_id = input("id видео: ")
                ready = True
            else:
                owner_id, post_id = obj.parse_url(url)
                ready = True
        except Exception as e:
            print("Ошибка при распознавании url. Повторите попытку ввода, "
                  "либо введите 0 для того, чтобы задать id пользователя и видео вручную.")

    try:
        with yaspin(color="magenta") as sp:
            counter = 1

            while True:
                sp.text = "Получение комментариев... (" + str(counter) + ") [CTRL+C для завершения работы]"

                data = obj.get_comments(owner_id, post_id)
                data = obj.get_usernames(data)
                obj.print_csv(data)

                counter += 1
                sleep(options.sleep_time)
    except KeyboardInterrupt:
        print("Программа завершена.")
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
