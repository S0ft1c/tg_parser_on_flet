import flet as ft
from typing import Callable


async def main_sessions_list(page: ft.Page, sessions: list, activate_session: Callable) -> ft.Row:

    sessions_list = ft.Row(controls=[])
    for el in sessions:
        if page.session.contains_key('selected_session') and el[1] == page.session.get('selected_session'):
            sessions_list.controls.append(
                ft.Column(controls=[
                    ft.ElevatedButton(
                        text=el[1],
                        icon_color=ft.colors.AMBER_200,
                        icon=ft.icons.PHONE,
                        width=200,
                        height=60,
                        on_click=activate_session,
                        data=el[1],
                        bgcolor=ft.colors.GREEN_800,
                    )
                ])
            )
        else:
            sessions_list.controls.append(
                ft.Column(controls=[
                    ft.ElevatedButton(
                        text=el[1],
                        icon_color=ft.colors.AMBER_200,
                        icon=ft.icons.PHONE,
                        width=200,
                        height=60,
                        on_click=activate_session,
                        data=el[1],
                    )
                ])
            )
    if not sessions_list.controls:
        sessions_list.controls.append(
            ft.Column(controls=[
                ft.Text(value='Пока тут ничего нет...', size=24)
            ])
        )
    return sessions_list
