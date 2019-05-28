import signal
import sys
from time import sleep

from halo import Halo
from vk.exceptions import VkAPIError

from vkcomments import VKComments


def exit_program():
    input("\nПрограмма остановлена. Нажмите [ENTER] для завершения работы.")
    sys.exit()


# Checking whether this is a script file or an frozen executable
IS_EXECUTABLE = True if getattr(sys, 'frozen', False) else False

# Defining handler for SIGINT (CTRL+C)
signal.signal(signal.SIGINT, signal.default_int_handler)

obj = VKComments()

# Reading config and authorizing
try:
    obj.load_config()
    obj.remove_comments_file()
    obj.authorize()
except KeyboardInterrupt:
    exit_program()
except Exception as e:
    if hasattr(e, 'message'):
        print(e.message)
    else:
        print(e)
    exit_program()

if obj:
    ready = False
    owner_id, video_id = 0, 0

    # Ask for url until it's successfully parsed or owner_id and video_id are entered manually
    while not ready:
        try:
            url = input("Введите url трансляции, либо [0] для ручного ввода id: ")

            if url in ["0", "[0]"]:
                owner_id = input("id пользователя: ")
                video_id = input("id видео: ")
            else:
                owner_id, video_id = obj.get_ids_from_url(url)

            obj.get_comments_number(owner_id, video_id)
        except KeyboardInterrupt:
            exit_program()
        except ValueError:
            print("Ошибка при распознавании url. Формат url: https://vk.com/videoXXXXX_XXXXX. Повторите попытку ввода.")
        except VkAPIError:
            print("Ошибка при доступе к API, возможно указанного видео не существует. Повторите попытку ввода.")
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
        else:
            ready = True

    # Getting comments and printing a spinner until escaped
    try:
        with Halo(text='Получение комментариев... (0) [CTRL+C для завершения работы]', spinner='dots') as sp:
            counter = 1

            while True:
                sp.text = "Получение комментариев... ({0}) [CTRL+C для завершения работы]".format(str(counter))

                data = obj.get_comments(owner_id, video_id)
                data = obj.get_usernames(data)
                obj.print_csv(data)

                counter += 1
                sleep(int(obj.config["SLEEP"]["sleep_time"]))
    except KeyboardInterrupt:
        exit_program()
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        exit_program()

