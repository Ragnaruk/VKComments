import signal
import getpass
import sys
from time import sleep

from halo import Halo
from vk.exceptions import VkAPIError, VkAuthError

from vk_video_comments_getter import VKVideoCommentsGetter


# Defining handler for SIGINT (CTRL+C)
signal.signal(signal.SIGINT, signal.default_int_handler)


# Loading (or creating and loading config) and removing previous comments file
def ready_files():
    try:
        if obj.print_default_config():
            input("Файл конфигураций создан. Нажмите [ENTER] для продолжения работы.")

        obj.load_config()

        obj.remove_comments_file()
    except KeyboardInterrupt:
        exit_program()
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        exit_program()


# Authorizing with credentials in config file or with inputted ones
def authorize():
    while True:
        try:
            inp = ""
            if obj.config["USER"]["username"] and obj.config["USER"]["password"]:
                while inp not in obj.POSSIBLE_INPUT_VALUES:
                    inp = input("Войти как {0}? [y/n]: ".format(obj.config["USER"]["username"]))
            
            if inp in obj.YES_INPUT_VALUES:
                username = obj.config["USER"]["username"]
                password = obj.config["USER"]["password"]
            else:
                username = input("Логин: ")
                password = getpass.getpass("Пароль: ")

            obj.authorize(username, password)

            print("Авторизация прошла успешно.")
        except VkAuthError:
            input("Авторизация неуспешна. Нажмите [ENTER] для новой попытки.")
        except KeyboardInterrupt:
            exit_program()
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            exit_program()
        else:
            break


# Asking for url until it's successfully parsed or owner_id and video_id are entered manually
def get_video_ids():
    while True:
        try:
            url = input("Введите url трансляции, либо [0] для ручного ввода id: ")

            if url in ["0", "[0]"]:
                owner_id = input("ID пользователя: ")
                video_id = input("ID видео: ")
            else:
                owner_id, video_id = obj.get_ids_from_url(url)

            obj.get_comments_number(owner_id, video_id)
        except ValueError:
            print("Ошибка при распознавании url. Формат url: https://vk.com/videoXXXXX_XXXXX. Повторите попытку ввода.")
        except VkAPIError:
            print("Ошибка при доступе к API, возможно указанного видео не существует. Повторите попытку ввода.")
        except KeyboardInterrupt:
            exit_program()
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
        else:
            break

    return owner_id, video_id


# Getting comments and printing a spinner until escaped
def get_comments(owner_id, video_id, sleep_time):
    try:
        with Halo(text='Получение комментариев... (0) [CTRL+C для завершения работы]', spinner='dots') as sp:
            counter = 1

            while True:
                sp.text = "Получение комментариев... ({0}) [CTRL+C для завершения работы]".format(str(counter))

                data = obj.get_comments(owner_id, video_id)
                data = obj.get_usernames(data)
                obj.print_comments(data)

                counter += 1
                sleep(sleep_time)
    except KeyboardInterrupt:
        exit_program()
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        exit_program()


def exit_program():
    input("\nПрограмма остановлена. Нажмите [ENTER] для завершения работы.")
    obj.logger.info("Программа остановлена пользователем.")
    sys.exit()


obj = VKVideoCommentsGetter()

ready_files()
authorize()

o_id, v_id = get_video_ids()
s_time = int(obj.config["SLEEP"]["sleep_time"])

get_comments(o_id, v_id, s_time)

exit_program()
