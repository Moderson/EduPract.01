from src.system.clipboard import ClipboardGuard


class FakeClipboard:
    def __init__(self):
        self.text = ""
        self.scheduled = []

    def set_text(self, text):
        self.text = text

    def clear(self):
        self.text = ""

    def schedule(self, delay, callback):
        item = {"delay": delay, "callback": callback, "cancelled": False}
        self.scheduled.append(item)

        def cancel():
            item["cancelled"] = True

        return cancel

    def fire_last(self):
        item = self.scheduled[-1]
        if not item["cancelled"]:
            item["callback"]()


def make_guard(clip, timeout=30.0):
    return ClipboardGuard(clip.set_text, clip.clear, timeout, clip.schedule)


def test_copy_sets_text_and_schedules_30_seconds():
    clip = FakeClipboard()
    make_guard(clip).copy("secret")
    assert clip.text == "secret"
    assert clip.scheduled[0]["delay"] == 30.0


def test_clipboard_cleared_when_timer_fires():
    clip = FakeClipboard()
    make_guard(clip).copy("secret")
    clip.fire_last()
    assert clip.text == ""


def test_second_copy_cancels_first_timer():
    clip = FakeClipboard()
    guard = make_guard(clip)
    guard.copy("first")
    guard.copy("second")
    assert clip.scheduled[0]["cancelled"] is True
    assert clip.text == "second"


def test_clear_now_cancels_timer_and_clears():
    clip = FakeClipboard()
    guard = make_guard(clip)
    guard.copy("secret")
    guard.clear_now()
    assert clip.text == ""
    assert clip.scheduled[0]["cancelled"] is True


def test_real_timer_clears_clipboard():
    import time

    clip = FakeClipboard()
    guard = ClipboardGuard(clip.set_text, clip.clear, timeout=0.05)
    guard.copy("secret")
    assert clip.text == "secret"
    time.sleep(0.3)
    assert clip.text == ""
