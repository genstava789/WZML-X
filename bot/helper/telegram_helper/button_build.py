from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ButtonMaker:
    def __init__(self):
        self.buttons = {
            "default": [],
            "header": [],
            "footer": []
        }

    def url_button(self, key, link, position=None):
        position = position if position in self.buttons else "default"
        self.buttons[position].append(InlineKeyboardButton(text=key, url=link))

    def data_button(self, key, data, position=None):
        position = position if position in self.buttons else "default"
        self.buttons[position].append(InlineKeyboardButton(text=key, callback_data=data))

    def build_menu(self, b_cols=1, h_cols=8, f_cols=8):
        menu = [
            self.buttons["default"][i: i + b_cols] for i in range(0, len(self.buttons["default"]), b_cols)
        ]
        
        if self.buttons["header"]:
            h_cnt = len(self.buttons["header"])
            if h_cnt > h_cols:
                header_buttons = [
                    self.buttons["header"][i: i + h_cols]
                    for i in range(0, len(self.buttons["header"]), h_cols)
                ]
                menu = header_buttons + menu
            else:
                menu.insert(0, self.buttons["header"])
        
        if self.buttons["footer"]:
            if len(self.buttons["footer"]) > f_cols:
                [
                    menu.append(self.buttons["footer"][i: i + f_cols])
                    for i in range(0, len(self.buttons["footer"]), f_cols)
                ]
            else:
                menu.append(self.buttons["footer"])
        
        return InlineKeyboardMarkup(menu)

    def reset(self):
        self.buttons = {
            "default": [],
            "header": [],
            "footer": []
        }
