import flet as ft
from typing import Callable


async def back_to_home_btn(home: Callable):
    return ft.TextButton(
        text='Назад',
        animate_size=24,
        on_click=home
    )
