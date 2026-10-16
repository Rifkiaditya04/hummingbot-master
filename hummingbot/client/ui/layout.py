from os.path import dirname, join, realpath
from pathlib import Path
from typing import Dict

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer
from prompt_toolkit.layout import Dimension
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.widgets import Box, Button, SearchToolbar

from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.client.settings import (
    CONTROLLERS_CONF_DIR_PATH,
    MAXIMUM_LOG_PANE_LINE_COUNT,
    MAXIMUM_OUTPUT_PANE_LINE_COUNT,
    SCRIPT_STRATEGY_CONF_DIR_PATH,
)
from hummingbot.client.tab.data_types import CommandTab
from hummingbot.client.ui.custom_widgets import CustomTextArea as TextArea, FormattedTextLexer


HEADER = """
⠀⠀⠀⠀⠀⠀⣀⣤⣶⣶⣿⢿⣿⣿⣷⣶⣦⣤⡀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀ ⢰⣤⡀⠀
⠀⠀⢾⡻⣶⣾⣿⣿⣛⣻⣮⡉⣿⣿⣿⠟⠋⠉⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀ ⠈⣿⣿⣦
⠀⠀⢸⢿⢿⣿⡿⠁⣀⠀⢛⣿⣿⣿⣷⣦⣄⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀ ⣀⡘⣿⣿⣷⡰⣶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⣶⠟⠁
⠀⠀⢸⠈⣿⣿⠁⠀⣿⡇⢸⡏⢻⣿⣿⣿⣿⣷⡄⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣔⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⢻⣿⣿⣌⢿⣿⣷⣭⣤⣤⣤⣤⣄⣀⠀⠀⠀⣠⣶⣿⣿⡿⠃
⠀⠀⢰⣦⣝⠁⡀⠀⢙⠡⠚⠣⣾⣿⡿⠿⠿⠿⢿⡄   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⣿⡿⣿⣇⣽⣿⠀⠀⠀⡀⣠⠤⠄   ⠀⠀ ⢸⣿⣿⣿⢎⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣿⣿⣿⠟⠉
⠀⠀⠀⠈⠡⡀⠀⠀⠀⠄⠚⣰⣿⣿⣷⡄⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠿⣿⡿⡿⠟⠁⢀⡴⠿⣵⣿⠛⠀⠀   ⠀⠀ ⣸⠛⠉⢀⣿⣿⠋⣭⢿⣿⣿⣿⡿⠻⣿⣿⡿⠋
⠀⠀⠀⢀⡔⡈⡲⠂⠰⠶⢟⡉⠿⢿⣿⣧⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣆⠄⣀⣿⣾⡯⠝⠃⠀⠀⠀⠀   ⢰⣿⣿⣶⡆⠻⠿⣿⣦⣤⣾⡿⣿⣧⠛⢀⣿⣿⡇
⠀⠀⠀⠫⣓⠣⢀⡣⡀⠀⡔⣹⣧⠀⠉⠃⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣛⠚⠛⢤⠄⢸⣿⣿⣷⣿⣍⡀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠻⣿⣿⣿⠀⢀⣿⣿⣿⠟⠛⢿⣿⣿⣿⣿⣿⡇⣠⣤⣤⣤
⠀⠀⠀⠀⠑⢄⣀⣀⣶⣶⠟⠛⠿⡀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⢿⣷⣦⣀⠹⣦⣿⣹⣿⣧⠹⢯⣿⣆⡀⠀⠀⠀⠀⠀  ⠀  ⠈⠻⣿⣦⡻⣿⣿⣿⡇⠀⣰⣿⣿⣿⡏⠀⢀⣿⣿⣿⠟
⠀⠀⠀⠀⠀⠀⣿⡏⢿⡏⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⢇⣀⡹⢿⣿⣷⣮⣝⢷⣝⣿⠀⠀⠀⠀⠈⠁⠀⠀⠀   ⠀⠀⠀⠀  ⣿⣿⣿⣮⣛⠿⠷⣾⣿⣿⡿⠿⣣⣴⡿⠟⠋⠀
⠀⠀⠀⠀⢠⠉⠻⠏⣺⣷⠔⡄⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⣀⣀⢤⣼⣿⢿⡷⠟⠿⣿⣷⣟⢿⣿⣼⣷⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀ ⣿⣿⣿⣿⣿⣿⣷⣶⣶⣶⣶⣿⣿⡟
⠀⠀⢀⣤⡒⢤⣀⡆⠀⠀⠀⢐⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⢀⣠⣴⡶⢛⣻⡽⠛⠛⠓⠉⠁⠀⠀⠈⠙⠻⢿⣝⢥⣿⣿⣿⣿⣿⣤⡀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀ ⢼⡿⠙⠿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠏
⢀⡾⣋⣵⣾⡀⣿⣿⣶⢂⡌⣍⠆⠀⠀⠀⠀⠀⠀⠀   ⠚⠛⠛⢯⡷⠿⠿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠋⠙⣛⣿⡛⠋⠷⠄⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠛⠛⠋⠉⠺⠷
⠘⠛⠛⠛⠛⠃⠉⠙⢏⣾⣧⢹⣿⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠿⣾⢸                      ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀					

█ █  █  █ █  █  ██  ██   █  ██  ███ ███  █  ██  ██  ███
███ █ █ █ █ █ █ █ █ █ █ █ █ █ █  █   █  █ █ █ █ █ █  █ 
█ █ ███  █  ███ ██  ██  ███ █ █  █   █  ███ ██  █ █  █ 
█ █ █ █  █  █ █ █   █ █ █ █ █ █  █   █  █ █ █ █ █ █  █ 
█ █ █ █  █  █ █ █   █ █ █ █ ██  ███  █  █ █ ██  ██   █ 
                     MAYAPRADITABOT

======================================================================================

Production Dashboard
- Mode: Binance spot paper trade
- Pair: BTC-USDT
- Timeframe: 5m
- Style: High confidence, selective entry
- Risk: Closed candle signal only

Quick Commands
- help all -> show every available command and usage
- connect -> configure/connect exchange API keys
- balance -> show balances for connected exchanges
- config -> view or edit bot configuration
- create -> create a new strategy/config workflow
- start -> start the selected strategy
- stop -> stop the running strategy
- status -> show live bot and network status
- history -> show trade history and performance report
- import -> load a saved config file
- export -> export keys or trade data
- rate -> show the current oracle/market rate
- ticker -> show latest ticker data for a pair
- order_book -> open the order book view
- mqtt -> manage MQTT bridge commands
- gateway -> gateway overview and configuration
- exit -> close Hummingbot

"""
with open(realpath(join(dirname(__file__), '../../VERSION'))) as version_file:
    version = version_file.read().strip()


def _repair_legacy_unicode(text: str) -> str:
    """Repair the old UTF-8-as-Windows-1252 header without rewriting source art."""
    cp1252_special = {
        "€": 0x80, "‚": 0x82, "ƒ": 0x83, "„": 0x84, "…": 0x85,
        "†": 0x86, "‡": 0x87, "ˆ": 0x88, "‰": 0x89, "Š": 0x8A,
        "‹": 0x8B, "Œ": 0x8C, "Ž": 0x8E, "‘": 0x91, "’": 0x92,
        "“": 0x93, "”": 0x94, "•": 0x95, "–": 0x96, "—": 0x97,
        "˜": 0x98, "™": 0x99, "š": 0x9A, "›": 0x9B, "œ": 0x9C,
        "ž": 0x9E, "Ÿ": 0x9F,
    }
    raw = bytearray()
    for char in text:
        codepoint = ord(char)
        if codepoint <= 0xFF:
            raw.append(codepoint)
        elif char in cp1252_special:
            raw.append(cp1252_special[char])
        else:
            raw.extend(char.encode("utf-8"))
    try:
        return bytes(raw).decode("utf-8")
    except UnicodeDecodeError:
        return text


def _brand_title() -> str:
    """Render the large spaced title without changing the artwork above it."""
    font = {
        "M": ["█  █", "████", "█ ██", "█  █", "█  █"],
        "A": [" ██ ", "█  █", "████", "█  █", "█  █"],
        "Y": ["█  █", "█  █", " ██ ", " ██ ", " ██ "],
        "P": ["███ ", "█  █", "███ ", "█   ", "█   "],
        "R": ["███ ", "█  █", "███ ", "█ █ ", "█  █"],
        "D": ["███ ", "█  █", "█  █", "█  █", "███ "],
        "I": ["████", " ██ ", " ██ ", " ██ ", "████"],
        "T": ["████", " ██ ", " ██ ", " ██ ", " ██ "],
        "B": ["███ ", "█  █", "███ ", "█  █", "███ "],
        "O": [" ██ ", "█  █", "█  █", "█  █", " ██ "],
        " ": ["    ", "    ", "    ", "    ", "    "],
    }
    return "\n".join(
        " ".join(font[char][row] for char in "MAYA PRADITA  BOT")
        for row in range(5)
    )


def get_static_header() -> str:
    """Return the fixed art/title block; this container is intentionally not scrollable."""
    repaired = _repair_legacy_unicode(HEADER)
    art_lines = [line.rstrip() for line in repaired.splitlines() if line.strip()][:15]
    separator = "=" * 86
    subtitle = "MAYA PRADITA BOT".center(len(separator))
    return "\n".join(art_lines + ["", _brand_title(), subtitle, "", separator])


def _strategy_dashboard_values() -> Dict[str, str]:
    values = {
        "mode": "Belum ditentukan",
        "pair": "BTC-USDT",
        "timeframe": "5m",
        "style": "Entry selektif, konfirmasi tinggi",
        "risk": "Sinyal candle yang sudah ditutup",
        "status": "Menunggu start strategi",
    }
    try:
        from hummingbot.client.hummingbot_application import HummingbotApplication
        hb = HummingbotApplication.main_application()
        strategy_file = (hb.strategy_file_name or "").lower()
        values["mode"] = (
            "Binance Spot Demo" if "demo" in strategy_file else
            "Binance Spot Paper" if "paper" in strategy_file else
            "Binance Spot"
        )
        values["status"] = "Strategi aktif" if hb.strategy_name else values["status"]
        if strategy_file:
            script_path = SCRIPT_STRATEGY_CONF_DIR_PATH / Path(strategy_file).name
            if script_path.exists():
                import yaml
                script_data = yaml.safe_load(script_path.read_text(encoding="utf-8")) or {}
                controller_names = script_data.get("controllers_config", [])
                if controller_names:
                    controller_path = CONTROLLERS_CONF_DIR_PATH / Path(controller_names[0]).name
                    controller_data = yaml.safe_load(controller_path.read_text(encoding="utf-8")) or {}
                    values["pair"] = controller_data.get("trading_pair", values["pair"])
                    values["timeframe"] = controller_data.get("interval", values["timeframe"])
    except Exception:
        pass
    return values


def get_dashboard_text() -> str:
    values = _strategy_dashboard_values()
    commands = [
        ("help all", "tampilkan semua bantuan"),
        ("connect", "atur koneksi API exchange"),
        ("balance", "lihat saldo exchange"),
        ("config", "lihat/ubah konfigurasi"),
        ("create", "buat konfigurasi strategi"),
        ("start", "jalankan strategi"),
        ("stop", "hentikan strategi"),
        ("status", "lihat status bot dan jaringan"),
        ("history", "lihat riwayat dan laporan trade"),
        ("import", "muat file konfigurasi"),
        ("export", "ekspor data atau key"),
        ("rate", "lihat harga dari rate oracle"),
        ("ticker", "lihat harga ticker pair"),
        ("order_book", "lihat order book"),
        ("mqtt", "kelola perintah MQTT"),
        ("gateway", "lihat konfigurasi Gateway"),
        ("exit", "tutup Hummingbot"),
    ]
    split = (len(commands) + 1) // 2
    left, right = commands[:split], commands[split:]
    command_rows = [
        f"- {left[index][0]:<12} {left[index][1]:<30} | "
        f"{right[index][0]:<12} {right[index][1]}"
        for index in range(len(right))
    ]
    return "\n".join([
        "Panel Produksi",
        f"- Mode: {values['mode']}",
        f"- Pair: {values['pair']}",
        f"- Timeframe: {values['timeframe']}",
        f"- Gaya: {values['style']}",
        f"- Risiko: {values['risk']}",
        f"- Status: {values['status']}",
        "",
        "Perintah Cepat",
        *command_rows,
        "",
    ])


def create_header_field():
    return Window(
        FormattedTextControl(get_static_header),
        # Keep the branding fixed, but allow compact terminals to shrink it.
        height=Dimension(min=1, preferred=23, max=23),
        dont_extend_height=True,
        style="class:output_field",
    )


def create_dashboard_field():
    return Window(
        FormattedTextControl(get_dashboard_text),
        height=Dimension(min=1, preferred=16, max=16),
        dont_extend_height=True,
        style="class:output_field",
    )


def create_input_field(lexer=None, completer: Completer = None):
    return TextArea(
        height=3,
        prompt='>>> ',
        style='class:input_field',
        multiline=False,
        focus_on_click=True,
        lexer=lexer,
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        complete_while_typing=True,
    )


def create_output_field(client_config_map: ClientConfigAdapter):
    return TextArea(
        style='class:output_field',
        focus_on_click=True,
        read_only=True,
        scrollbar=True,
        max_line_count=MAXIMUM_OUTPUT_PANE_LINE_COUNT,
        initial_text="\n\nNotifikasi BUY/SELL akan tampil di sini.\n",
        lexer=FormattedTextLexer(client_config_map)
    )


def create_timer():
    return TextArea(
        style='class:footer',
        focus_on_click=False,
        read_only=False,
        scrollbar=False,
        max_line_count=1,
        width=30,
    )


def create_process_monitor():
    return TextArea(
        style='class:footer',
        focus_on_click=False,
        read_only=False,
        scrollbar=False,
        max_line_count=1,
        align=WindowAlign.RIGHT
    )


def create_trade_monitor():
    return TextArea(
        style='class:footer',
        focus_on_click=False,
        read_only=False,
        scrollbar=False,
        max_line_count=1,
    )


def create_search_field() -> SearchToolbar:
    return SearchToolbar(text_if_not_searching=[('class:primary', "[CTRL + F] to start searching.")],
                         forward_search_prompt=[('class:primary', "Search logs [Press CTRL + F to hide search] >>> ")],
                         ignore_case=True)


def create_log_field(search_field: SearchToolbar):
    return TextArea(
        style='class:log_field',
        text="Running Logs\n",
        focus_on_click=False,
        read_only=False,
        scrollbar=True,
        max_line_count=MAXIMUM_LOG_PANE_LINE_COUNT,
        initial_text="Running Logs \n",
        search_field=search_field,
        preview_search=False,
    )


def create_live_field():
    return TextArea(
        style='class:log_field',
        focus_on_click=False,
        read_only=False,
        scrollbar=True,
        max_line_count=MAXIMUM_OUTPUT_PANE_LINE_COUNT,
    )


def create_log_toggle(function):
    return Button(
        text='> Ctrl+T',
        width=10,
        handler=function,
        left_symbol='',
        right_symbol='',
    )


def create_tab_button(text, function, margin=2, left_symbol=' ', right_symbol=' '):
    return Button(
        text=text,
        width=len(text) + margin,
        handler=function,
        left_symbol=left_symbol,
        right_symbol=right_symbol
    )


def get_version():
    return [("class:header", f"Version: {version}")]


def get_active_strategy():
    from hummingbot.client.hummingbot_application import HummingbotApplication
    hb = HummingbotApplication.main_application()
    style = "class:log_field"
    return [(style, f"Strategy: {hb.strategy_name}")]


def get_strategy_file():
    from hummingbot.client.hummingbot_application import HummingbotApplication
    hb = HummingbotApplication.main_application()
    style = "class:log_field"
    return [(style, f"Strategy File: {hb.strategy_file_name}")]


def get_gateway_status():
    from hummingbot.client.hummingbot_application import HummingbotApplication
    hb = HummingbotApplication.main_application()
    gateway_status = hb.trading_core.gateway_monitor.gateway_status.name
    style = "class:log_field"

    # Check if SSL is enabled
    use_ssl = getattr(hb.client_config_map.gateway, "gateway_use_ssl", False)
    lock_icon = "ðŸ”’ " if use_ssl else ""

    # Add visual indicator based on status
    if gateway_status == "ONLINE":
        status_display = f"ðŸŸ¢ {gateway_status}"
    else:
        status_display = f"ðŸ”´ {gateway_status}"

    return [(style, f"{lock_icon}Gateway: {status_display}")]


def generate_layout(input_field: TextArea,
                    output_field: TextArea,
                    header_field,
                    dashboard_field,
                    log_field: TextArea,
                    right_pane_toggle: Button,
                    log_field_button: Button,
                    search_field: SearchToolbar,
                    timer: TextArea,
                    process_monitor: TextArea,
                    trade_monitor: TextArea,
                    command_tabs: Dict[str, CommandTab],
                    ):
    components = {}

    components["item_top_version"] = Window(FormattedTextControl(get_version), style="class:header")
    components["item_top_active"] = Window(FormattedTextControl(get_active_strategy), style="class:header")
    components["item_top_file"] = Window(FormattedTextControl(get_strategy_file), style="class:header")
    components["item_top_gateway"] = Window(FormattedTextControl(get_gateway_status), style="class:header")
    components["item_top_toggle"] = right_pane_toggle
    components["pane_top"] = VSplit([components["item_top_version"],
                                     components["item_top_active"],
                                     components["item_top_file"],
                                     components["item_top_gateway"],
                                     components["item_top_toggle"]], height=1)
    components["pane_bottom"] = VSplit([trade_monitor,
                                        process_monitor,
                                        timer], height=1)
    output_pane = Box(body=output_field, padding=0, padding_left=2, style="class:output_field")
    input_pane = Box(body=input_field, padding=0, padding_left=2, padding_top=1, style="class:input_field")
    components["pane_left"] = HSplit([
        header_field,
        dashboard_field,
        output_pane,
        input_pane,
    ], width=Dimension(weight=1))
    if all(not t.is_selected for t in command_tabs.values()):
        log_field_button.window.style = "class:tab_button.focused"
    else:
        log_field_button.window.style = "class:tab_button"
    tab_buttons = [log_field_button]
    for tab in sorted(command_tabs.values(), key=lambda x: x.tab_index):
        if tab.button is not None:
            if tab.is_selected:
                tab.button.window.style = "class:tab_button.focused"
            else:
                tab.button.window.style = "class:tab_button"
            tab.close_button.window.style = tab.button.window.style
            tab_buttons.append(VSplit([tab.button, tab.close_button]))
    pane_right_field = log_field
    focused_right_field = [tab.output_field for tab in command_tabs.values() if tab.is_selected]
    if focused_right_field:
        pane_right_field = focused_right_field[0]
    components["pane_right_top"] = VSplit(tab_buttons, height=1, style="class:log_field", padding_char=" ", padding=2)
    components["pane_right"] = ConditionalContainer(
        Box(body=HSplit([components["pane_right_top"], pane_right_field, search_field], width=Dimension(weight=1)),
            padding=0, padding_left=2, style="class:log_field"),
        filter=True
    )
    components["hint_menus"] = [Float(xcursor=True,
                                      ycursor=True,
                                      transparent=True,
                                      content=CompletionsMenu(max_height=16,
                                                              scroll_offset=1))]

    root_container = HSplit([
        components["pane_top"],
        VSplit(
            [FloatContainer(components["pane_left"], components["hint_menus"]),
             components["pane_right"]]),
        components["pane_bottom"],
    ])
    return Layout(root_container, focused_element=input_field), components

