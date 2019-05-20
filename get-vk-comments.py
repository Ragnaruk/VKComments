from vkcomments import VKComments
from time import sleep
from yaspin import yaspin

# https://vk.com/video1009205_456239050

# Initializing class and logging in
try:
    obj = VKComments()
except KeyboardInterrupt:
    obj = None
    print("\nПрограмма завершена.")
except Exception as e:
    obj = None
    if hasattr(e, 'message'):
        print(e.message)
    else:
        print(e)

if obj:
    ready = False
    owner_id, post_id = 0, 0

    # Ask for url until it's successfully parsed or owner_id and post_id are entered manually
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

    # Getting comments and printing a spinner until escaped
    try:
        with yaspin(color="magenta") as sp:
            counter = 1

            while True:
                sp.text = "Получение комментариев... (" + str(counter) + ") [CTRL+C для завершения работы]"

                data = obj.get_comments(owner_id, post_id)
                data = obj.get_usernames(data)
                obj.print_csv(data)

                counter += 1
                sleep(int(obj.config["SLEEP"]["sleep_time"]))
    except KeyboardInterrupt:
        print("\nПрограмма завершена.")
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
