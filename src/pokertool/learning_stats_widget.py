#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Learning System Statistics Widget for GUI
==========================================

PyQt6 widget to display scraper learning system statistics in real-time.

Usage:
    from pokertool.learning_stats_widget import LearningStatsWidget

    widget = LearningStatsWidget(scraper)
    layout.addWidget(widget)
"""

import logging
from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QGroupBox, QProgressBar, QPushButton, QTextEdit
    )
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # Dummy classes for type hints
    QWidget = object
    QVBoxLayout = object
    QHBoxLayout = object
    QLabel = object
    QGroupBox = object
    QProgressBar = object
    QPushButton = object
    QTextEdit = object

logger = logging.getLogger(__name__)


class LearningStatsWidget(QWidget):
    """
    Widget displaying learning system statistics.

    Shows:
    - Overall learning health score
    - Recent detection performance
    - OCR strategy rankings
    - Cache performance
    - Environment profile info
    """

    def __init__(self, scraper=None, parent=None):
        """
        Initialize learning stats widget.

        Args:
            scraper: PokerScreenScraper instance with learning system
            parent: Parent widget
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available")

        super().__init__(parent)
        self.scraper = scraper

        # UI Elements
        self.health_label = None
        self.health_bar = None
        self.stats_text = None
        self.refresh_button = None

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_interval = 5000  # Update every 5 seconds

        self._init_ui()

        # Start automatic updates
        if self.scraper and self.scraper.learning_system:
            self.update_timer.start(self.update_interval)
            self.update_stats()  # Initial update

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🧠 Learning System")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_stats)
        header_layout.addWidget(self.refresh_button)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Learning Health Score
        health_group = QGroupBox("Learning Health")
        health_layout = QVBoxLayout()

        self.health_label = QLabel("Health Score: --")
        health_layout.addWidget(self.health_label)

        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(0)
        health_layout.addWidget(self.health_bar)

        health_group.setLayout(health_layout)
        layout.addWidget(health_group)

        # Statistics Display
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(300)
        stats_layout.addWidget(self.stats_text)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Add stretch to push everything to top
        layout.addStretch()

        self.setLayout(layout)

    def set_scraper(self, scraper):
        """
        Set the scraper instance.

        Args:
            scraper: PokerScreenScraper instance
        """
        self.scraper = scraper

        if self.scraper and self.scraper.learning_system:
            if not self.update_timer.isActive():
                self.update_timer.start(self.update_interval)
            self.update_stats()
        else:
            self.update_timer.stop()
            self._show_unavailable()

    def update_stats(self):
        """Update displayed statistics."""
        if not self.scraper or not self.scraper.learning_system:
            self._show_unavailable()
            return

        try:
            report = self.scraper.get_learning_report()
            if not report:
                self._show_unavailable()
                return

            # Calculate health score
            health_score = self._calculate_health_score(report)

            # Update health display
            self.health_label.setText(f"Health Score: {health_score:.0f}/100")
            self.health_bar.setValue(int(health_score))

            # Set color based on score
            if health_score >= 70:
                color = "green"
            elif health_score >= 40:
                color = "orange"
            else:
                color = "red"

            self.health_bar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)

            # Update stats text
            stats_html = self._format_stats_html(report, health_score)
            self.stats_text.setHtml(stats_html)

        except Exception as e:
            logger.error(f"Failed to update learning stats: {e}")
            self._show_error(str(e))

    def _calculate_health_score(self, report: Dict[str, Any]) -> float:
        """
        Calculate overall learning health score (0-100).

        Args:
            report: Learning system report

        Returns:
            Health score 0-100
        """
        score = 0.0

        # Environment profiles (20 points)
        env_profiles = report.get('environment_profiles', {}).get('profiles', [])
        if env_profiles:
            avg_success = sum(p['success_rate'] for p in env_profiles) / len(env_profiles)
            score += avg_success * 20

        # Recent performance (30 points)
        recent = report.get('recent_performance', {})
        if recent:
            score += recent.get('success_rate', 0) * 30

        # CDP learning (20 points)
        cdp = report.get('cdp_learning', {})
        if cdp.get('total_cdp_samples', 0) > 0:
            score += 20

        # User feedback (10 points)
        feedback = report.get('user_feedback', {})
        if feedback.get('total_feedback', 0) > 10:
            score += 10

        # OCR strategies (10 points)
        ocr_strats = report.get('ocr_strategies', {})
        if ocr_strats:
            score += 10

        # Caching (10 points)
        caching = report.get('caching', {})
        if caching.get('hit_rate', 0) > 0.2:
            score += caching['hit_rate'] * 10

        return min(100.0, score)

    def _format_stats_html(self, report: Dict[str, Any], health_score: float) -> str:
        """
        Format statistics as HTML.

        Args:
            report: Learning system report
            health_score: Calculated health score

        Returns:
            HTML string
        """
        html = "<html><body style='font-family: monospace; font-size: 10pt;'>"

        # Health status
        if health_score >= 70:
            status = "🌟 <span style='color: green;'><b>Excellent</b></span>"
            tip = "The system is well-trained for your environment."
        elif health_score >= 40:
            status = "✓ <span style='color: orange;'><b>Learning</b></span>"
            tip = "The system is adapting to your setup."
        else:
            status = "⚠ <span style='color: red;'><b>Needs Data</b></span>"
            tip = "Continue using to improve performance."

        html += f"<p><b>Status:</b> {status}</p>"
        html += f"<p style='color: gray; font-size: 9pt;'>{tip}</p>"
        html += "<hr>"

        # Recent Performance
        recent = report.get('recent_performance', {})
        if recent:
            html += "<p><b>📈 Recent Performance:</b></p>"
            html += f"<ul>"
            html += f"<li>Success Rate: <b>{recent.get('success_rate', 0):.1%}</b></li>"
            html += f"<li>Avg Time: <b>{recent.get('avg_time_ms', 0):.1f}ms</b></li>"
            html += f"<li>Samples: {recent.get('sample_size', 0)}</li>"
            html += f"</ul>"

        # Environment Profiles
        env = report.get('environment_profiles', {})
        if env.get('total', 0) > 0:
            html += "<p><b>📊 Environments:</b></p>"
            html += f"<ul>"
            html += f"<li>Profiles: {env['total']}</li>"
            profiles = env.get('profiles', [])
            if profiles:
                best = profiles[0]
                html += f"<li>Best Success: {best['success_rate']:.1%}</li>"
            html += f"</ul>"

        # OCR Strategies
        ocr_strats = report.get('ocr_strategies', {})
        if ocr_strats:
            html += "<p><b>🎯 Best OCR Strategies:</b></p>"
            for ext_type, strategies in list(ocr_strats.items())[:2]:  # Show first 2 types
                if strategies:
                    best_strat = strategies[0]
                    html += f"<ul>"
                    html += f"<li>{ext_type}: <b>{best_strat['strategy_id']}</b> "
                    html += f"({best_strat['success_rate']:.1%})</li>"
                    html += f"</ul>"

        # Caching
        caching = report.get('caching', {})
        if caching and caching.get('hit_rate', 0) > 0:
            html += "<p><b>⚡ Cache Performance:</b></p>"
            html += f"<ul>"
            html += f"<li>Hit Rate: <b>{caching['hit_rate']:.1%}</b></li>"
            html += f"<li>Cache Size: {caching['cache_size']} entries</li>"
            speedup = 1 / (1 - caching['hit_rate'] * 0.8)
            html += f"<li>Est. Speedup: <b>{speedup:.1f}x</b></li>"
            html += f"</ul>"

        # CDP Learning
        cdp = report.get('cdp_learning', {})
        if cdp.get('total_cdp_samples', 0) > 0:
            html += "<p><b>🎓 CDP Learning:</b></p>"
            html += f"<ul>"
            html += f"<li>Samples: {cdp['total_cdp_samples']}</li>"
            acc_by_type = cdp.get('accuracy_by_type', {})
            if acc_by_type:
                avg_acc = sum(s['avg_accuracy'] for s in acc_by_type.values()) / len(acc_by_type)
                html += f"<li>Avg Accuracy: <b>{avg_acc:.1%}</b></li>"
            html += f"</ul>"

        # Learned Patterns
        patterns = report.get('learned_patterns', {})
        if patterns.get('player_names_count', 0) > 0:
            html += "<p><b>🔍 Learned Patterns:</b></p>"
            html += f"<ul>"
            html += f"<li>Player Names: {patterns['player_names_count']}</li>"
            html += f"</ul>"

        html += "</body></html>"
        return html

    def _show_unavailable(self):
        """Show unavailable message."""
        self.health_label.setText("Health Score: Unavailable")
        self.health_bar.setValue(0)
        self.stats_text.setHtml("""
            <html><body style='font-family: monospace; font-size: 10pt;'>
            <p style='color: gray;'>Learning system not available or disabled.</p>
            <p>Enable learning to see statistics.</p>
            </body></html>
        """)

    def _show_error(self, error_msg: str):
        """Show error message."""
        self.health_label.setText("Health Score: Error")
        self.health_bar.setValue(0)
        self.stats_text.setHtml(f"""
            <html><body style='font-family: monospace; font-size: 10pt;'>
            <p style='color: red;'><b>Error loading statistics:</b></p>
            <p>{error_msg}</p>
            </body></html>
        """)

    def stop_updates(self):
        """Stop automatic updates."""
        self.update_timer.stop()

    def start_updates(self):
        """Start automatic updates."""
        if self.scraper and self.scraper.learning_system:
            self.update_timer.start(self.update_interval)

    def set_update_interval(self, interval_ms: int):
        """
        Set update interval.

        Args:
            interval_ms: Update interval in milliseconds
        """
        self.update_interval = interval_ms
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.update_timer.start(interval_ms)


def create_learning_stats_widget(scraper=None, parent=None):
    """
    Create learning stats widget.

    Args:
        scraper: PokerScreenScraper instance
        parent: Parent widget

    Returns:
        LearningStatsWidget instance
    """
    if not PYQT_AVAILABLE:
        logger.error("PyQt6 not available - cannot create learning stats widget")
        return None

    return LearningStatsWidget(scraper, parent)


# Example usage for testing
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create widget without scraper (will show unavailable)
    widget = LearningStatsWidget()
    widget.setWindowTitle("Learning System Statistics")
    widget.resize(400, 600)
    widget.show()

    sys.exit(app.exec())
