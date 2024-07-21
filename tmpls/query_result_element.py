import flet as ft
from typing import Callable


class ParseEventButton(ft.ElevatedButton):
    def __init__(self, text: str, on_click: Callable, id: str | int):
        super().__init__()
        self.id = id
        self.text = text
        self.on_click = on_click


class QResultElement(ft.Container):
    def __init__(self, id: int, name: str, image_src: str | None, parse_func: Callable, megagroup: bool) -> None:
        super().__init__()
        self.id = id

        # the image of entity
        if image_src:
            self.image = ft.Image(
                src=image_src,
                width=20,
                height=20,
                fit=ft.ImageFit.CONTAIN
            )
        else:
            self.image = ft.Text(value='no pic', size=8)

        # name text
        self.name_txt = ft.Text(
            value=name,
            size=14,
            bgcolor=ft.colors.WHITE12 if not megagroup else ft.colors.ORANGE
        )

        # button
        self.scrap_btn = ParseEventButton(
            text='Спарсить данные',
            on_click=parse_func,
            id=id,
        )

        row = ft.Row(
            controls=[
                self.image, self.name_txt, self.scrap_btn
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,

        )

        self.content = row
