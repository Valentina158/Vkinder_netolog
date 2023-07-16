import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools
from data_store import engine, data_store_tools

class Botinterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.data_store_tools = data_store_tools(engine)
        self.check_user = data_store_tools(engine)
        self.params = {}
        self.worksheets = []
        self.offset = 0


    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                   {'user_id': user_id,
                    "message": message,
                    "attachment": attachment,
                    "random_id": get_random_id()}
                    )

    def handler_info(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                return event.text

    def int_check(self, num):
        try:
            int(num)
        except (TypeError, ValueError):
            return False
        else:
            return True

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:

                    if event.text.lower() == 'привет':
                        # логика получения данных о пользователе

                        self.params = self.vk_tools.get_profile_info(event.user_id)
                        self.message_send(event.user_id, f'Привет, {self.params["name"]},'
                                                         )
                        # недостающие данные

                        if self.params['year'] is None:
                            self.message_send(event.user_id, f'Укажите Ваш возраст, пожалуйста')
                            age = (self.handler_info())
                            while not self.int_check(age):
                                self.message_send(event.user_id, f'Введите корректный возраст')
                                age = (self.handler_info())
                            self.params['year'] = int(age)

                        if self.params['city'] is None:
                            self.message_send(event.user_id, f'Укажите Ваш город, пожалуйста')
                            self.params['city'] = self.handler_info()

                        if self.params['sex'] == 0:
                            self.message_send(event.user_id, f'Укажите Ваш пол, пожалуйста м/ж')
                            sex = (self.handler_info())
                            while sex not in 'мж':
                                self.message_send(event.user_id, f'Введите корректный пол м/ж')
                                sex = (self.handler_info())
                            self.params['sex'] = 1 if sex == 'ж' else 2

                        self.message_send(event.user_id, f'Введите "поиск" для поиска')

                    elif event.text.lower() == 'поиск':

                        # логика поиска анкет

                        self.message_send(
                            event.user_id, 'Начинаем поиск')

                        if  self.worksheets:
                            worksheet = self.worksheets.pop()

                            photos = self.vk_tools.get_photos(worksheet['id'])
                            photo_string = ''
                            for photo in photos:
                                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

                        else:
                            self.worksheets = self.vk_tools.search_worksheet(
                                self.params, self.offset)

                            worksheet = self.worksheets.pop()

                            # проверка в БД
                            while self.data_store_tools.check_user(event.user_id, worksheet["id"]) is True:
                                worksheet = self.worksheets.pop()

                            photos = self.vk_tools.get_photos(worksheet['id'])
                            photo_string = ''
                            for photo in photos:
                                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                            self.offset += 20

                        self.message_send(
                            event.user_id,
                            f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                            attachment = photo_string
                        )
                        # добавление в БД
                        if self.data_store_tools.check_user(event.user_id, worksheet["id"]) is False:
                            self.data_store_tools.add_user(event.user_id, worksheet["id"])

                        elif event.text.lower() == 'пока':
                            self.message_send(
                            event.user_id, 'До новых встреч')
                        else:
                            self.message_send(
                                event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = Botinterface(comunity_token, acces_token)
    bot_interface.event_handler()

