"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import math

import pyray as rl

from openpilot.selfdrive.ui.mici.layouts.home import MiciHomeLayout, HOME_PADDING
from openpilot.selfdrive.ui.sunnypilot.longitudinal_mode import EXPERIMENTAL_ICON
from openpilot.selfdrive.ui.sunnypilot.model_info import carrying_name, short_name
from openpilot.selfdrive.ui.ui_state import ui_state, ChestnutState
from openpilot.system.ui.lib.application import FontWeight, TextAlignment, TextAlignmentVertical, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets.icon_widget import IconWidget
from openpilot.system.ui.widgets.label import UnifiedLabel

MODEL_ROW_HEIGHT = 48
MODEL_ICON_GAP = 24
MODEL_FONT_SIZE = 32
MODEL_MIN_WIDTH = 96  # narrower than this, a scrolling name is a few letters at a time


class MiciHomeLayoutSP(MiciHomeLayout):
  def __init__(self):
    super().__init__()
    self._openpilot_label = UnifiedLabel("zoompilot", font_size=88, font_weight=FontWeight.AUDIOWIDE, max_width=480, wrap_text=False)
    # zoompilot keeps upstream's retired long press to switch experimental mode
    self.set_long_press_callback(self._toggle_experimental_mode)
    # upstream's status bar icon, after the network icon, retired with chill mode
    self._experimental_icon = IconWidget(EXPERIMENTAL_ICON, (48, 48))
    self._experimental_icon.set_visible(lambda: ui_state.has_longitudinal_control and ui_state.experimental_mode)
    self._status_bar_layout.add_widget(self._experimental_icon)
    self._status_bar_layout.widgets.insert(2, self._status_bar_layout.widgets.pop())
    # the models page's active model line, right aligned in the footer; a long name scrolls
    self._model_label = UnifiedLabel("", MODEL_FONT_SIZE, FontWeight.ROMAN, rl.Color(255, 255, 255, int(255 * 0.9 * 0.65)),
                                     alignment=TextAlignment.RIGHT, alignment_vertical=TextAlignmentVertical.MIDDLE, scroll=True)

  @staticmethod
  def _toggle_experimental_mode():
    if ui_state.has_longitudinal_control:
      ui_state.set_experimental_mode(not ui_state.experimental_mode)

  def _set_chestnut_visibility(self):
    usb_connected = ui_state.usb_connected
    usb_unknown = ui_state.usb_unknown
    chestnut_state = ui_state.chestnut_state
    loading = chestnut_state == ChestnutState.LOADING
    # ready, and only a swap window away: steady rather than the loading pulse,
    # dim rather than the solid green of a model that is driving
    waiting = chestnut_state == ChestnutState.WAITING

    # the port is known while Jetlink holds it, whatever enumerated
    self._usb_icon.set_visible(usb_connected and usb_unknown and not ui_state.adb_blocked)
    self._chestnut_loading_icon.set_opacity(0.35 + 0.65 * (0.5 - 0.5 * math.cos(rl.get_time() * 6.0)))
    self._chestnut_loading_icon.set_visible(not usb_unknown and loading)
    self._chestnut_icon.set_opacity(0.5 if waiting else 1.0)
    self._chestnut_icon.set_visible(not usb_unknown and not loading and
                                    chestnut_state in (ChestnutState.READY, ChestnutState.ACTIVE,
                                                       ChestnutState.WAITING))
    self._chestnut_failed_icon.set_visible(not usb_unknown and chestnut_state in (ChestnutState.UNCOMPILED, ChestnutState.FAILED))

  def _render(self, rect):
    super()._render(rect)
    if ui_state.home_show_active_model:
      self._render_model_name()

  def _render_model_name(self):
    # the footer between the last status icon (settings always shows) and the alerts pill
    last_icon = [w for w in self._status_bar_layout.widgets if w.is_visible][-1]
    left = last_icon.rect.x + last_icon.rect.width + MODEL_ICON_GAP
    right = self.rect.x + self.rect.width - HOME_PADDING
    if self._alert_count_callback and self._alert_count_callback() > 0:
      right = self._alerts_pill.rect.x - HOME_PADDING
    name = short_name(carrying_name()).lower()
    # a name that fits always shows; one that does not scrolls, unless too little of it would
    if right - left < min(measure_text_cached(gui_app.font(FontWeight.ROMAN), name, MODEL_FONT_SIZE).x, MODEL_MIN_WIDTH):
      return
    self._model_label.set_text(name)
    self._model_label.render(rl.Rectangle(left, self.rect.y + self.rect.height - MODEL_ROW_HEIGHT, right - left, MODEL_ROW_HEIGHT))
