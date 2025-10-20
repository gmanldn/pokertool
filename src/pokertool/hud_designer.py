"""Interactive HUD designer dialog for customizing the overlay."""

from __future__ import annotations

import copy
from typing import Dict, List, Optional, Any, TYPE_CHECKING

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError as exc:  # pragma: no cover - GUI only
    raise RuntimeError("tkinter is required for the HUD designer") from exc

from .hud_profiles import list_hud_profiles, load_hud_profile

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .hud_overlay import HUDConfig


class HUDDesigner:
    """Modal configuration editor for the HUD overlay."""

    _OPERATORS = ['>=', '>', '<=', '<', '==']

    def __init__(self, parent: tk.Misc, config: 'HUDConfig') -> None:
        self.parent = parent
        self._config_cls = type(config)
        self._original_config = config
        self._working_config = self._config_cls.from_dict(config.to_dict())
        self._result: Optional['HUDConfig'] = None

        self._window: Optional[tk.Toplevel] = None
        self._notebook: Optional[ttk.Notebook] = None

        # Tk variables populated during UI build
        self._display_vars: Dict[str, tk.Variable] = {}
        self._dimension_vars: Dict[str, tk.StringVar] = {}
        self._stat_vars: Dict[str, tk.BooleanVar] = {}
        self._new_stat_var: Optional[tk.StringVar] = None

        self._profile_name_value = config.profile_name
        self._profile_name: Optional[tk.StringVar] = None
        self._profile_selector: Optional[ttk.Combobox] = None


        # Color condition state structures
        self._condition_stat_var: Optional[tk.StringVar] = None
        self._condition_listbox: Optional[tk.Listbox] = None
        self._condition_fields: Dict[str, tk.StringVar] = {}
        self._conditions: Dict[str, List[Dict[str, Any]]] = copy.deepcopy(
            self._working_config.stat_color_conditions
        )

        # Popup stats structures
        self._popup_available: Optional[tk.Listbox] = None
        self._popup_selected: Optional[tk.Listbox] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def show(self) -> Optional['HUDConfig']:
        """Display the designer window and return the updated config."""
        self._create_window()
        self.parent.wait_window(self._window)
        return self._result

    # ------------------------------------------------------------------
    # Window and UI construction
    # ------------------------------------------------------------------
    def _create_window(self) -> None:
        window = tk.Toplevel(self.parent)
        window.title("HUD Designer")
        window.transient(self.parent)
        window.grab_set()
        window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        window.geometry('720x560')
        self._window = window

        self._notebook = ttk.Notebook(window)
        self._notebook.pack(fill='both', expand=True, padx=12, pady=12)

        self._build_display_tab()
        self._build_stats_tab()
        self._build_conditions_tab()
        self._build_popup_tab()
        self._build_profile_tab()

        # Action buttons
        button_frame = ttk.Frame(window)
        button_frame.pack(fill='x', padx=12, pady=(0, 12))
        ttk.Button(button_frame, text='Cancel', command=self._on_cancel).pack(side='right')
        ttk.Button(button_frame, text='Apply', command=self._on_apply).pack(side='right', padx=(0, 8))

    # ------------------------------------------------------------------
    # Display tab helpers
    # ------------------------------------------------------------------
    def _build_display_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text='Display')

        toggles = {
            'show_hole_cards': 'Show hero hole cards',
            'show_board_cards': 'Show community cards',
            'show_position': 'Show position',
            'show_pot_odds': 'Show pot odds',
            'show_hand_strength': 'Show hand strength',
            'show_gto_advice': 'Show GTO advice',
            'show_opponent_stats': 'Show opponent stats',
            'popup_enabled': 'Enable opponent popup',
            'always_on_top': 'Keep HUD on top'
        }

        toggle_frame = ttk.LabelFrame(frame, text='Sections')
        toggle_frame.pack(fill='both', expand=False, padx=12, pady=12)

        for key, label in toggles.items():
            var = tk.BooleanVar(master=self._window, value=getattr(self._working_config, key))
            self._display_vars[key] = var
            ttk.Checkbutton(toggle_frame, text=label, variable=var).pack(anchor='w', pady=2)

        config_frame = ttk.LabelFrame(frame, text='Appearance')
        config_frame.pack(fill='x', expand=False, padx=12, pady=(0, 12))

        # Opacity, font size, theme, update interval
        self._dimension_vars['opacity'] = tk.StringVar(master=self._window, value=str(self._working_config.opacity))
        self._dimension_vars['font_size'] = tk.StringVar(master=self._window, value=str(self._working_config.font_size))
        self._dimension_vars['update_interval'] = tk.StringVar(
            master=self._window,
            value=str(self._working_config.update_interval)
        )

        ttk.Label(config_frame, text='Opacity (0-1)').grid(row=0, column=0, sticky='w')
        ttk.Entry(config_frame, textvariable=self._dimension_vars['opacity'], width=10).grid(
            row=0, column=1, sticky='w', padx=(4, 20)
        )

        ttk.Label(config_frame, text='Font size').grid(row=0, column=2, sticky='w')
        ttk.Entry(config_frame, textvariable=self._dimension_vars['font_size'], width=10).grid(
            row=0, column=3, sticky='w', padx=(4, 20)
        )

        ttk.Label(config_frame, text='Update interval (s)').grid(row=1, column=0, sticky='w', pady=(8, 0))
        ttk.Entry(config_frame, textvariable=self._dimension_vars['update_interval'], width=10).grid(
            row=1, column=1, sticky='w', padx=(4, 20), pady=(8, 0)
        )

        ttk.Label(config_frame, text='Theme').grid(row=1, column=2, sticky='w', pady=(8, 0))
        theme_var = tk.StringVar(master=self._window, value=self._working_config.theme)
        self._dimension_vars['theme'] = theme_var
        ttk.Combobox(
            config_frame,
            textvariable=theme_var,
            values=['dark', 'light'],
            state='readonly',
            width=12
        ).grid(row=1, column=3, sticky='w', padx=(4, 20), pady=(8, 0))

        position_frame = ttk.LabelFrame(frame, text='Window Placement')
        position_frame.pack(fill='x', expand=False, padx=12, pady=(0, 12))

        self._dimension_vars['position_x'] = tk.StringVar(master=self._window, value=str(self._working_config.position[0]))
        self._dimension_vars['position_y'] = tk.StringVar(master=self._window, value=str(self._working_config.position[1]))
        self._dimension_vars['width'] = tk.StringVar(master=self._window, value=str(self._working_config.size[0]))
        self._dimension_vars['height'] = tk.StringVar(master=self._window, value=str(self._working_config.size[1]))

        ttk.Label(position_frame, text='X').grid(row=0, column=0, sticky='w')
        ttk.Entry(position_frame, textvariable=self._dimension_vars['position_x'], width=8).grid(
            row=0, column=1, sticky='w', padx=(4, 12)
        )
        ttk.Label(position_frame, text='Y').grid(row=0, column=2, sticky='w')
        ttk.Entry(position_frame, textvariable=self._dimension_vars['position_y'], width=8).grid(
            row=0, column=3, sticky='w', padx=(4, 12)
        )
        ttk.Label(position_frame, text='Width').grid(row=1, column=0, sticky='w', pady=(8, 0))
        ttk.Entry(position_frame, textvariable=self._dimension_vars['width'], width=8).grid(
            row=1, column=1, sticky='w', padx=(4, 12), pady=(8, 0)
        )
        ttk.Label(position_frame, text='Height').grid(row=1, column=2, sticky='w', pady=(8, 0))
        ttk.Entry(position_frame, textvariable=self._dimension_vars['height'], width=8).grid(
            row=1, column=3, sticky='w', padx=(4, 12), pady=(8, 0)
        )

    # ------------------------------------------------------------------
    # Stats tab helpers
    # ------------------------------------------------------------------
    def _build_stats_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text='Stats')

        stats_frame = ttk.LabelFrame(frame, text='Available stats')
        stats_frame.pack(fill='both', expand=True, padx=12, pady=12)

        self._stat_vars = {}
        existing = sorted(set(self._working_config.available_stats + self._working_config.enabled_stats))
        for stat in existing:
            var = tk.BooleanVar(master=self._window, value=stat in self._working_config.enabled_stats)
            self._stat_vars[stat] = var
            ttk.Checkbutton(stats_frame, text=stat.upper(), variable=var).pack(anchor='w', pady=2)

        add_frame = ttk.Frame(frame)
        add_frame.pack(fill='x', expand=False, padx=12, pady=(0, 12))
        ttk.Label(add_frame, text='New stat name').pack(side='left')
        self._new_stat_var = tk.StringVar(master=self._window)
        ttk.Entry(add_frame, textvariable=self._new_stat_var, width=20).pack(side='left', padx=6)
        ttk.Button(add_frame, text='Add stat', command=self._add_custom_stat).pack(side='left')

    def _add_custom_stat(self) -> None:
        name = self._new_stat_var.get().strip().lower()
        if not name:
            return
        if name in self._stat_vars:
            messagebox.showinfo('HUD Designer', f"Stat '{name}' already exists.")
            return
        if name not in self._working_config.available_stats:
            self._working_config.available_stats.append(name)
        if name not in self._working_config.enabled_stats:
            self._working_config.enabled_stats.append(name)
        self._conditions.setdefault(name, [])
        self._rebuild_full_ui()
        self._new_stat_var.set('')

    # ------------------------------------------------------------------
    # Color conditions tab helpers
    # ------------------------------------------------------------------
    def _build_conditions_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text='Color Conditions')

        self._condition_stat_var = tk.StringVar(master=self._window)
        self._condition_fields = {
            'operator': tk.StringVar(master=self._window, value=self._OPERATORS[0]),
            'threshold': tk.StringVar(master=self._window, value='0'),
            'color': tk.StringVar(master=self._window, value='#ffffff'),
            'label': tk.StringVar(master=self._window, value='')
        }

        top_frame = ttk.Frame(frame)
        top_frame.pack(fill='x', padx=12, pady=(12, 6))

        stats = sorted(self._stat_vars.keys()) or ['vpip']
        current_stat = stats[0]
        self._condition_stat_var.set(current_stat)
        ttk.Label(top_frame, text='Stat').pack(side='left')
        stat_combo = ttk.Combobox(
            top_frame,
            textvariable=self._condition_stat_var,
            values=stats,
            state='readonly',
            width=16
        )
        stat_combo.pack(side='left', padx=8)
        stat_combo.bind('<<ComboboxSelected>>', lambda _e: self._refresh_condition_list())

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        self._condition_listbox = tk.Listbox(list_frame, height=8)
        self._condition_listbox.pack(side='left', fill='both', expand=True)
        self._condition_listbox.bind('<<ListboxSelect>>', self._on_condition_selected)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self._condition_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self._condition_listbox.configure(yscrollcommand=scrollbar.set)

        form = ttk.LabelFrame(frame, text='Condition details')
        form.pack(fill='x', padx=12, pady=(0, 12))

        ttk.Label(form, text='Operator').grid(row=0, column=0, sticky='w')
        operator_combo = ttk.Combobox(
            form,
            textvariable=self._condition_fields['operator'],
            values=self._OPERATORS,
            state='readonly',
            width=6
        )
        operator_combo.grid(row=0, column=1, sticky='w', padx=(6, 18))

        ttk.Label(form, text='Threshold').grid(row=0, column=2, sticky='w')
        ttk.Entry(form, textvariable=self._condition_fields['threshold'], width=10).grid(
            row=0, column=3, sticky='w', padx=(6, 18)
        )

        ttk.Label(form, text='Color').grid(row=1, column=0, sticky='w', pady=(8, 0))
        ttk.Entry(form, textvariable=self._condition_fields['color'], width=10).grid(
            row=1, column=1, sticky='w', padx=(6, 18), pady=(8, 0)
        )

        ttk.Label(form, text='Label').grid(row=1, column=2, sticky='w', pady=(8, 0))
        ttk.Entry(form, textvariable=self._condition_fields['label'], width=18).grid(
            row=1, column=3, sticky='w', padx=(6, 18), pady=(8, 0)
        )

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', padx=12, pady=(0, 12))
        ttk.Button(button_frame, text='Add', command=self._add_condition).pack(side='left')
        ttk.Button(button_frame, text='Update', command=self._update_condition).pack(side='left', padx=6)
        ttk.Button(button_frame, text='Delete', command=self._delete_condition).pack(side='left')

        self._refresh_condition_list()

    def _refresh_condition_list(self) -> None:
        if not self._condition_stat_var or not self._condition_listbox:
            return
        stat_name = self._condition_stat_var.get()
        if stat_name not in self._conditions:
            self._conditions[stat_name] = []
        self._condition_listbox.delete(0, tk.END)
        for condition in self._conditions[stat_name]:
            description = (
                f"{condition.get('operator', '>=')} {condition.get('threshold', 0)} -> "
                f"{condition.get('color', '#ffffff')}"
            )
            label = condition.get('label')
            if label:
                description += f" ({label})"
            self._condition_listbox.insert(tk.END, description)
        self._condition_listbox.selection_clear(0, tk.END)
        for value in self._condition_fields.values():
            value.set('')
        self._condition_fields['operator'].set(self._OPERATORS[0])
        self._condition_fields['threshold'].set('0')
        self._condition_fields['color'].set('#ffffff')

    def _on_condition_selected(self, _event=None) -> None:
        if not self._condition_listbox:
            return
        selection = self._condition_listbox.curselection()
        if not selection:
            return
        stat_name = self._condition_stat_var.get()
        index = selection[0]
        condition = self._conditions.get(stat_name, [])[index]
        self._condition_fields['operator'].set(condition.get('operator', '>=') or '>=')
        self._condition_fields['threshold'].set(str(condition.get('threshold', 0)))
        self._condition_fields['color'].set(condition.get('color', '#ffffff') or '#ffffff')
        self._condition_fields['label'].set(condition.get('label', '') or '')

    def _read_condition_fields(self) -> Optional[Dict[str, Any]]:
        try:
            threshold = float(self._condition_fields['threshold'].get())
        except ValueError:
            messagebox.showerror('HUD Designer', 'Threshold must be a numeric value.')
            return None
        operator = self._condition_fields['operator'].get() or '>='
        if operator not in self._OPERATORS:
            messagebox.showerror('HUD Designer', 'Operator is not supported.')
            return None
        data = {
            'operator': operator,
            'threshold': threshold,
            'color': self._condition_fields['color'].get() or '#ffffff',
            'label': self._condition_fields['label'].get().strip()
        }
        return data

    def _add_condition(self) -> None:
        if not self._condition_stat_var:
            return
        stat_name = self._condition_stat_var.get()
        condition = self._read_condition_fields()
        if not condition:
            return
        self._conditions.setdefault(stat_name, []).append(condition)
        self._refresh_condition_list()

    def _update_condition(self) -> None:
        if not self._condition_stat_var or not self._condition_listbox:
            return
        selection = self._condition_listbox.curselection()
        if not selection:
            messagebox.showinfo('HUD Designer', 'Select a condition to update.')
            return
        condition = self._read_condition_fields()
        if not condition:
            return
        stat_name = self._condition_stat_var.get()
        index = selection[0]
        self._conditions[stat_name][index] = condition
        self._refresh_condition_list()

    def _delete_condition(self) -> None:
        if not self._condition_stat_var or not self._condition_listbox:
            return
        selection = self._condition_listbox.curselection()
        if not selection:
            return
        stat_name = self._condition_stat_var.get()
        index = selection[0]
        del self._conditions[stat_name][index]
        self._refresh_condition_list()

    # ------------------------------------------------------------------
    # Popup configuration tab helpers
    # ------------------------------------------------------------------
    def _build_popup_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text='Popup Stats')

        container = ttk.Frame(frame)
        container.pack(fill='both', expand=True, padx=12, pady=12)

        ttk.Label(container, text='Available').grid(row=0, column=0)
        ttk.Label(container, text='Selected').grid(row=0, column=2)

        self._popup_available = tk.Listbox(container, selectmode=tk.MULTIPLE, height=12)
        self._popup_available.grid(row=1, column=0, sticky='nsew')

        control_frame = ttk.Frame(container)
        control_frame.grid(row=1, column=1, padx=10)
        ttk.Button(control_frame, text='Add →', command=self._add_popup_stats).pack(pady=4)
        ttk.Button(control_frame, text='← Remove', command=self._remove_popup_stats).pack(pady=4)
        ttk.Button(control_frame, text='Move Up', command=lambda: self._reorder_popup(-1)).pack(pady=4)
        ttk.Button(control_frame, text='Move Down', command=lambda: self._reorder_popup(1)).pack(pady=4)

        self._popup_selected = tk.Listbox(container, selectmode=tk.SINGLE, height=12)
        self._popup_selected.grid(row=1, column=2, sticky='nsew')

        container.columnconfigure(0, weight=1)
        container.columnconfigure(2, weight=1)

        all_stats = sorted(set(self._stat_vars.keys()))
        selected = list(self._working_config.popup_stats)
        for stat in all_stats:
            if stat not in selected:
                self._popup_available.insert(tk.END, stat)
        for stat in selected:
            self._popup_selected.insert(tk.END, stat)

    def _add_popup_stats(self) -> None:
        if not self._popup_available or not self._popup_selected:
            return
        selections = self._popup_available.curselection()
        for index in selections:
            stat = self._popup_available.get(index)
            if stat not in self._popup_selected.get(0, tk.END):
                self._popup_selected.insert(tk.END, stat)

    def _remove_popup_stats(self) -> None:
        if not self._popup_selected:
            return
        selection = self._popup_selected.curselection()
        for index in reversed(selection):
            self._popup_selected.delete(index)

    def _reorder_popup(self, direction: int) -> None:
        if not self._popup_selected:
            return
        selection = self._popup_selected.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + direction
        if new_index < 0 or new_index >= self._popup_selected.size():
            return
        value = self._popup_selected.get(index)
        self._popup_selected.delete(index)
        self._popup_selected.insert(new_index, value)
        self._popup_selected.selection_set(new_index)

    # ------------------------------------------------------------------
    # Profile tab helpers
    # ------------------------------------------------------------------
    def _build_profile_tab(self) -> None:
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text='Profiles')

        chooser = ttk.LabelFrame(frame, text='Load existing profile')
        chooser.pack(fill='x', padx=12, pady=12)

        profiles = list_hud_profiles()
        self._profile_selector = ttk.Combobox(chooser, values=profiles, state='readonly', width=20)
        self._profile_selector.pack(side='left', padx=(6, 8), pady=8)
        if self._profile_name_value in profiles:
            self._profile_selector.set(self._profile_name_value)
        ttk.Button(chooser, text='Load', command=self._load_profile).pack(side='left', pady=8)

        name_frame = ttk.LabelFrame(frame, text='Profile name')
        name_frame.pack(fill='x', padx=12, pady=(0, 12))

        self._profile_name = tk.StringVar(master=self._window, value=self._profile_name_value)
        ttk.Entry(name_frame, textvariable=self._profile_name, width=24).pack(padx=8, pady=8, fill='x')
        ttk.Label(
            name_frame,
            text='The profile name is used when saving from the HUD overlay.'
        ).pack(anchor='w', padx=8, pady=(0, 8))

    def _load_profile(self) -> None:
        if not self._profile_selector:
            return
        name = self._profile_selector.get().strip()
        if not name:
            return
        data = load_hud_profile(name)
        if not data:
            messagebox.showinfo('HUD Designer', f"Profile '{name}' could not be loaded.")
            return
        merged = {**self._original_config.to_dict(), **data}
        merged['profile_name'] = name
        self._working_config = self._config_cls.from_dict(merged)
        self._conditions = copy.deepcopy(self._working_config.stat_color_conditions)
        self._profile_name_value = name
        self._rebuild_full_ui()

    def _rebuild_full_ui(self) -> None:
        if not self._window or not self._notebook:
            return
        current_tab = self._notebook.index(self._notebook.select())
        if self._profile_name:
            value = self._profile_name.get().strip()
            if value:
                self._profile_name_value = value
        self._display_vars.clear()
        self._dimension_vars.clear()
        self._stat_vars = {}
        self._new_stat_var = None
        self._condition_fields = {}
        self._condition_stat_var = None
        self._condition_listbox = None
        self._popup_available = None
        self._popup_selected = None
        self._profile_selector = None
        self._profile_name = None
        for child in list(self._notebook.winfo_children()):
            self._notebook.forget(child)
        self._build_display_tab()
        self._build_stats_tab()
        self._build_conditions_tab()
        self._build_popup_tab()
        self._build_profile_tab()
        try:
            self._notebook.select(current_tab)
        except tk.TclError:
            self._notebook.select(0)

    # ------------------------------------------------------------------
    # Apply / Cancel handlers
    # ------------------------------------------------------------------
    def _on_cancel(self) -> None:
        if self._window:
            self._window.destroy()
        self._result = None

    def _on_apply(self) -> None:
        try:
            updated = self._collect_configuration()
        except ValueError as exc:
            messagebox.showerror('HUD Designer', str(exc))
            return
        self._result = updated
        if self._window:
            self._window.destroy()

    def _collect_configuration(self) -> 'HUDConfig':
        config_dict = self._working_config.to_dict()

        # Display toggles
        for key, var in self._display_vars.items():
            config_dict[key] = bool(var.get())

        # Numeric and string fields
        try:
            config_dict['opacity'] = float(self._dimension_vars['opacity'].get())
        except (KeyError, ValueError):
            raise ValueError('Opacity must be a decimal between 0 and 1.')
        if not 0.0 <= config_dict['opacity'] <= 1.0:
            raise ValueError('Opacity must be between 0 and 1.')
        try:
            config_dict['font_size'] = int(self._dimension_vars['font_size'].get())
        except (KeyError, ValueError):
            raise ValueError('Font size must be an integer.')
        if config_dict['font_size'] <= 0:
            raise ValueError('Font size must be greater than zero.')
        try:
            config_dict['update_interval'] = float(self._dimension_vars['update_interval'].get())
        except (KeyError, ValueError):
            raise ValueError('Update interval must be a decimal number.')
        if config_dict['update_interval'] <= 0:
            raise ValueError('Update interval must be greater than zero.')

        config_dict['theme'] = self._dimension_vars['theme'].get()

        try:
            position = (
                int(self._dimension_vars['position_x'].get()),
                int(self._dimension_vars['position_y'].get())
            )
        except (KeyError, ValueError):
            raise ValueError('Position values must be integers.')
        try:
            size = (
                int(self._dimension_vars['width'].get()),
                int(self._dimension_vars['height'].get())
            )
        except (KeyError, ValueError):
            raise ValueError('Size values must be integers.')
        config_dict['position'] = position
        config_dict['size'] = size

        # Stats
        enabled = [stat for stat, var in self._stat_vars.items() if var.get()]
        config_dict['available_stats'] = list(sorted(self._stat_vars.keys()))
        config_dict['enabled_stats'] = enabled

        # Color conditions
        config_dict['stat_color_conditions'] = {
            stat: list(conditions)
            for stat, conditions in self._conditions.items()
        }

        # Popup stats
        if self._popup_selected:
            config_dict['popup_stats'] = list(self._popup_selected.get(0, tk.END))
        if 'popup_enabled' in self._display_vars:
            config_dict['popup_enabled'] = bool(self._display_vars['popup_enabled'].get())

        # Profile name
        profile_value = self._profile_name.get().strip() if self._profile_name else self._profile_name_value
        profile_name = profile_value or 'Custom'
        config_dict['profile_name'] = profile_name

        return self._config_cls.from_dict(config_dict)
