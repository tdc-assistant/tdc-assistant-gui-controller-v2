from typing import Any, Union, Optional

from time import sleep

from pywinauto import mouse  # type: ignore

from tdc_assistant_gui_controller_v2.code_editor.types.code_editor import CodeEditor
from tdc_assistant_gui_controller_v2.windows.window_exception import WindowException
from tdc_assistant_gui_controller_v2.word_processor.word_processor import WordProcessor

from ..logger import Logger
from ..types import Coordinate, AWSCredentials, Screenshare
from ..public_chat import PublicChat

from .open_all_windows import open_all_windows
from .public_chat_window_controller import PublicChatWindowController
from .code_editor_window_controller import CodeEditorWindowController
from .screenshare_window_controller import ScreenshareWindowController
from .code_editor_window_controller import CodeEditorWindowController
from .word_processor_window_controller import WordProcessorWindowController

from ..types import WindowTitle
from .get_first_window import get_first_window

WindowController = Union[
    PublicChatWindowController,
    CodeEditorWindowController,
    ScreenshareWindowController,
    WordProcessorWindowController,
]

code_editor_window_titles = [
    WindowTitle.C_LIKE_EDITOR,
    WindowTitle.CSS_EDITOR,
    WindowTitle.GO_EDITOR,
    WindowTitle.HTML_EDITOR,
    WindowTitle.JAVA_EDITOR,
    WindowTitle.JAVASCRIPT_EDITOR,
    WindowTitle.MATHEMATICA_EDITOR,
    WindowTitle.PHP_EDITOR,
    WindowTitle.PYTHON_EDITOR,
    WindowTitle.R_EDITOR,
    WindowTitle.RUBY_EDITOR,
    WindowTitle.SQL_EDITOR,
    WindowTitle.XML_EDITOR,
]


class WindowManager:
    _right_pop_out_button_coords: Coordinate
    _public_chat_text_box_coords: Coordinate
    _end_session_button_coords: Coordinate
    _confirm_end_session_button_coords: Coordinate
    _tutor_first_name: str
    _tutor_last_initial: str
    _aws_credentials: AWSCredentials
    _window_controllers: list[WindowController]
    _logger: Logger

    def __init__(
        self,
        aws_credentials: AWSCredentials,
        right_pop_out_button_coords: Coordinate,
        public_chat_text_box_coords: Coordinate,
        end_session_button_coords: Coordinate,
        confirm_end_session_button_coords: Coordinate,
        tutor_first_name: str,
        tutor_last_initial: str,
    ):
        self._aws_credentials = aws_credentials
        self._right_pop_out_button_coords = right_pop_out_button_coords
        self._public_chat_text_box_coords = public_chat_text_box_coords
        self._end_session_button_coords = end_session_button_coords
        self._confirm_end_session_button_coords = confirm_end_session_button_coords
        self._tutor_first_name = tutor_first_name
        self._tutor_last_initial = tutor_last_initial
        self._window_controllers = []
        self._logger = Logger(self)

    def open_all_windows(self):
        open_all_windows_start = self._logger.log("Started opening all windows")
        for window in open_all_windows(self._right_pop_out_button_coords):
            controller = self._map_window_to_controller(window)

            if controller is not None:
                for existing_controller in self._window_controllers:
                    if (
                        existing_controller.get_window_title()
                        == controller.get_window_title()
                    ):
                        break
                else:
                    controller.maximize_window()
                    self._window_controllers.append(controller)
            else:
                self._logger.log_warning(
                    f"No controller exists for Window: '{window.window_text()}'"
                )

        open_all_windows_end = self._logger.log("Finished opening all windows")
        self._logger.log_elapsed_time(open_all_windows_start, open_all_windows_end)

    def _parse_programming_language_and_editor_number(
        self, window_title: str
    ) -> tuple[str, int]:
        editor_index = window_title.index("Editor")
        programming_language = window_title[:editor_index].strip()
        editor_number = int(
            window_title[editor_index + len("Editor") :].split()[0].strip()
        )
        return programming_language, editor_number

    def _parse_word_processor_number(self, window_title: str) -> int:
        return int(window_title[len("word processor") :].split()[0].strip())

    def _map_window_to_controller(self, window: Any) -> Optional[WindowController]:
        try:
            window_text = window.window_text()
        except:
            raise WindowException()
        if WindowTitle.PUBLIC_CHAT.value.lower() in window_text.lower():
            return PublicChatWindowController(
                window, self._tutor_first_name, self._tutor_last_initial
            )
        for code_editor_window_title in code_editor_window_titles:
            if code_editor_window_title.value.lower() in window_text.lower():
                (
                    programming_language,
                    editor_number,
                ) = self._parse_programming_language_and_editor_number(window_text)
                return CodeEditorWindowController(
                    window, programming_language, editor_number
                )
        if WindowTitle.SCREENSHARE.value.lower() in window_text.lower():
            return ScreenshareWindowController(window, self._aws_credentials)
        if WindowTitle.WORD_PROCESSOR.value.lower() in window_text.lower():
            return WordProcessorWindowController(
                window,
                number=self._parse_word_processor_number(window_text.lower().strip()),
            )
        return None

    def find_public_chat_window_controller(
        self,
    ) -> Optional[PublicChatWindowController]:
        self.open_all_windows()

        for controller in self._window_controllers:
            if isinstance(controller, PublicChatWindowController):
                return controller

        return None

    def find_screenshare_window_controller(
        self,
    ) -> Optional[ScreenshareWindowController]:
        self.open_all_windows()

        for controller in self._window_controllers:
            if isinstance(controller, ScreenshareWindowController):
                return controller

        return None

    def find_code_editor_window_controller(
        self, editor_language: str, editor_number: int
    ) -> Optional[CodeEditorWindowController]:
        self.open_all_windows()

        for controller in self._window_controllers:
            if isinstance(controller, CodeEditorWindowController):
                if (
                    editor_language == controller._programming_language
                    and editor_number == controller._editor_number
                ):
                    return controller

        return None

    def find_window_processor_window_controller(self, number: int):
        self.open_all_windows()

        for controller in self._window_controllers:
            if isinstance(controller, WordProcessorWindowController):
                if controller._number == number:
                    return controller

        return None

    def scrape_public_chat(self) -> PublicChat:
        controller = self.find_public_chat_window_controller()

        if controller is None:
            raise Exception(f"Cannot find {WindowTitle.PUBLIC_CHAT.value} window")

        return controller.scrape()

    def scrape_code_editors(self) -> list[CodeEditor]:
        self.open_all_windows()

        code_editors: list[CodeEditor] = []

        for controller in self._window_controllers:
            if isinstance(controller, CodeEditorWindowController):
                code_editors.append(controller.scrape())

        return code_editors

    def send_message(self, message: str):
        controller = self.find_public_chat_window_controller()

        if controller is None:
            raise Exception(f"Cannot find {WindowTitle.PUBLIC_CHAT.value} window")

        controller.send_message(
            message,
            (
                self._public_chat_text_box_coords["x"],
                self._public_chat_text_box_coords["y"],
            ),
        )

    def scrape_screenshare(self) -> Optional[Screenshare]:
        controller = self.find_screenshare_window_controller()

        if controller is None:
            print("cannot find screenshare window")
            return None

        return controller.scrape()

    def is_screenshare_window_open(self) -> bool:
        return self.find_screenshare_window_controller() is not None

    def send_text_to_code_editor(
        self, editor_language: str, editor_number: int, text: str
    ):
        start = self._logger.log("Started finding code editor window controller")
        optional_controller = self.find_code_editor_window_controller(
            editor_language, editor_number
        )
        end = self._logger.log("Finished finding code editor window controller")
        self._logger.log_elapsed_time(start, end)

        if optional_controller is None:
            self._logger.log_warning("Cannot find code editor window controller")
            return None

        optional_controller.send_text(text)

    def scrape_word_processors(self) -> list[WordProcessor]:
        self.open_all_windows()

        word_processors: list[WordProcessor] = []

        for controller in self._window_controllers:
            if isinstance(controller, WordProcessorWindowController):
                word_processors.append(controller.scrape())

        return word_processors

    def end_session(self) -> None:
        optional_classroom_window = get_first_window(WindowTitle.CLASSROOM)

        if optional_classroom_window is not None:
            optional_classroom_window.set_focus()

        mouse.move(
            coords=(
                self._end_session_button_coords["x"],
                self._end_session_button_coords["y"],
            )
        )

        sleep(1)

        mouse.click(
            coords=(
                self._end_session_button_coords["x"],
                self._end_session_button_coords["y"],
            )
        )

        sleep(1)

        mouse.move(
            coords=(
                self._confirm_end_session_button_coords["x"],
                self._confirm_end_session_button_coords["y"],
            )
        )

        sleep(1)

        mouse.click(
            coords=(
                self._confirm_end_session_button_coords["x"],
                self._confirm_end_session_button_coords["y"],
            )
        )
