import ctypes


def hide_file(file_name):
    """Set a file as hidden."""
    ctypes.windll.kernel32.SetFileAttributesW(file_name, 2)

   
def show_file(file_name):
    """Unset a file as hidden."""
    ctypes.windll.kernel32.SetFileAttributesW(file_name, 128)


def get_resolution():
    """Get the resolution of the main monitor.
    Returns:
        (x, y) resolution as a tuple.
    """
    user32 = ctypes.windll.user32
    return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))


def get_refresh_rate():
    """Get the refresh rate of the main monitor.
    Returns:
        Refresh rate/display frequency as an int.
    """
    raise NotImplementedError()


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_ulong), ("y", ctypes.c_ulong)]


def get_cursor_pos():
    """Read the cursor position on screen.
    Returns:
        (x, y) coordinates as a tuple.
        None if it can't be detected.
    """
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return (int(pt.x), int(pt.y))


def get_mouse_click():
    """Check if one of the three main mouse buttons is being clicked.
    Returns:
        True/False if any clicks have been detected or not.
    """
    buttons = (1, 4, 2)
    return tuple(ctypes.windll.user32.GetKeyState(button) > 1 for button in buttons)


def get_key_press(key):
    """Check if a key is being pressed.
    Needs changing for something that detects keypresses in applications.
    Returns:
        True/False if the selected key has been pressed or not.
    """
    return ctypes.windll.user32.GetKeyState(key) > 1
    

class _RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_ulong),
        ('top', ctypes.c_ulong),
        ('right', ctypes.c_ulong),
        ('bottom', ctypes.c_ulong)
    ]
  
    def dump(self):
        return map(int, (self.left, self.top, self.right, self.bottom))


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', _RECT),
        ('rcWork', _RECT),
        ('dwFlags', ctypes.c_ulong)
    ]


def _get_monitors():
    """Get a list of all monitors to further processing.
    Copied from code.activestate.com/recipes/460509-get-the-actual-and-usable-sizes-of-all-the-monitor/
    """
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                                ctypes.POINTER(_RECT), ctypes.c_double)

    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        data = [hMonitor]
        data.append(r.dump())
        retval.append(data)
    return 1

    cbfunc = CBFUNC(cb)
    temp = ctypes.windll.user32.EnumDisplayMonitors(0, 0, cbfunc, 0)
  
  return retval


def _monitor_areas():
    """Find the active and working area of each monitor.
    Copied from code.activestate.com/recipes/460509-get-the-actual-and-usable-sizes-of-all-the-monitor/
    """
  retval = []
  monitors = _get_monitors()
  for hMonitor, extents in monitors:
    data = [hMonitor]
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    mi.rcMonitor = _RECT()
    mi.rcWork = _RECT()
    res = ctypes.windll.user32.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
    data.append(mi.rcMonitor.dump())
    data.append(mi.rcWork.dump())
    retval.append(data)
  return retval


def get_monitor_info():
    """Extract size and location from monitor functions."""
    max_int = 2 ** 32
    monitor_list = []
    for monitor, actual, working in _monitor_areas():
        x_min, y_min, x_max, y_max = actual
        width = (x_max - x_min) % max_int
        height = (y_max - y_min) % max_int
        
        if x_min > x_max:
            x_min -= max_int
        if y_min > y_max:
            y_min -= max_int

        monitor_info = {'Size': (width, height),
                        'Location': {'X': (x_min, x_max), 'Y': (y_min, y_max)}}
        monitor_list.append(monitor_info)
    return monitor_list
