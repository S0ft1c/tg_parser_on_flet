import asyncio

import tmpls
from db import AsyncSQLiteSessionDB
import os
import shutil
from dotenv import load_dotenv
import flet as ft
import datetime as dt
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import PeerChannel, PeerChat

# Configuring the api's
load_dotenv()
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
SYSTEM_VERSION = os.environ.get('SYSTEM_VERSION')


async def main(page: ft.Page):
    def on_window_event_custom(e: ft.WindowEvent):
        def handle_closing_window():
            folder_path = './photos'
            # Ensure the folder exists
            if not os.path.exists(folder_path):
                print(f"The folder {folder_path} does not exist.")
                return

            # Iterate over the files in the folder
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                try:
                    # Check if it's a file (not a directory)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Delete the file
                        print(f"Deleted file: {file_path}")
                    elif os.path.isdir(file_path):
                        # Delete the directory and its contents
                        shutil.rmtree(file_path)
                        print(f"Deleted directory: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            page.window.destroy()

        if e.data == 'close':  # if we are closing window
            handle_closing_window()

    async def plusw_view(e: ft.ControlEvent = None):
        def on_file_selected(event: ft.FilePickerResultEvent):
            if event.files:
                selected_file = event.files[0]
                file_path = selected_file.path

                # here a logic to append all the words
                with open(file_path, 'r+') as ff:
                    lines = ff.readlines()
                    page.session.set('plusw', lines)

                    for idx, el in enumerate(lines):
                        plusw_list_view.controls.append(
                            ft.Text(
                                value=el,
                                bgcolor=ft.colors.WHITE12 if idx % 2 == 0 else ft.colors.BLACK
                            )
                        )

                page.update()

        async def clear_the_plusw(e: ft.ControlEvent = None):
            page.session.set('plusw', '')
            plusw_list_view.clean()

        async def add_one_plusw(e: ft.ControlEvent = None):
            data = page.session.get('plusw')
            if not data:
                data = []
            data.append(plusw_add_text_field.value)
            plusw_list_view.controls.append(
                ft.Text(
                    value=plusw_add_text_field.value
                )
            )
            plusw_add_text_field.value = ''
            page.session.set('plusw', data)

            page.update()

        page.views.clear()
        view = ft.View()

        # add a back btn
        view.controls.append(ft.Row(controls=[
            await tmpls.back_to_home_btn(home_view)
        ]))

        # the main lists
        h4_plusw = ft.Text(
            value='Плюс слова',
            color=ft.colors.PURPLE_200,
            size=24
        )
        view.controls.append(h4_plusw)

        plusw_words = page.session.get('plusw')
        if not plusw_words:
            plusw_words = []
        plusw_list_view = ft.ListView(
            controls=[ft.Text(value=el) for el in plusw_words],
            width=480,
            height=300,
        )
        plusw_divider = ft.Divider(
            thickness=1,
            leading_indent=20,
            trailing_indent=20,
            color=ft.colors.RED_400,
        )

        clear_plusw_list_view_btn = ft.ElevatedButton(
            text='Очистить',
            bgcolor=ft.colors.RED_400,
            width=150,
            height=40,
            on_click=clear_the_plusw,
        )
        view.controls.append(ft.Row(controls=[
            ft.Column(controls=[plusw_list_view]), ft.Column(controls=[clear_plusw_list_view_btn])
        ]))
        view.controls.append(plusw_divider)

        plusw_add_text_field = ft.TextField(label='Введите слово')
        plusw_add_btn = ft.ElevatedButton(
            icon=ft.icons.ADD,
            icon_color=ft.colors.AMBER_200,
            text='Добавить',
            on_click=add_one_plusw,
            bgcolor=ft.colors.WHITE12
        )
        view.controls.append(ft.Row(controls=[
            ft.Column(controls=[plusw_add_text_field]),
            ft.Column(controls=[plusw_add_btn])
        ]))

        # for pickinng files
        file_picker = ft.FilePicker(on_result=on_file_selected)

        plusw_choose_txt_file_btn = ft.ElevatedButton(
            text='Выбрать текстовый файл',
            on_click=lambda _: file_picker.pick_files()
        )
        view.controls.append(plusw_choose_txt_file_btn)

        page.overlay.append(file_picker)
        page.views.append(view)
        page.update()

    async def home_view(e: ft.ControlEvent = None):
        async def on_click_parse_entity(e: ft.ControlEvent):
            selected_session = page.session.get('selected_session')
            client = TelegramClient(selected_session, api_id=API_ID, api_hash=API_HASH, system_version=SYSTEM_VERSION)
            await client.connect()
            if not await client.is_user_authorized():
                print('ERROR')
                await client.disconnect()
                return

            # for the join the channel
            await client(JoinChannelRequest(e.control.id))
            await asyncio.sleep(5)

            # for all the information
            users_info_file = open(f'output/users_info_{dt.datetime.now()}.txt', 'a+')
            messages_info_file = open(f'output/messages_info_{dt.datetime.now()}.txt', 'a+')
            # for remembering what users was captured
            users_was_set = set()
            # the path for the result
            result_dir = f'users_avatars_{dt.datetime.now()}/' if not page.session.get(
                'result_dir') else page.session.get('result_dir') + '/'

            cnt = 0
            plusw = set() if not page.session.get('plusw') else set(page.session.get('plusw'))
            limit = 0
            try:
                if int(limit_for_parsing_field.value):
                    limit = int(limit_for_parsing_field.value)
            except:
                pass

            # create a text for the cnt
            cnt_parsing_text = ft.Text(
                color=ft.colors.GREEN,
                value=f'Парсинг в процессе - 0 сообщений.',
                visible=True
            )
            view.controls.append(cnt_parsing_text)
            page.update()

            async for message in client.iter_messages(e.control.id, limit=limit):
                try:
                    if message.text:
                        context_of_message = set(message.text.lower().split())
                    elif message.caption:
                        context_of_message = set(message.caption.lower().split())
                    else:
                        context_of_message = True

                    if set(context_of_message) & plusw or not plusw:

                        try:  # try to add the user's info
                            if message.sender.id not in users_was_set:
                                await client.download_profile_photo(message.sender, file=result_dir)
                                await asyncio.sleep(10)  # for not banning of flood
                                print(message.sender, file=users_info_file)  # for user info
                                print('-' * 15, file=users_info_file)
                                users_was_set.add(message.sender.id)
                        except Exception as exc:
                            print(exc)

                        try:  # try to add the message info
                            print(message, file=messages_info_file)
                            print('-' * 15, file=messages_info_file)
                        except Exception as exc:
                            print(exc)

                        try:
                            if message.media:
                                await client.download_media(message, file=result_dir)
                        except Exception as e:
                            print(e)

                        cnt += 1
                        cnt_parsing_text.value = f'Парсинг в процессе - {cnt} сообщений.'
                        page.update()
                except Exception as exc:
                    print(exc)

            print('parse is over; cnt = ', cnt)
            view.controls.remove(cnt_parsing_text)
            page.update()
            await asyncio.sleep(5)
            await client(LeaveChannelRequest(e.control.id))
            await client.disconnect()

        async def on_click_search(e: ft.ControlEvent):
            selected_phone = page.session.get('selected_session')
            client = TelegramClient(
                selected_phone, api_id=API_ID, api_hash=API_HASH, system_version=SYSTEM_VERSION)
            await client.connect()
            if not await client.is_user_authorized():
                print('Not auth!!!')
                return

            red_text = ft.Text(
                value='Идет поиск. Ничего не жать.',
                color=ft.colors.RED_400,
            )
            view.controls.append(red_text)
            page.update()

            # search
            result = await client(SearchRequest(
                q=search_query_field.value,
                limit=100,
            ))

            # add the things to the list_view
            cnt = 0
            for el in result.results:
                if isinstance(el, PeerChannel) or isinstance(el, PeerChat):
                    cnt += 1
                    try:
                        info_full = await client(GetFullChannelRequest(el))
                    except Exception as exc:
                        print(exc)
                        continue
                    print(info_full.chats[0].megagroup, '\n', '-' * 15, '\n')

                    # for all the megagroups that connected with channel
                    chats = []
                    for ch in info_full.chats:
                        if ch.megagroup:
                            chats.append(ch)

                    title = info_full.chats[0].title
                    info = info_full.full_chat

                    # get the photo info
                    photo = await client.download_profile_photo(info.id, file='photos/')

                    chat_list_view.controls.append(
                        tmpls.QResultElement(
                            id=info.id,
                            name=title,
                            image_src=photo,
                            parse_func=on_click_parse_entity,
                            megagroup=info_full.chats[0].megagroup,
                        )
                    )
                    page.update()

                    # for each megagroup
                    for mg in chats:
                        title = mg.title
                        id = mg.id
                        megagroup = mg.megagroup
                        photo = await client.download_profile_photo(id, file='photos/')

                        chat_list_view.controls.append(
                            tmpls.QResultElement(
                                id=id,
                                name=title,
                                image_src=photo,
                                parse_func=on_click_parse_entity,
                                megagroup=megagroup,
                            )
                        )
                        page.update()
                        cnt += 1

            await client.disconnect()
            red_text.value = f'Найдено {cnt}. Как только это сообщение исчезнет - можете работать.'
            page.update()
            await asyncio.sleep(2)
            view.controls.remove(red_text)
            page.update()

        async def on_click_clear_list_view(e: ft.ControlEvent = None):
            chat_list_view.clean()

        async def on_choose_result_dir(e: ft.FilePickerResultEvent = None):
            page.session.set('result_dir', e.path)
            result_dir_text.value = e.path
            page.update()

        page.clean()
        view = ft.View(controls=[])

        # получаем все данные о сессиях
        db = AsyncSQLiteSessionDB()
        await db.connect()
        sessions = await db.get_all_sessions()
        view.controls.append(await tmpls.main_sessions_list(page, sessions, select_the_session))
        await db.disconnect()

        # add the add session btn
        view.controls.append(
            ft.ElevatedButton(
                text='Добавить аккаунт сессии',
                on_click=create_session,
                width=200,
                height=60,
                bgcolor=ft.colors.WHITE12,
            )
        )

        # if there are a selected session
        if page.session.contains_key('selected_session'):
            # add the divider
            view.controls.append(
                ft.Divider(
                    thickness=5,
                    color=ft.colors.RED_400,
                    leading_indent=10,
                    trailing_indent=10,
                )
            )

            # add the h1
            view.controls.append(ft.Row(controls=[ft.Text(
                value='Поиск групп и чатов',
                color=ft.colors.BLUE_400,
                size=40,
            )]))

            # THE SEARCH
            # add the left_block elements
            h4_search = ft.Text(
                value='Поиск',
                color=ft.colors.PURPLE_200,
                size=18
            )
            search_query_field = ft.TextField(
                label='Введите сюда ваш запрос для поиска')
            search_btn = ft.ElevatedButton(
                text='Искать',
                icon=ft.icons.SEARCH,
                icon_color=ft.colors.AMBER_400,
                color=ft.colors.BLUE_300,
                bgcolor=ft.colors.WHITE12,
                on_click=on_click_search,
            )

            plusw_view_btn = ft.ElevatedButton(
                text='Начать добавлять слова',
                icon=ft.icons.ADD,
                icon_color=ft.colors.AMBER_200,
                on_click=plusw_view,
            )

            # for THE PATH OF DIRECTORY
            h4_path_of_dir = ft.Text(
                value='Текущая директория для сохранения',
                color=ft.colors.PURPLE_200,
                size=18,
            )
            result_dir = page.session.get('result_dir')
            result_dir_text = ft.Text(
                value=result_dir,
                size=12,
            )

            # for the dir picker
            result_dir_picker = ft.FilePicker(on_result=on_choose_result_dir)
            page.overlay.append(result_dir_picker)

            specify_dir_btn = ft.ElevatedButton(
                text='Выберите директория для вывода',
                bgcolor=ft.colors.WHITE12,
                icon=ft.icons.STORE_MALL_DIRECTORY_ROUNDED,
                icon_color=ft.colors.AMBER_200,
                on_click=lambda _: result_dir_picker.get_directory_path()
            )

            h4_limit_for_parsing = ft.Text(
                value='Лимит сообщений для парсинга',
                color=ft.colors.PURPLE_200,
                size=18
            )
            limit_for_parsing_field = ft.TextField(
                label='Введите сюда количество сообщений',
            )

            left_block_elems = ft.Column(controls=[
                h4_search,
                search_query_field,
                search_btn,
                plusw_view_btn,
                h4_path_of_dir,
                result_dir_text,
                specify_dir_btn,
                h4_limit_for_parsing,
                limit_for_parsing_field,
            ])

            left_block = ft.Container(  # create a left container
                content=left_block_elems,
                border=ft.border.all(2, ft.colors.WHITE12),
                border_radius=10,
                padding=10,
                width=600,
                height=600,
            )

            # create a right block
            h4_finded_chats = ft.Text(
                value='Найденные чаты',
                color=ft.colors.PURPLE_200,
                size=18
            )
            chat_list_view = ft.ListView(
                width=600,
                height=500,
                spacing=10,
                padding=10,
                auto_scroll=False,
                expand=True,
            )
            clear_list_view_btn = ft.ElevatedButton(
                text='Очистить',
                bgcolor=ft.colors.WHITE12,
                on_click=on_click_clear_list_view
            )
            right_block_elems = ft.Column(controls=[
                h4_finded_chats,
                chat_list_view,
                clear_list_view_btn
            ])
            right_block = ft.Container(
                content=right_block_elems,
                border=ft.border.all(2, ft.colors.WHITE12),
                border_radius=10,
                padding=10,
                width=650,
                height=550
            )

            # add the hole row
            view.controls.append(ft.Row(
                controls=[left_block, right_block],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            ))

        page.views.append(view)
        page.update()

    async def create_session(e: ft.ControlEvent = None):

        async def verify_code(e):
            global client
            try:
                await client.sign_in(
                    phone=phone_number.value,
                    code=code.value
                )
                view.controls.append(success_login_text)

                # add the acc to db
                db = AsyncSQLiteSessionDB()
                await db.connect()
                await db.insert_session(phone_number.value)
                await db.disconnect()

                await client.disconnect()
            except Exception as e:
                print(e)
            page.update()

        async def send_code(e):
            global client
            client = TelegramClient(
                phone_number.value, API_ID, API_HASH, system_version=SYSTEM_VERSION
            )

            try:  # try to connect
                await client.connect()
            except Exception as e:
                print(e)

            if await client.is_user_authorized():  # if where session file
                view.controls.append(account_exists_text)
            else:
                # send the code
                try:
                    await client.send_code_request(phone_number.value)
                except Exception as e:
                    print(e)

                view.controls.append(
                    ft.Text('Код отправлен',
                            color=ft.colors.BLUE_200, size=24)
                )
                code.visible = True
                verify_code_btn.visible = True

            page.update()

        page.clean()
        view = ft.View(controls=[])

        # add the back btn
        view.controls.append(ft.Row(controls=[
            ft.Column(controls=[await tmpls.back_to_home_btn(home_view)])
        ]))

        # add the inputs
        phone_number = ft.TextField(label='Введите номер аккаунта')
        code = ft.TextField(label='Введите код из телеграма', visible=False)
        send_code_btn = ft.TextButton(
            text='Отправить код в тг',
            on_click=send_code
        )
        verify_code_btn = ft.TextButton(
            text='Подтвердить код',
            on_click=verify_code,
            visible=False
        )
        success_login_text = ft.Text(
            value='Вы успешно залогинились',
            color=ft.colors.GREEN_200,
            size=40,
        )
        account_exists_text = ft.Text(
            'ТАКОЙ АККАУНТ УЖЕ ЕСТЬ!',
            color=ft.colors.RED_200, size=36
        )

        view.controls.append(
            ft.Row(controls=[
                ft.Column(controls=[
                    phone_number, send_code_btn
                ])
            ])
        )
        view.controls.append(
            ft.Row(controls=[
                ft.Column(controls=[
                    code, verify_code_btn
                ])
            ])
        )

        page.views.append(view)
        page.update()

    async def select_the_session(e: ft.ControlEvent = None):
        if page.session.contains_key('selected_session') and page.session.get('selected_session') == e.control.text:
            page.session.remove('selected_session')
        else:
            page.session.set('selected_session', e.control.text)
        await home_view()

    # first deploy
    page.window.prevent_close = True
    page.window.on_event = on_window_event_custom
    await home_view()


if __name__ == "__main__":
    ft.app(main)
