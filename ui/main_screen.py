"""
ui/main_screen.py  —  Vibrant "Deep Space" theme
Deep navy base · Electric cyan accents · Coral highlights · Glassmorphism panels
"""

import os
import io
import threading
import logging
from typing import Optional, List, Dict

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image as KvImage
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.graphics import (Color, Rectangle, RoundedRectangle,
                             Line, Ellipse)

from modules.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

# ── Vibrant "Deep Space" Palette ───────────────────────────────────────────
#  Base: rich dark navy
#  Primary accent: electric cyan  #00E5FF
#  Secondary accent: warm coral   #FF6B6B
#  Surface: layered dark blues with slight purple tint

C_BG_DEEP     = get_color_from_hex("#080C1AFF")   # deepest bg
C_BG_SURFACE  = get_color_from_hex("#0D1526FF")   # main surface
C_BG_PANEL    = get_color_from_hex("#111B33FF")   # raised panels
C_BG_CARD     = get_color_from_hex("#162040FF")   # cards / bubbles
C_BG_INPUT    = get_color_from_hex("#0A1020FF")   # input fields
C_BG_GLASS    = get_color_from_hex("#1A2A4AE0")   # glass overlay

C_CYAN        = get_color_from_hex("#00E5FFFF")   # electric cyan
C_CYAN_DIM    = get_color_from_hex("#00E5FF55")   # cyan 33% alpha
C_CYAN_GLOW   = get_color_from_hex("#00E5FF22")   # cyan 13% alpha
C_CORAL       = get_color_from_hex("#FF6B6BFF")   # warm coral
C_CORAL_DIM   = get_color_from_hex("#FF6B6B55")   # coral 33% alpha
C_MINT        = get_color_from_hex("#00FFB3FF")   # mint green
C_GOLD        = get_color_from_hex("#FFD166FF")   # gold

C_TEXT_BRIGHT = get_color_from_hex("#F0F4FFFF")   # near-white
C_TEXT_MID    = get_color_from_hex("#8A9BBEFF")   # mid grey-blue
C_TEXT_DIM    = get_color_from_hex("#4A5A78FF")   # dim text

C_BORDER_CYAN = get_color_from_hex("#00E5FF40")   # cyan border
C_BORDER_MID  = get_color_from_hex("#1E3060FF")   # mid border
C_DIVIDER     = get_color_from_hex("#00E5FF33")   # divider line

C_NAV_BG      = get_color_from_hex("#060A14FF")   # nav bar
C_USER_BUBBLE = get_color_from_hex("#162A4AFF")   # user message bg
C_BOT_BUBBLE  = get_color_from_hex("#0D1E38FF")   # bot message bg

TRANSPARENT   = (0.0, 0.0, 0.0, 0.0)
MAX_WIDTH     = dp(520)


# ── Canvas helpers ─────────────────────────────────────────────────────────

def make_bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(size=widget.size, pos=widget.pos)
    widget.bind(size=lambda w, v: setattr(rect, 'size', v),
                pos=lambda w, v: setattr(rect, 'pos', v))
    return rect


def make_rounded_bg(widget, color, border_color=None, radius=8):
    with widget.canvas.before:
        if border_color:
            Color(*border_color)
            rb = RoundedRectangle(size=widget.size, pos=widget.pos,
                                   radius=[dp(radius)])
            widget.bind(size=lambda w, v: setattr(rb, 'size', v),
                        pos=lambda w, v: setattr(rb, 'pos', v))
        Color(*color)
        inner_pad = dp(1) if border_color else 0
        ri = RoundedRectangle(
            size=[widget.size[0] - inner_pad*2, widget.size[1] - inner_pad*2],
            pos=[widget.pos[0] + inner_pad, widget.pos[1] + inner_pad],
            radius=[dp(max(1, radius - 1))])
        widget.bind(
            size=lambda w, v: setattr(ri, 'size',
                [v[0]-inner_pad*2, v[1]-inner_pad*2]),
            pos=lambda w, v: setattr(ri, 'pos',
                [v[0]+inner_pad, v[1]+inner_pad]))


def png_to_texture(png_bytes: bytes):
    try:
        buf = io.BytesIO(png_bytes)
        ci = CoreImage(buf, ext="png", keep_data=True)
        return ci.texture
    except Exception as e:
        logger.error(f"png_to_texture: {e}")
        return None


# ── Glowing accent button ──────────────────────────────────────────────────

def make_glow_btn(text: str, callback, width=None,
                  bg=None, text_color=None, radius=10):
    """Button with a coloured rounded background and subtle glow border."""
    bg         = bg         or C_CYAN
    text_color = text_color or C_BG_DEEP

    btn = Button(
        text=text,
        size_hint_y=1,
        size_hint_x=(None if width else 1),
        width=width or dp(100),
        background_color=TRANSPARENT,
        color=text_color,
        font_size=sp(13),
        bold=True,
    )

    with btn.canvas.before:
        # Outer glow ring
        Color(bg[0], bg[1], bg[2], 0.25)
        glow = RoundedRectangle(size=btn.size, pos=btn.pos,
                                 radius=[dp(radius + 2)])
        # Fill
        Color(*bg)
        fill = RoundedRectangle(size=[btn.size[0]-dp(4), btn.size[1]-dp(4)],
                                 pos=[btn.pos[0]+dp(2), btn.pos[1]+dp(2)],
                                 radius=[dp(radius)])

    btn.bind(
        size=lambda w, v: (
            setattr(glow, 'size', v),
            setattr(fill, 'size', [v[0]-dp(4), v[1]-dp(4)])),
        pos=lambda w, v: (
            setattr(glow, 'pos', v),
            setattr(fill, 'pos', [v[0]+dp(2), v[1]+dp(2)])))

    if callback is not None:
        btn.bind(on_release=callback)
    return btn


# ── Chat Bubble ────────────────────────────────────────────────────────────

class ChatBubble(BoxLayout):
    def __init__(self, text: str, is_user: bool = False,
                 score: float = 0, page: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.padding     = [dp(6), dp(3)]
        self.spacing     = dp(4)

        bg_col     = C_USER_BUBBLE if is_user else C_BOT_BUBBLE
        glow_col   = C_CYAN_DIM    if is_user else C_CORAL_DIM
        accent_col = C_CYAN        if is_user else C_CORAL
        txt_col    = C_TEXT_BRIGHT

        outer = BoxLayout(orientation="vertical",
                          size_hint_x=0.87 if is_user else 0.91,
                          size_hint_y=None)

        # Glow border + fill
        with outer.canvas.before:
            Color(*glow_col)
            self._border = RoundedRectangle(
                size=outer.size, pos=outer.pos, radius=[dp(14)])
        with outer.canvas.before:
            Color(*bg_col)
            self._fill = RoundedRectangle(
                size=[max(0, outer.size[0]-dp(1.5)),
                      max(0, outer.size[1]-dp(1.5))],
                pos=[outer.pos[0]+dp(0.75), outer.pos[1]+dp(0.75)],
                radius=[dp(13)])
        # Left accent stripe
        with outer.canvas.before:
            Color(*accent_col)
            self._stripe = RoundedRectangle(
                size=[dp(3), max(0, outer.size[1]-dp(16))],
                pos=[outer.pos[0]+dp(8), outer.pos[1]+dp(8)],
                radius=[dp(2)])

        def _upd(w, v):
            setattr(self._border, 'size', v)
            setattr(self._fill, 'size',
                    [max(0,v[0]-dp(1.5)), max(0,v[1]-dp(1.5))])
            setattr(self._stripe, 'size', [dp(3), max(0,v[1]-dp(16))])
        def _upd_pos(w, v):
            setattr(self._border, 'pos', v)
            setattr(self._fill, 'pos', [v[0]+dp(0.75), v[1]+dp(0.75)])
            setattr(self._stripe, 'pos', [v[0]+dp(8), v[1]+dp(8)])

        outer.bind(size=_upd, pos=_upd_pos)

        # Role pill label
        role_box = BoxLayout(size_hint_y=None, height=dp(22),
                             padding=[dp(14), dp(2)])
        role_lbl = Label(
            text="● YOU" if is_user else "◆ DOCASSIST",
            font_size=sp(9), color=accent_col, bold=True,
            size_hint_x=1, halign="left",
            text_size=(None, None))
        role_box.add_widget(role_lbl)
        outer.add_widget(role_box)

        # Message text
        lbl = Label(
            text=text, font_size=sp(13), color=txt_col,
            size_hint_y=None, halign="left", valign="top",
            padding=[dp(14), dp(4)], markup=True)
        lbl.bind(width=lambda w, v: setattr(w, 'text_size', (v - dp(28), None)))
        lbl.bind(texture_size=lambda w, v: setattr(w, 'height', v[1]+dp(6)))
        outer.add_widget(lbl)

        if not is_user and score > 0:
            meta = Label(
                text=f"  ◈ {int(score*100)}% match  ·  pg {page}",
                font_size=sp(9), color=C_TEXT_DIM,
                size_hint_y=None, height=dp(20),
                halign="left", italic=True,
                padding=[dp(14), 0])
            outer.add_widget(meta)

        outer.add_widget(BoxLayout(size_hint_y=None, height=dp(6)))

        outer.bind(minimum_height=outer.setter('height'))
        outer.height = dp(70)

        if is_user:
            self.add_widget(BoxLayout(size_hint_x=0.13))
        self.add_widget(outer)
        if not is_user:
            self.add_widget(BoxLayout(size_hint_x=0.09))

        self.bind(minimum_height=self.setter('height'))
        Clock.schedule_once(lambda dt: self._fix(outer), 0.15)

    def _fix(self, outer):
        self.height = outer.height + dp(8)


# ── PDF Viewer ─────────────────────────────────────────────────────────────

class PDFViewer(BoxLayout):
    """Vertical BoxLayout: scroll area (flex) + nav bar (fixed)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self._page_num   = 0
        self._page_count = 0
        self._highlights: List[str] = []
        self._engine: Optional[RAGEngine] = None

        make_bg(self, C_BG_SURFACE)

        # Placeholder — lives in self, removed when doc loads
        ph_wrap = BoxLayout(orientation="vertical", size_hint=(1, 1))
        make_bg(ph_wrap, C_BG_SURFACE)
        self._placeholder = Label(
            text=(
                "[b][color=#00E5FF]📄[/color][/b]\n\n"
                "[color=#8A9BBE]Upload a PDF or DOCX\n"
                "to get started[/color]"
            ),
            markup=True, font_size=sp(16), halign="center",
            size_hint=(1, 1))
        ph_wrap.add_widget(self._placeholder)
        self._ph_wrap = ph_wrap
        self.add_widget(ph_wrap)

        # Scroll view with single image child — NOT added to self yet
        self._scroll = ScrollView(size_hint=(1, 1),
                                   do_scroll_x=False, do_scroll_y=True,
                                   bar_color=C_CYAN,
                                   bar_inactive_color=C_CYAN_DIM,
                                   bar_width=dp(4))
        self._img = KvImage(size_hint_x=1, size_hint_y=None,
                             height=dp(1), mipmap=True)
        self._scroll.add_widget(self._img)   # only child

        # ── Nav bar ──
        nav = BoxLayout(orientation="horizontal", size_hint=(1, None),
                        height=dp(48), padding=[dp(8), dp(6)], spacing=dp(8))
        make_bg(nav, C_NAV_BG)

        # Cyan top border on nav
        with nav.canvas.before:
            Color(*C_DIVIDER)
            self._nav_line = Line(points=[0,0,1,0], width=dp(1))
        nav.bind(
            pos =lambda w, v: setattr(self._nav_line, 'points',
                [v[0], v[1]+nav.height-dp(0.5),
                 v[0]+nav.width, v[1]+nav.height-dp(0.5)]),
            size=lambda w, v: setattr(self._nav_line, 'points',
                [nav.x, nav.y+v[1]-dp(0.5),
                 nav.x+v[0], nav.y+v[1]-dp(0.5)]))

        self._page_lbl = Label(
            text="—", color=C_TEXT_MID, font_size=sp(13),
            size_hint_x=1, halign="center", bold=True)
        nav.add_widget(self._make_nav_btn("◀", self._prev_page))
        nav.add_widget(self._page_lbl)
        nav.add_widget(self._make_nav_btn("▶", self._next_page))
        self.add_widget(nav)

    def _make_nav_btn(self, text: str, cb) -> Button:
        btn = Button(
            text=text, size_hint=(None, 1), width=dp(52),
            background_color=TRANSPARENT, color=C_CYAN,
            font_size=sp(16), bold=True)
        with btn.canvas.before:
            Color(*C_CYAN_DIM)
            r = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[dp(8)])
        btn.bind(size=lambda w, v: setattr(r, 'size', v),
                 pos=lambda w, v: setattr(r, 'pos', v))
        btn.bind(on_release=cb)
        return btn

    # ------------------------------------------------------------------

    def set_engine(self, engine: RAGEngine):
        self._engine     = engine
        self._page_count = engine.page_count
        self._page_num   = 0
        self._highlights = []
        if self._ph_wrap.parent is self:
            self.remove_widget(self._ph_wrap)
        if self._scroll.parent is None:
            self.add_widget(self._scroll, index=1)
        self._render_current()

    def show_page_with_highlights(self, page_0based: int,
                                   highlights: List[str],
                                   page_image_bytes: Optional[bytes] = None):
        self._page_num   = page_0based
        self._highlights = highlights
        if page_image_bytes:
            Clock.schedule_once(
                lambda dt: self._apply_texture(page_image_bytes), 0)
            self._update_nav_label()
        else:
            self._render_current()
        Clock.schedule_once(
            lambda dt: setattr(self._scroll, 'scroll_y', 1), 0.4)

    def _prev_page(self, *_):
        if self._page_num > 0:
            self._page_num -= 1
            self._highlights = []
            self._render_current()

    def _next_page(self, *_):
        if self._page_num < self._page_count - 1:
            self._page_num += 1
            self._highlights = []
            self._render_current()

    def _render_current(self):
        if not self._engine or self._page_count == 0:
            return
        Clock.schedule_once(self._do_render, 0)

    def _do_render(self, dt):
        page = self._page_num
        hl   = list(self._highlights)
        eng  = self._engine

        def _worker():
            img_bytes = None
            try:
                if eng and eng.is_pdf and eng.highlighter:
                    img_bytes = eng.highlighter.render_page(
                        page, zoom=2.5,
                        highlights=[{"text": h} for h in hl])
            except Exception as e:
                logger.error(f"render worker: {e}")
            Clock.schedule_once(lambda dt: self._update_nav_label(), 0)
            if img_bytes:
                Clock.schedule_once(lambda dt: self._apply_texture(img_bytes), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_texture(self, png_bytes: bytes):
        tex = png_to_texture(png_bytes)
        if not tex:
            return
        self._img.texture = tex
        w = self._scroll.width if self._scroll.width > 1 else dp(400)
        self._img.width  = w
        self._img.height = w * (tex.height / max(tex.width, 1))
        self._scroll.scroll_y = 1

    def _update_nav_label(self):
        total = max(self._page_count, 1)
        self._page_lbl.text = (
            f"[color=#00E5FF]{self._page_num + 1}[/color]"
            f"[color=#4A5A78] / {total}[/color]")
        self._page_lbl.markup = True


# ── Main Screen ────────────────────────────────────────────────────────────

class MainScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine = RAGEngine()
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        from kivy.core.window import Window

        # Full-screen deep bg
        outer = AnchorLayout(anchor_x="center", anchor_y="top")
        make_bg(outer, C_BG_DEEP)

        # Centre column with max width
        col = BoxLayout(orientation="vertical", size_hint=(None, 1),
                        width=MAX_WIDTH)
        make_bg(col, C_BG_SURFACE)

        # Subtle side borders on the column
        with col.canvas.before:
            Color(*C_BORDER_MID)
            self._left_line  = Line(points=[0,0,0,1], width=dp(0.5))
            self._right_line = Line(points=[0,0,0,1], width=dp(0.5))
        col.bind(
            pos =lambda w, v: self._update_col_lines(col),
            size=lambda w, v: self._update_col_lines(col))

        def _sync(win, size):
            col.width = min(size[0], MAX_WIDTH)
        Window.bind(size=_sync)
        col.width = min(Window.width, MAX_WIDTH)

        col.add_widget(self._build_header())
        col.add_widget(self._build_progress_row())

        # Split: viewer 60% / chat 40%
        split = BoxLayout(orientation="vertical", size_hint=(1, 1))

        self._viewer = PDFViewer(size_hint=(1, 0.60))
        split.add_widget(self._viewer)

        # Glowing divider
        div = BoxLayout(size_hint_y=None, height=dp(2))
        make_bg(div, C_DIVIDER)
        split.add_widget(div)

        chat = self._build_chat_panel()
        chat.size_hint_y = 0.40
        split.add_widget(chat)

        col.add_widget(split)
        outer.add_widget(col)
        self.add_widget(outer)

    def _update_col_lines(self, col):
        x, y, w, h = col.x, col.y, col.width, col.height
        self._left_line.points  = [x,       y, x,       y+h]
        self._right_line.points = [x+w-dp(0.5), y, x+w-dp(0.5), y+h]

    # ------------------------------------------------------------------

    def _build_progress_row(self) -> BoxLayout:
        row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(22))
        make_bg(row, C_BG_SURFACE)

        self._progress = ProgressBar(max=100, value=0,
                                      size_hint_y=None, height=dp(3))
        self._progress.opacity = 0
        row.add_widget(self._progress)

        self._status_lbl = Label(
            text="", font_size=sp(10), color=C_TEXT_DIM,
            size_hint=(1, None), height=dp(16), halign="center")
        row.add_widget(self._status_lbl)
        return row

    # ------------------------------------------------------------------

    def _build_header(self) -> BoxLayout:
        bar = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(58), padding=[dp(16), dp(8)], spacing=dp(12))
        make_bg(bar, C_BG_PANEL)

        # Bottom border on header
        with bar.canvas.before:
            Color(*C_DIVIDER)
            hline = Line(points=[0,0,1,0], width=dp(1))
        bar.bind(
            pos =lambda w, v: setattr(hline, 'points',
                [v[0], v[1], v[0]+bar.width, v[1]]),
            size=lambda w, v: setattr(hline, 'points',
                [bar.x, bar.y, bar.x+v[0], bar.y]))

        # Logo mark — small cyan square
        logo_box = BoxLayout(size_hint=(None, None),
                             size=(dp(32), dp(32)))
        logo_box.pos_hint = {"center_y": 0.5}
        with logo_box.canvas:
            Color(*C_CYAN)
            RoundedRectangle(size=(dp(32), dp(32)), pos=(0,0),
                              radius=[dp(6)])
            Color(*C_BG_DEEP)
            RoundedRectangle(size=(dp(18), dp(18)),
                              pos=(dp(7), dp(7)), radius=[dp(3)])
        bar.add_widget(logo_box)

        # Title
        title = Label(
            text="[b][color=#00E5FF]Doc[/color]"
                 "[color=#F0F4FF]Assist[/color][/b]",
            markup=True, font_size=sp(22),
            size_hint_x=1, halign="left")
        bar.add_widget(title)

        # Upload button (coral glow)
        upload_btn = make_glow_btn(
            "📂  Upload",
            self._open_file_picker,
            width=dp(120),
            bg=C_CORAL,
            text_color=C_TEXT_BRIGHT,
            radius=10)
        bar.add_widget(upload_btn)

        # Doc name chip
        self._doc_name_lbl = Label(
            text="No file", font_size=sp(10), color=C_TEXT_DIM,
            size_hint=(None, 1), width=dp(110),
            halign="right", text_size=(dp(110), None))
        bar.add_widget(self._doc_name_lbl)
        return bar

    # ------------------------------------------------------------------

    def _build_chat_panel(self) -> BoxLayout:
        panel = BoxLayout(orientation="vertical")
        make_bg(panel, C_BG_PANEL)

        # Chat list
        self._chat_scroll = ScrollView(
            size_hint=(1, 1), do_scroll_x=False,
            bar_color=C_CORAL, bar_inactive_color=C_CORAL_DIM,
            bar_width=dp(3))
        self._chat_list = GridLayout(
            cols=1, size_hint_y=None,
            spacing=dp(6), padding=[dp(10), dp(8)])
        self._chat_list.bind(minimum_height=self._chat_list.setter('height'))
        self._chat_scroll.add_widget(self._chat_list)
        panel.add_widget(self._chat_scroll)

        # Input row
        input_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                              height=dp(58), padding=[dp(10), dp(8)],
                              spacing=dp(8))
        make_bg(input_row, C_BG_DEEP)

        # Cyan top border on input row
        with input_row.canvas.before:
            Color(*C_DIVIDER)
            il = Line(points=[0,0,1,0], width=dp(0.5))
        input_row.bind(
            pos =lambda w, v: setattr(il, 'points',
                [v[0], v[1]+input_row.height-dp(0.5),
                 v[0]+input_row.width, v[1]+input_row.height-dp(0.5)]),
            size=lambda w, v: setattr(il, 'points',
                [input_row.x, input_row.y+v[1]-dp(0.5),
                 input_row.x+v[0], input_row.y+v[1]-dp(0.5)]))

        # Text input with cyan border
        input_wrap = BoxLayout(size_hint=(1, 1))
        with input_wrap.canvas.before:
            Color(*C_BORDER_CYAN)
            iw_border = RoundedRectangle(
                size=input_wrap.size, pos=input_wrap.pos, radius=[dp(12)])
            Color(*C_BG_INPUT)
            iw_fill = RoundedRectangle(
                size=[input_wrap.size[0]-dp(1.5), input_wrap.size[1]-dp(1.5)],
                pos=[input_wrap.pos[0]+dp(0.75), input_wrap.pos[1]+dp(0.75)],
                radius=[dp(11)])
        input_wrap.bind(
            size=lambda w, v: (
                setattr(iw_border, 'size', v),
                setattr(iw_fill, 'size',
                        [v[0]-dp(1.5), v[1]-dp(1.5)])),
            pos=lambda w, v: (
                setattr(iw_border, 'pos', v),
                setattr(iw_fill, 'pos',
                        [v[0]+dp(0.75), v[1]+dp(0.75)])))

        self._query_input = TextInput(
            hint_text="Ask anything about the document…",
            multiline=False, size_hint=(1, 1), font_size=sp(13),
            background_color=TRANSPARENT,
            foreground_color=C_TEXT_BRIGHT,
            hint_text_color=C_TEXT_DIM,
            cursor_color=C_CYAN,
            padding=[dp(14), dp(14)])
        self._query_input.bind(on_text_validate=self._on_send)
        input_wrap.add_widget(self._query_input)
        input_row.add_widget(input_wrap)

        # Send button (cyan glow)
        send_btn = make_glow_btn(
            "➤", self._on_send,
            width=dp(52),
            bg=C_CYAN,
            text_color=C_BG_DEEP,
            radius=12)
        input_row.add_widget(send_btn)
        panel.add_widget(input_row)
        return panel

    # ------------------------------------------------------------------
    # File picker
    # ------------------------------------------------------------------

    def _open_file_picker(self, *_):
        content = BoxLayout(orientation="vertical", spacing=dp(10),
                            padding=dp(12))
        make_bg(content, C_BG_SURFACE)

        fc = FileChooserIconView(
            filters=["*.pdf", "*.docx", "*.doc"], size_hint=(1, 1))
        content.add_widget(fc)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        btn_open = make_glow_btn("Open", None, bg=C_CYAN,
                                  text_color=C_BG_DEEP, radius=8)
        btn_cancel = make_glow_btn("Cancel", None, bg=C_CORAL,
                                    text_color=C_TEXT_BRIGHT, radius=8)
        btn_row.add_widget(btn_open)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        popup = Popup(
            title="Select Document", content=content,
            size_hint=(0.95, 0.85),
            title_color=C_CYAN,
            background_color=C_BG_PANEL,
            separator_color=C_DIVIDER)

        def _open(*_a):
            if fc.selection:
                popup.dismiss()
                self._load_document(fc.selection[0])

        btn_open.bind(on_release=_open)
        btn_cancel.bind(on_release=popup.dismiss)
        popup.open()

    # ------------------------------------------------------------------
    # Document loading
    # ------------------------------------------------------------------

    def _load_document(self, filepath: str):
        self._engine.close()
        self._engine = RAGEngine()
        self._chat_list.clear_widgets()
        name = os.path.basename(filepath)
        self._doc_name_lbl.text = name[:18] + "…" if len(name) > 18 else name
        self._progress.opacity = 1
        self._progress.value   = 0

        self._engine.load_document(
            filepath,
            on_progress=lambda m, r: Clock.schedule_once(
                lambda dt: self._update_progress(m, r)),
            on_complete=lambda: Clock.schedule_once(
                lambda dt: self._on_doc_ready()),
            on_error=lambda e: Clock.schedule_once(
                lambda dt: self._show_error(e)),
        )

    def _update_progress(self, msg: str, ratio: float):
        self._progress.value  = ratio * 100
        self._status_lbl.text = msg

    def _on_doc_ready(self):
        self._progress.opacity = 0
        self._status_lbl.text  = "✓ Ready — ask me anything!"
        self._viewer.set_engine(self._engine)
        self._add_bot_message(
            "Document loaded! I've indexed everything.\n"
            "Ask me anything about it.")

    def _show_error(self, msg: str):
        self._progress.opacity = 0
        self._status_lbl.text  = f"⚠ {msg}"
        self._add_bot_message(f"[b][color=#FF6B6B]Error:[/color][/b] {msg}")

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def _on_send(self, *_):
        question = self._query_input.text.strip()
        if not question:
            return
        self._query_input.text = ""
        self._add_user_message(question)
        self._status_lbl.text = "⟳ Searching…"

        self._engine.query(
            question,
            on_result=lambda r: Clock.schedule_once(
                lambda dt: self._display_results(r)),
            on_error=lambda e: Clock.schedule_once(
                lambda dt: self._show_error(e)),
        )

    def _display_results(self, results: List[Dict]):
        self._status_lbl.text = ""
        if not results:
            self._add_bot_message("No relevant sections found.")
            return

        best  = results[0]
        lines = []
        for i, r in enumerate(results):
            pct = int(r.get("score", 0) * 100)
            pg  = r.get("page", 0)
            txt = r.get("text", "").strip()
            pin = "[color=#00E5FF]📌[/color]" if i == 0 else f"[color=#FF6B6B][{i+1}][/color]"
            lines.append(
                f"{pin} [b]Page {pg}[/b] "
                f"[color=#4A5A78]({pct}% match)[/color]\n{txt}")

        self._add_bot_message(
            "\n\n".join(lines),
            score=best.get("score", 0),
            page=best.get("page", 0))

        if self._engine.is_pdf:
            page_0    = best.get("page_0based", max(0, best.get("page", 1)-1))
            sentences = best.get("sentences", [])[:2]
            img_bytes = best.get("page_image")
            self._viewer.show_page_with_highlights(
                page_0, sentences, page_image_bytes=img_bytes)

    # ------------------------------------------------------------------

    def _add_user_message(self, text: str):
        self._chat_list.add_widget(ChatBubble(text=text, is_user=True))
        Clock.schedule_once(
            lambda dt: setattr(self._chat_scroll, 'scroll_y', 0), 0.2)

    def _add_bot_message(self, text: str, score: float = 0, page: int = 0):
        self._chat_list.add_widget(
            ChatBubble(text=text, is_user=False, score=score, page=page))
        Clock.schedule_once(
            lambda dt: setattr(self._chat_scroll, 'scroll_y', 0), 0.2)

    def on_leave(self, *_):
        self._engine.close()