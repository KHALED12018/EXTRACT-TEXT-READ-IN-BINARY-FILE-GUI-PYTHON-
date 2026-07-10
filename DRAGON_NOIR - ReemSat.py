"""
================================================================================
                    KERNEL DECRYPTION ENGINE v3.0 - ULTIMATE
================================================================================
أداة متكاملة لاستخراج وتحليل وتصحيح النصوص من ملفات الكرنل والثنائيات
دمج بين Kernel Advanced Extractor و Binary Forge PRO

المطور: DRAGON_NOIR - ReemSat
الإصدار: 3.0 (الإصدار المتكامل النهائي)
================================================================================
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import re
import json
import csv
import hashlib
import binascii
import zlib
import tempfile
import time
from datetime import datetime
from pathlib import Path
import argparse
import sys
import struct

# =============================================================================
#                              نظام الإلغاء (Undo/Redo)
# =============================================================================

class UndoManager:
    """مدير عمليات التراجع والإعادة"""
    
    def __init__(self, max_history=100):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history
        self.current_snapshot = None
        
    def snapshot(self, data, description="", position=-1):
        snapshot = {
            'data': data.copy() if data else bytearray(),
            'description': description,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'position': position,
            'size': len(data) if data else 0
        }
        
        if self.current_snapshot is not None:
            self.undo_stack.append(self.current_snapshot)
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
        
        self.current_snapshot = snapshot
        self.redo_stack.clear()
        
    def undo(self):
        if not self.undo_stack:
            return None
            
        if self.current_snapshot is not None:
            self.redo_stack.append(self.current_snapshot)
            
        snapshot = self.undo_stack.pop()
        self.current_snapshot = snapshot
        return snapshot['data'].copy()
        
    def redo(self):
        if not self.redo_stack:
            return None
            
        if self.current_snapshot is not None:
            self.undo_stack.append(self.current_snapshot)
            
        snapshot = self.redo_stack.pop()
        self.current_snapshot = snapshot
        return snapshot['data'].copy()
        
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_snapshot = None


# =============================================================================
#                          نظام تصحيح النصوص المقلوبة المتقدم
# =============================================================================

class AdvancedTextReverser:
    """نظام متقدم لتصحيح النصوص المقلوبة مع دعم متعدد"""
    
    @staticmethod
    def reverse_string(text):
        """عكس النص بالكامل"""
        return text[::-1]
    
    @staticmethod
    def reverse_words(text):
        """عكس ترتيب الكلمات"""
        words = text.split()
        return ' '.join(reversed(words))
    
    @staticmethod
    def reverse_chars_in_words(text):
        """عكس الأحرف داخل كل كلمة"""
        words = text.split()
        return ' '.join(word[::-1] for word in words)
    
    @staticmethod
    def detect_reversed_text(text):
        """كشف النصوص المقلوبة مع حساب درجة الثقة"""
        if len(text) < 3:
            return False, 0.0
            
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
        
        if has_arabic:
            reversed_text = text[::-1]
            common_arabic = ['ال', 'و', 'من', 'في', 'على', 'إلى', 'ب', 'ك', 'ل', 'ما']
            score = 0
            for word in common_arabic:
                if word in text:
                    score += 2
                if word in reversed_text:
                    score += 1
            if score > 5:
                return True, min(0.9, score / 15)
        else:
            reversed_text = text[::-1]
            common_english = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'was', 'with']
            score = 0
            for word in common_english:
                if word.lower() in text.lower():
                    score += 2
                if word.lower() in reversed_text.lower():
                    score += 1
            if score > 5:
                return True, min(0.9, score / 15)
                
        return False, 0.0
    
    @staticmethod
    def smart_reverse(text):
        """تصحيح ذكي للنصوص المقلوبة"""
        is_reversed, confidence = AdvancedTextReverser.detect_reversed_text(text)
        
        if not is_reversed or confidence < 0.3:
            return text, False
        
        # تجربة طرق مختلفة واختيار الأفضل
        results = []
        
        r1 = AdvancedTextReverser.reverse_string(text)
        results.append(('full_reverse', r1))
        
        r2 = AdvancedTextReverser.reverse_words(text)
        results.append(('words_reverse', r2))
        
        r3 = AdvancedTextReverser.reverse_chars_in_words(text)
        results.append(('chars_reverse', r3))
        
        best = results[0]
        best_score = 0
        
        for method, result in results:
            score = 0
            if any('\u0600' <= c <= '\u06FF' for c in text):
                common_arabic = ['ال', 'و', 'من', 'في', 'على', 'إلى']
                for word in common_arabic:
                    if word in result:
                        score += 2
            else:
                common_english = ['the', 'and', 'for', 'are', 'but', 'not', 'you']
                for word in common_english:
                    if word.lower() in result.lower():
                        score += 2
            
            if score > best_score:
                best_score = score
                best = result
        
        return best, True


# =============================================================================
#                          محرك استخراج الكرنل المتقدم
# =============================================================================

class KernelExtractionEngine:
    """محرك متخصص لاستخراج وتحليل نصوص الكرنل"""
    
    def __init__(self):
        self.reverser = AdvancedTextReverser()
        self.patterns = {
            'kernel': re.compile(rb'[A-Za-z0-9_\-\.\s\/\:\=\%]{10,}'),
            'hex': re.compile(rb'[0-9A-Fa-f]{8,}'),
            'version': re.compile(rb'[0-9]+\.[0-9]+\.[0-9]+'),
            'path': re.compile(rb'[A-Za-z]:\\[^\s<>"{}|\\^`[\]]+'),
            'function': re.compile(rb'[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)'),
        }
        
    def extract_strings(self, data, min_length=10):
        """استخراج النصوص من البيانات الثنائية"""
        results = []
        positions = []
        
        for match in self.patterns['kernel'].finditer(data):
            raw = match.group()
            text = raw.decode('ascii', errors='ignore').strip()
            if len(text) >= min_length:
                results.append(text)
                positions.append(match.start())
                
        return results, positions
    
    def analyze_string(self, raw_bytes):
        """تحليل النص وتحديد نوعه"""
        try:
            plain_text = raw_bytes.decode('ascii', errors='ignore').strip()
        except:
            return 'SKIP', '', 0
        
        if len(plain_text) < 10:
            return 'SKIP', '', 0
        
        # المؤشرات
        reversed_indicators = ["MUNN", "RESU", "EMAN", "YALP", "ETAS", "TROPR", "KSED", "NoN"]
        standard_indicators = ["INFO", "VER ", "coms", "esa1", "esa2", "pcm_", "para", "CON", "RE", "DE"]
        
        if any(ind in plain_text for ind in reversed_indicators):
            fixed, _ = self.reverser.smart_reverse(plain_text)
            return 'REVERSED', fixed, 1
        
        if any(ind in plain_text for ind in standard_indicators):
            return 'STANDARD', plain_text, 2
        
        # تحليل إحصائي
        def calculate_score(text):
            score = 0
            common_prefixes = ["CON", "RE", "DE", "UN", "IN", "SYS", "PRO", "PAS", "KER", "NEL", "WIN", "LIN"]
            common_suffixes = ["ION", "ING", "ED", "MENT", "ABLE", "ITY", "WORD", "NAME", "SYS", "CTL"]
            
            if any(text.startswith(p) for p in common_prefixes): score += 3
            if any(text.endswith(s) for s in common_suffixes): score += 3
            
            vowels = set("AEIOUaeiou")
            consonants = set("BCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz")
            
            for i in range(len(text) - 2):
                if text[i] in consonants and text[i+1] in consonants and text[i+2] in consonants:
                    score -= 1
                    
            return score
        
        normal_score = calculate_score(plain_text.upper())
        
        try:
            fixed, was_fixed = self.reverser.smart_reverse(plain_text)
            reversed_score = calculate_score(fixed.upper()) if was_fixed else -999
        except:
            reversed_score = -999
        
        if reversed_score > normal_score + 2:
            return 'REVERSED', fixed, 3
        else:
            return 'STANDARD', plain_text, 4
    
    def extract_structured_data(self, data):
        """استخراج بيانات منظمة من الكرنل"""
        results = {
            'strings': [],
            'hex_values': [],
            'versions': [],
            'paths': [],
            'functions': []
        }
        
        # استخراج النصوص
        strings, _ = self.extract_strings(data)
        results['strings'] = strings
        
        # استخراج القيم السداسية
        for match in self.patterns['hex'].finditer(data):
            hex_val = match.group().decode('ascii', errors='ignore')
            if len(hex_val) >= 8:
                results['hex_values'].append(hex_val)
        
        # استخراج الإصدارات
        for match in self.patterns['version'].finditer(data):
            version = match.group().decode('ascii', errors='ignore')
            results['versions'].append(version)
        
        # استخراج المسارات
        for match in self.patterns['path'].finditer(data):
            path = match.group().decode('ascii', errors='ignore')
            results['paths'].append(path)
        
        # استخراج الدوال
        for match in self.patterns['function'].finditer(data):
            func = match.group().decode('ascii', errors='ignore')
            results['functions'].append(func)
        
        return results


# =============================================================================
#                          نظام تحليل الملفات
# =============================================================================

class FileFormatDetector:
    """كاشف تنسيقات الملفات"""
    
    MAGIC_BYTES = {
        'PE (Windows Kernel)': (b'MZ', 0),
        'ELF (Linux Kernel)': (b'\x7FELF', 0),
        'Mach-O (macOS Kernel)': (b'\xFE\xED\xFA', 0),
        'ZIP Archive': (b'PK\x03\x04', 0),
        'PDF Document': (b'%PDF', 0),
    }
    
    @classmethod
    def detect(cls, data):
        if not data:
            return "Empty/No Data"
            
        for format_name, (magic, offset) in cls.MAGIC_BYTES.items():
            if offset < len(data) and data[offset:offset+len(magic)] == magic:
                return format_name
                
        return "Unknown Binary"


# =============================================================================
#                          الواجهة الرسومية الرئيسية
# =============================================================================

class KernelUltimateExtractor(tk.Tk):
    """التطبيق الرئيسي - Kernel Decryption Engine v3.0"""
    
    VERSION = "3.0"
    
    def __init__(self):
        super().__init__()
        
        self.title(f"🐉 KERNEL DECRYPTION ENGINE v{self.VERSION} - ULTIMATE")
        self.geometry("1300x800")
        self.configure(bg="#0d1117")
        
        # الأنظمة الفرعية
        self.undo_manager = UndoManager()
        self.reverser = AdvancedTextReverser()
        self.kernel_engine = KernelExtractionEngine()
        
        # الحالة
        self.current_file = ""
        self.data = None
        self.modified = False
        self.auto_reverse = tk.BooleanVar(value=True)
        self.current_mode = "standard"  # standard, reversed, all
        
        # البيانات المستخرجة
        self.extracted_strings = []
        self.string_positions = []
        self.analyzed_results = []
        
        # الثيمات
        self.themes = {
            'dark': {
                'bg': '#0d1117', 'fg': '#c9d1d9', 'accent': '#58a6ff',
                'success': '#238636', 'warning': '#d29922', 'danger': '#f85149',
                'panel_bg': '#161b22', 'status_bg': '#0d1117'
            },
            'light': {
                'bg': '#f0f0f0', 'fg': '#000000', 'accent': '#0066cc',
                'success': '#22863a', 'warning': '#b08800', 'danger': '#cf222e',
                'panel_bg': '#ffffff', 'status_bg': '#e8e8e8'
            }
        }
        self.current_theme = 'dark'
        self.colors = self.themes['dark']
        
        # بناء الواجهة
        self.setup_ui()
        self.setup_bindings()
        
        # تحديث الحالة
        self.update_status("READY")
        
    def setup_ui(self):
        """بناء واجهة المستخدم"""
        # الشريط العلوي
        top_frame = tk.Frame(self, bg=self.colors['bg'])
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_frame, text="TARGET KERNEL:", bg=self.colors['bg'],
                fg=self.colors['accent'], font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.path_entry = tk.Entry(top_frame, bg=self.colors['panel_bg'],
                                   fg=self.colors['fg'], insertbackground=self.colors['fg'],
                                   font=("Consolas", 10), bd=1, relief="solid")
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)
        
        btn_open = tk.Button(top_frame, text="OPEN FILE", bg="#21262d", fg=self.colors['fg'],
                            activebackground="#30363d", activeforeground="#ffffff",
                            font=("Consolas", 10, "bold"), bd=1, relief="solid",
                            cursor="hand2", command=self.open_file)
        btn_open.pack(side=tk.LEFT, padx=5, ipadx=12)
        
        # أزرار التحكم الإضافية
        btn_reverse = tk.Button(top_frame, text="🔄 REVERSE", bg="#f85149", fg="#ffffff",
                               activebackground="#ff7b72", font=("Consolas", 10, "bold"),
                               bd=0, cursor="hand2", command=self.fix_reversed)
        btn_reverse.pack(side=tk.LEFT, padx=5, ipadx=12)
        
        btn_extract = tk.Button(top_frame, text="EXECUTE EXTRACT", bg="#238636", fg="#ffffff",
                               activebackground="#2ea043", font=("Consolas", 10, "bold"),
                               bd=0, cursor="hand2", command=self.execute_extraction)
        btn_extract.pack(side=tk.LEFT, padx=5, ipadx=18)
        
        # دفتر التبويبات
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # تبويب الاستخراج
        self.tab_extract = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(self.tab_extract, text=" 📝 String Extraction ")
        
        # تبويب التحليل المتقدم
        self.tab_analyze = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(self.tab_analyze, text=" 🔬 Advanced Analysis ")
        
        # تبويب الهيكس
        self.tab_hex = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(self.tab_hex, text=" 🔢 Hex Viewer ")
        
        # تبويب Bitwise Inverter
        self.tab_invert = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(self.tab_invert, text=" ⚡ Bitwise Inverter ")
        
        # بناء كل تبويب
        self.build_extract_tab()
        self.build_analyze_tab()
        self.build_hex_tab()
        self.build_invert_tab()
        
        # شريط الحالة
        self.status_bar = tk.Frame(self, bg=self.colors['status_bg'], height=30)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_bar, text="✅ READY", bg=self.colors['status_bg'],
                                     fg="#238636", font=("Consolas", 9))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.position_label = tk.Label(self.status_bar, text="🔍 POSITION: 0x00000000",
                                      bg=self.colors['status_bg'], fg="#8b949e",
                                      font=("Consolas", 9))
        self.position_label.pack(side=tk.RIGHT, padx=10)
        
        self.count_label = tk.Label(self.status_bar, text="📦 STRINGS: 0",
                                   bg=self.colors['status_bg'], fg="#58a6ff",
                                   font=("Consolas", 9))
        self.count_label.pack(side=tk.RIGHT, padx=20)
        
        # قائمة الأزرار التي يتم تعطيلها
        self.busy_buttons = [btn_open, btn_extract, btn_reverse]
        
    def build_extract_tab(self):
        """بناء تبويب الاستخراج"""
        # خيارات الاستخراج
        options_frame = tk.Frame(self.tab_extract, bg=self.colors['bg'])
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(options_frame, text="MIN LENGTH:", bg=self.colors['bg'],
                fg=self.colors['fg'], font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)
        
        self.min_length_var = tk.StringVar(value="10")
        min_length_spin = tk.Spinbox(options_frame, from_=3, to_=50, width=5,
                                    textvariable=self.min_length_var,
                                    bg=self.colors['panel_bg'], fg=self.colors['fg'],
                                    font=("Consolas", 10), bd=1, relief="solid")
        min_length_spin.pack(side=tk.LEFT, padx=5)
        
        tk.Label(options_frame, text="MODE:", bg=self.colors['bg'],
                fg=self.colors['fg'], font=("Consolas", 10)).pack(side=tk.LEFT, padx=(20, 5))
        
        self.mode_var = tk.StringVar(value="all")
        mode_combo = ttk.Combobox(options_frame, textvariable=self.mode_var,
                                 values=["all", "standard", "reversed"], width=12,
                                 state="readonly")
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # خيار التصحيح التلقائي
        self.auto_reverse_cb = tk.Checkbutton(options_frame, text="AUTO REVERSE",
                                             variable=self.auto_reverse,
                                             bg=self.colors['bg'], fg=self.colors['fg'],
                                             selectcolor=self.colors['bg'])
        self.auto_reverse_cb.pack(side=tk.LEFT, padx=20)
        
        # منطقة العرض
        display_frame = tk.Frame(self.tab_extract, bg=self.colors['panel_bg'], bd=1, relief="solid")
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(display_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(display_frame, bg=self.colors['bg'], fg="#58a6ff",
                                   insertbackground=self.colors['fg'],
                                   font=("Consolas", 11), bd=0,
                                   yscrollcommand=scrollbar.set)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # تنسيقات النص
        self.output_text.tag_config("standard", foreground="#8b949e")
        self.output_text.tag_config("reversed", foreground="#f85149")
        self.output_text.tag_config("decrypted", foreground="#58a6ff")
        self.output_text.tag_config("number", foreground="#d29922")
        self.output_text.tag_config("highlight", background="#238636", foreground="#ffffff")
        
    def build_analyze_tab(self):
        """بناء تبويب التحليل المتقدم"""
        # إطار التحليل
        analyze_frame = tk.Frame(self.tab_analyze, bg=self.colors['bg'])
        analyze_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # أزرار التحليل
        btn_frame = tk.Frame(analyze_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        btn_analyze_strings = tk.Button(btn_frame, text="📊 ANALYZE STRINGS",
                                       bg="#21262d", fg=self.colors['fg'],
                                       activebackground="#30363d",
                                       font=("Consolas", 10, "bold"),
                                       bd=1, relief="solid", cursor="hand2",
                                       command=self.analyze_strings)
        btn_analyze_strings.pack(side=tk.LEFT, padx=5, ipadx=12)
        
        btn_detect_patterns = tk.Button(btn_frame, text="🎯 DETECT PATTERNS",
                                       bg="#21262d", fg=self.colors['fg'],
                                       activebackground="#30363d",
                                       font=("Consolas", 10, "bold"),
                                       bd=1, relief="solid", cursor="hand2",
                                       command=self.detect_patterns)
        btn_detect_patterns.pack(side=tk.LEFT, padx=5, ipadx=12)
        
        btn_export = tk.Button(btn_frame, text="📤 EXPORT RESULTS",
                               bg="#1f6feb", fg="#ffffff",
                               activebackground="#388bfd",
                               font=("Consolas", 10, "bold"),
                               bd=0, cursor="hand2",
                               command=self.export_analysis)
        btn_export.pack(side=tk.LEFT, padx=5, ipadx=12)
        
        # عرض النتائج
        result_frame = tk.Frame(analyze_frame, bg=self.colors['panel_bg'], bd=1, relief="solid")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.analyze_text = tk.Text(result_frame, bg=self.colors['bg'],
                                    fg=self.colors['fg'],
                                    insertbackground=self.colors['fg'],
                                    font=("Consolas", 10), bd=0,
                                    yscrollcommand=scrollbar.set)
        self.analyze_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.analyze_text.yview)
        
        self.analyze_text.tag_config("header", foreground="#58a6ff", font=("Consolas", 11, "bold"))
        self.analyze_text.tag_config("value", foreground="#d29922")
        self.analyze_text.tag_config("found", foreground="#238636")
        
    def build_hex_tab(self):
        """بناء تبويب عرض الهيكس"""
        hex_frame = tk.Frame(self.tab_hex, bg=self.colors['bg'])
        hex_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # أزرار التحكم
        btn_frame = tk.Frame(hex_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=5)
        
        btn_hex_prev = tk.Button(btn_frame, text="◀ PREV", bg="#21262d", fg=self.colors['fg'],
                                 activebackground="#30363d", font=("Consolas", 9, "bold"),
                                 bd=1, relief="solid", cursor="hand2", command=self.hex_prev)
        btn_hex_prev.pack(side=tk.LEFT, padx=5, ipadx=10)
        
        btn_hex_next = tk.Button(btn_frame, text="NEXT ▶", bg="#21262d", fg=self.colors['fg'],
                                 activebackground="#30363d", font=("Consolas", 9, "bold"),
                                 bd=1, relief="solid", cursor="hand2", command=self.hex_next)
        btn_hex_next.pack(side=tk.LEFT, padx=5, ipadx=10)
        
        btn_hex_goto = tk.Button(btn_frame, text="GOTO", bg="#21262d", fg=self.colors['fg'],
                                 activebackground="#30363d", font=("Consolas", 9, "bold"),
                                 bd=1, relief="solid", cursor="hand2", command=self.hex_goto)
        btn_hex_goto.pack(side=tk.LEFT, padx=5, ipadx=10)
        
        self.hex_offset_label = tk.Label(btn_frame, text="OFFSET: 0x00000000",
                                         bg=self.colors['bg'], fg="#58a6ff",
                                         font=("Consolas", 9))
        self.hex_offset_label.pack(side=tk.RIGHT, padx=10)
        
        # عرض الهيكس
        hex_display = tk.Frame(hex_frame, bg=self.colors['panel_bg'], bd=1, relief="solid")
        hex_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(hex_display)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.hex_text = tk.Text(hex_display, bg=self.colors['bg'], fg="#00ff00",
                                insertbackground=self.colors['fg'],
                                font=("Consolas", 10), bd=0,
                                yscrollcommand=scrollbar.set)
        self.hex_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.hex_text.yview)
        
        self.hex_text.tag_config("offset", foreground="#8b949e")
        self.hex_text.tag_config("hex", foreground="#00ff00")
        self.hex_text.tag_config("ascii", foreground="#58a6ff")
        self.hex_text.tag_config("highlight", background="#238636", foreground="#ffffff")
        
        self.hex_offset = 0
        self.hex_chunk = 4096
        
    def build_invert_tab(self):
        """بناء تبويب Bitwise Inverter"""
        invert_frame = tk.Frame(self.tab_invert, bg=self.colors['bg'])
        invert_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        title = tk.Label(invert_frame, text="⚡ RAW BITWISE INVERSION UTILITY",
                         bg=self.colors['bg'], fg="#f85149",
                         font=("Consolas", 16, "bold"))
        title.pack(pady=20)
        
        description = tk.Label(invert_frame,
                               text="Perform byte-level bitwise NOT (0xFF XOR) on entire firmware binary",
                               bg=self.colors['bg'], fg="#8b949e",
                               font=("Consolas", 11))
        description.pack(pady=10)
        
        btn_invert = tk.Button(invert_frame, text="INVERT FIRMWARE BYTES",
                               bg="#f85149", fg="#0d1117",
                               activebackground="#ff7b72",
                               font=("Consolas", 14, "bold"),
                               bd=0, cursor="hand2", padx=30, pady=15,
                               command=self.execute_invert)
        btn_invert.pack(pady=30)
        
        self.invert_status = tk.Label(invert_frame, text="STATUS: IDLE - WAITING FOR INPUT",
                                      bg=self.colors['bg'], fg="#8b949e",
                                      font=("Consolas", 10, "italic"))
        self.invert_status.pack(pady=10)
        
        # معلومات إضافية
        info_frame = tk.Frame(invert_frame, bg=self.colors['panel_bg'], bd=1, relief="solid")
        info_frame.pack(fill=tk.X, pady=20)
        
        info_text = """
BITWISE INVERSION OPERATION:
  • Each byte is XORed with 0xFF (bitwise NOT)
  • Original: 0x00 → 0xFF, 0x01 → 0xFE, ..., 0xFF → 0x00
  • Useful for decrypting XOR-encrypted firmware
  • Output saved as separate binary file
        """
        
        info_label = tk.Label(info_frame, text=info_text, bg=self.colors['panel_bg'],
                              fg="#8b949e", font=("Consolas", 10), justify=tk.LEFT)
        info_label.pack(padx=20, pady=15, anchor=tk.W)
        
    def setup_bindings(self):
        """إعداد اختصارات لوحة المفاتيح"""
        self.bind('<Control-o>', lambda e: self.open_file())
        self.bind('<Control-s>', lambda e: self.save_file())
        self.bind('<Control-f>', lambda e: self.search_in_output())
        self.bind('<Escape>', lambda e: self.clear_output())
        
    # ===================================================================
    #                         دوال الملفات
    # ===================================================================
    
    def open_file(self):
        """فتح ملف"""
        file = filedialog.askopenfilename(
            title="Open Kernel/Binary File",
            filetypes=[("All Files", "*.*"), ("Kernel", "*.exe *.dll *.sys"), ("Binary", "*.bin *.rom")]
        )
        if not file:
            return
            
        try:
            self.update_status("LOADING...")
            
            with open(file, "rb") as f:
                raw = f.read()
                
            self.current_file = file
            self.data = bytearray(raw)
            self.modified = False
            
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file)
            
            self.update_status(f"LOADED: {os.path.basename(file)} ({len(self.data):,} bytes)")
            self.position_label.config(text=f"📁 {os.path.basename(file)}")
            
            # تحديث عرض الهيكس
            self.update_hex_view()
            
            # استخراج تلقائي
            self.execute_extraction()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            self.update_status("ERROR")
            
    def save_file(self):
        """حفظ الملف المعدل"""
        if self.data is None:
            messagebox.showwarning("Warning", "No file to save")
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".bin",
            initialfile=f"modified_{os.path.basename(self.current_file) if self.current_file else 'output.bin'}"
        )
        if not save_path:
            return
            
        try:
            with open(save_path, "wb") as f:
                f.write(self.data)
                
            self.modified = False
            messagebox.showinfo("Success", f"File saved to: {save_path}")
            self.update_status("SAVED")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            
    # ===================================================================
    #                         محرك الاستخراج
    # ===================================================================
    
    def execute_extraction(self):
        """تنفيذ عملية الاستخراج"""
        if self.data is None:
            messagebox.showwarning("Warning", "Please load a kernel file first")
            return
            
        self.set_busy(True)
        self.update_status("EXTRACTING...")
        self.output_text.delete("1.0", tk.END)
        
        def worker():
            try:
                min_length = int(self.min_length_var.get())
                mode = self.mode_var.get()
                
                extracted_strings, positions = self.kernel_engine.extract_strings(
                    bytes(self.data), min_length
                )
                
                self.extracted_strings = []
                self.string_positions = []
                self.analyzed_results = []
                
                count = 0
                reversed_count = 0
                standard_count = 0
                
                for raw_str, pos in zip(extracted_strings, positions):
                    raw_bytes = raw_str.encode('ascii', errors='ignore')
                    decision, processed, _ = self.kernel_engine.analyze_string(raw_bytes)
                    
                    if decision == 'SKIP':
                        continue
                    
                    if self.auto_reverse.get():
                        processed, was_fixed = self.reverser.smart_reverse(processed)
                        if was_fixed:
                            decision = 'REVERSED'
                    
                    if mode == 'standard' and decision != 'STANDARD':
                        continue
                    if mode == 'reversed' and decision != 'REVERSED':
                        continue
                    
                    self.extracted_strings.append(processed)
                    self.string_positions.append(pos)
                    self.analyzed_results.append({
                        'text': processed,
                        'position': pos,
                        'type': decision
                    })
                    
                    # عرض في الواجهة
                    if decision == 'REVERSED':
                        self.output_text.insert(tk.END, f"[DECRYPTED] -> {processed}\n", "decrypted")
                        reversed_count += 1
                    else:
                        self.output_text.insert(tk.END, f"[STANDARD]  -> {processed}\n", "standard")
                        standard_count += 1
                    
                    count += 1
                
                def done():
                    self.count_label.config(text=f"📦 STRINGS: {count} (↻{reversed_count} ⬜{standard_count})")
                    self.update_status(f"EXTRACTED: {count} strings ({reversed_count} reversed)")
                    self.set_busy(False)
                    
                self.after(0, done)
                
            except Exception as e:
                def error():
                    self.set_busy(False)
                    self.update_status("ERROR")
                    messagebox.showerror("Extraction Error", str(e))
                self.after(0, error)
                
        threading.Thread(target=worker, daemon=True).start()
        
    # ===================================================================
    #                         تصحيح النصوص المقلوبة
    # ===================================================================
    
    def fix_reversed(self):
        """تصحيح النصوص المقلوبة في النتائج الحالية"""
        if not self.extracted_strings:
            messagebox.showwarning("Warning", "No strings extracted yet")
            return
            
        self.set_busy(True)
        self.update_status("FIXING REVERSED...")
        
        fixed_count = 0
        new_strings = []
        new_positions = []
        new_results = []
        
        for idx, text in enumerate(self.extracted_strings):
            fixed_text, was_fixed = self.reverser.smart_reverse(text)
            if was_fixed:
                fixed_count += 1
            new_strings.append(fixed_text)
            if idx < len(self.string_positions):
                new_positions.append(self.string_positions[idx])
            new_results.append({
                'text': fixed_text,
                'position': self.string_positions[idx] if idx < len(self.string_positions) else -1,
                'type': 'REVERSED' if was_fixed else 'STANDARD'
            })
        
        self.extracted_strings = new_strings
        self.string_positions = new_positions
        self.analyzed_results = new_results
        
        # إعادة عرض النتائج
        self.output_text.delete("1.0", tk.END)
        for result in new_results:
            if result['type'] == 'REVERSED':
                self.output_text.insert(tk.END, f"[DECRYPTED] -> {result['text']}\n", "decrypted")
            else:
                self.output_text.insert(tk.END, f"[STANDARD]  -> {result['text']}\n", "standard")
        
        self.count_label.config(text=f"📦 STRINGS: {len(new_strings)} (↻{fixed_count} fixed)")
        self.update_status(f"FIXED: {fixed_count} reversed strings")
        self.set_busy(False)
        
        messagebox.showinfo("Success", f"Fixed {fixed_count} reversed strings")
        
    # ===================================================================
    #                         تحليل متقدم
    # ===================================================================
    
    def analyze_strings(self):
        """تحليل متقدم للنصوص المستخرجة"""
        if not self.extracted_strings:
            messagebox.showwarning("Warning", "No strings to analyze")
            return
            
        self.analyze_text.delete("1.0", tk.END)
        self.analyze_text.insert(tk.END, "📊 STRING ANALYSIS REPORT\n", "header")
        self.analyze_text.insert(tk.END, "=" * 60 + "\n\n", "header")
        
        # إحصائيات أساسية
        total = len(self.extracted_strings)
        chars = sum(len(s) for s in self.extracted_strings)
        avg = chars / total if total > 0 else 0
        
        self.analyze_text.insert(tk.END, f"📝 Total Strings: ", "header")
        self.analyze_text.insert(tk.END, f"{total}\n", "value")
        
        self.analyze_text.insert(tk.END, f"📊 Total Characters: ", "header")
        self.analyze_text.insert(tk.END, f"{chars}\n", "value")
        
        self.analyze_text.insert(tk.END, f"📈 Average Length: ", "header")
        self.analyze_text.insert(tk.END, f"{avg:.1f}\n\n", "value")
        
        # تحليل الطول
        length_groups = {}
        for text in self.extracted_strings:
            length = len(text)
            group = length // 10 * 10
            key = f"{group}-{group+9}"
            length_groups[key] = length_groups.get(key, 0) + 1
        
        self.analyze_text.insert(tk.END, "📏 Length Distribution:\n", "header")
        for key, count in sorted(length_groups.items()):
            bar = "█" * min(count, 50)
            self.analyze_text.insert(tk.END, f"  {key}: {count:4d} {bar}\n", "value")
        
        # تحليل الأحرف
        self.analyze_text.insert(tk.END, "\n🔤 Character Analysis:\n", "header")
        
        all_text = ''.join(self.extracted_strings)
        char_counts = {}
        for c in all_text:
            if c.isprintable():
                char_counts[c] = char_counts.get(c, 0) + 1
        
        most_common = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        self.analyze_text.insert(tk.END, "  Most Common Characters:\n", "header")
        for char, count in most_common:
            if char in ' \t\n':
                display = repr(char)
            else:
                display = char
            self.analyze_text.insert(tk.END, f"    '{display}': {count}\n", "value")
        
    def detect_patterns(self):
        """كشف الأنماط الخاصة في النصوص"""
        if not self.extracted_strings:
            messagebox.showwarning("Warning", "No strings to analyze")
            return
            
        patterns = {
            'URL': r'https?://[^\s<>"{}|\\^`[\]]+',
            'IP Address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'Email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'File Path': r'[A-Za-z]:\\[^\s<>"{}|\\^`[\]]+',
            'MD5 Hash': r'\b[a-f0-9]{32}\b',
            'SHA1 Hash': r'\b[a-f0-9]{40}\b',
            'Version': r'\b\d+\.\d+\.\d+(?:\.\d+)?\b',
            'GUID': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'Base64': r'[A-Za-z0-9+/]{4,}(?:={1,2})?',
        }
        
        self.analyze_text.delete("1.0", tk.END)
        self.analyze_text.insert(tk.END, "🎯 PATTERN DETECTION RESULTS\n", "header")
        self.analyze_text.insert(tk.END, "=" * 60 + "\n\n", "header")
        
        found_any = False
        
        for pattern_name, pattern in patterns.items():
            matches = []
            for text in self.extracted_strings:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    matches.extend(found)
            
            if matches:
                found_any = True
                self.analyze_text.insert(tk.END, f"🔍 {pattern_name} ({len(matches)} matches):\n", "header")
                for match in matches[:20]:
                    self.analyze_text.insert(tk.END, f"    {match}\n", "found")
                if len(matches) > 20:
                    self.analyze_text.insert(tk.END, f"    ... and {len(matches)-20} more\n", "value")
                self.analyze_text.insert(tk.END, "\n")
        
        if not found_any:
            self.analyze_text.insert(tk.END, "No patterns detected in the extracted strings.\n", "value")
    
    def export_analysis(self):
        """تصدير نتائج التحليل"""
        if not self.extracted_strings:
            messagebox.showwarning("Warning", "No data to export")
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
            initialfile=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if not save_path:
            return
            
        try:
            data = {
                'file': os.path.basename(self.current_file) if self.current_file else None,
                'timestamp': datetime.now().isoformat(),
                'total_strings': len(self.extracted_strings),
                'strings': self.analyzed_results
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            messagebox.showinfo("Success", f"Analysis exported to: {save_path}")
            self.update_status("EXPORTED")
            
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    # ===================================================================
    #                         عرض الهيكس
    # ===================================================================
    
    def update_hex_view(self, offset=None):
        """تحديث عرض الهيكس"""
        if self.data is None:
            return
            
        if offset is not None:
            self.hex_offset = offset
            
        self.hex_text.delete("1.0", tk.END)
        
        start = self.hex_offset
        end = min(len(self.data), start + self.hex_chunk)
        
        for i in range(start, end, 16):
            chunk = self.data[i:i+16]
            offset_str = f"0x{i:08x}: "
            self.hex_text.insert(tk.END, offset_str, "offset")
            
            hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(48)
            self.hex_text.insert(tk.END, hex_part, "hex")
            
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            self.hex_text.insert(tk.END, f"  |{ascii_part}|\n", "ascii")
        
        total_pages = max(1, (len(self.data) + self.hex_chunk - 1) // self.hex_chunk)
        current_page = start // self.hex_chunk + 1
        self.hex_offset_label.config(text=f"OFFSET: 0x{start:08x} [{current_page}/{total_pages}]")
        
    def hex_prev(self):
        """الصفحة السابقة"""
        if self.hex_offset - self.hex_chunk >= 0:
            self.hex_offset -= self.hex_chunk
            self.update_hex_view()
            
    def hex_next(self):
        """الصفحة التالية"""
        if self.hex_offset + self.hex_chunk < len(self.data):
            self.hex_offset += self.hex_chunk
            self.update_hex_view()
            
    def hex_goto(self):
        """الانتقال إلى موضع"""
        dialog = tk.Toplevel(self)
        dialog.title("Goto Address")
        dialog.geometry("300x120")
        dialog.configure(bg=self.colors['bg'])
        
        tk.Label(dialog, text="Enter offset (hex):", bg=self.colors['bg'],
                fg=self.colors['fg'], font=("Consolas", 10)).pack(pady=10)
        
        entry = tk.Entry(dialog, bg=self.colors['panel_bg'], fg=self.colors['fg'],
                         font=("Consolas", 10))
        entry.pack(pady=5, padx=20, fill=tk.X)
        entry.insert(0, "0x0000")
        
        def do_goto():
            try:
                text = entry.get().strip()
                if text.startswith('0x'):
                    offset = int(text[2:], 16)
                else:
                    offset = int(text, 16)
                
                if 0 <= offset < len(self.data):
                    page = (offset // self.hex_chunk) * self.hex_chunk
                    self.hex_offset = page
                    self.update_hex_view()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Warning", "Offset out of range")
            except ValueError:
                messagebox.showwarning("Warning", "Invalid hex value")
        
        btn_frame = tk.Frame(dialog, bg=self.colors['bg'])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="GO", bg="#238636", fg="#ffffff",
                 activebackground="#2ea043", font=("Consolas", 10, "bold"),
                 bd=0, cursor="hand2", command=do_goto).pack(side=tk.LEFT, padx=5, ipadx=20)
        
        tk.Button(btn_frame, text="CANCEL", bg="#21262d", fg=self.colors['fg'],
                 activebackground="#30363d", font=("Consolas", 10, "bold"),
                 bd=1, relief="solid", cursor="hand2",
                 command=dialog.destroy).pack(side=tk.LEFT, padx=5, ipadx=15)
        
        entry.bind("<Return>", lambda e: do_goto())
        entry.focus()
        
    # ===================================================================
    #                         Bitwise Inverter
    # ===================================================================
    
    def execute_invert(self):
        """تنفيذ عملية Bitwise Inversion"""
        if self.data is None:
            messagebox.showwarning("Warning", "Please load a kernel file first")
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".bin",
            filetypes=[("Binary Files", "*.bin"), ("All Files", "*.*")],
            initialfile=f"inverted_{os.path.basename(self.current_file) if self.current_file else 'output.bin'}"
        )
        if not save_path:
            return
            
        try:
            self.invert_status.config(text="INVERTING...", fg="#d29922")
            
            inverted = bytearray(b ^ 0xFF for b in self.data)
            
            with open(save_path, "wb") as f:
                f.write(inverted)
                
            self.invert_status.config(text=f"SUCCESS: INVERTED SAVED TO {os.path.basename(save_path)}",
                                      fg="#238636")
            messagebox.showinfo("Success", f"Bitwise inversion completed!\nSaved to: {save_path}")
            self.update_status("INVERTED")
            
        except Exception as e:
            self.invert_status.config(text=f"ERROR: {str(e)}", fg="#f85149")
            messagebox.showerror("Error", f"Inversion failed: {str(e)}")
    
    # ===================================================================
    #                         دوال مساعدة
    # ===================================================================
    
    def set_busy(self, busy):
        """تعطيل/تفعيل الأزرار"""
        state = tk.DISABLED if busy else tk.NORMAL
        for btn in self.busy_buttons:
            try:
                btn.config(state=state)
            except:
                pass
        if busy:
            self.config(cursor="watch")
        else:
            self.config(cursor="")
            
    def update_status(self, status):
        """تحديث شريط الحالة"""
        self.status_label.config(text=f"✅ {status}")
        self.update()
        
    def search_in_output(self):
        """بحث في منطقة النتائج"""
        dialog = tk.Toplevel(self)
        dialog.title("Search")
        dialog.geometry("400x100")
        dialog.configure(bg=self.colors['bg'])
        
        tk.Label(dialog, text="Search for:", bg=self.colors['bg'],
                fg=self.colors['fg']).pack(pady=5)
        
        entry = tk.Entry(dialog, bg=self.colors['panel_bg'], fg=self.colors['fg'])
        entry.pack(pady=5, padx=20, fill=tk.X)
        
        def do_search():
            query = entry.get().strip()
            if query:
                self.output_text.tag_remove("highlight", "1.0", tk.END)
                start = "1.0"
                while True:
                    pos = self.output_text.search(query, start, tk.END, nocase=True)
                    if not pos:
                        break
                    end = f"{pos}+{len(query)}c"
                    self.output_text.tag_add("highlight", pos, end)
                    self.output_text.see(pos)
                    start = end
                dialog.destroy()
        
        entry.bind("<Return>", lambda e: do_search())
        btn_frame = tk.Frame(dialog, bg=self.colors['bg'])
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="SEARCH", bg="#238636", fg="#ffffff",
                 command=do_search).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="CANCEL", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        entry.focus()
        
    def clear_output(self):
        """مسح منطقة النتائج"""
        self.output_text.delete("1.0", tk.END)


# =============================================================================
#                              نقطة الدخول الرئيسية
# =============================================================================

def main():
    """نقطة الدخول الرئيسية للتطبيق"""
    app = KernelUltimateExtractor()
    
    def on_closing():
        app.destroy()
        
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()