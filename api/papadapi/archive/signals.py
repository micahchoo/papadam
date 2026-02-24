"""
archive/signals.py — custom signals fired by the archive app.

Signals are the clean way to let higher-level apps (annotate, exhibit, …)
react to archive events without creating an upward import dependency.
"""

from django.dispatch import Signal

# Fired when a MediaStore item is duplicated via the copy endpoint.
# kwargs: old_uuid (str), new_uuid (str)
media_copied = Signal()
