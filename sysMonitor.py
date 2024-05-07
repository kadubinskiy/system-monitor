import psutil
import subprocess
import curses
import time
import os


### DATA COLLECTION
def reqSysLoad():
    return "System load", int(psutil.getloadavg()[0] / 4 * 100)


def reqCpuLoad():
    return "CPU load", psutil.cpu_percent(interval=1)


def reqRamLoad():
    return "GPU load", psutil.virtual_memory().percent


def reqCDUsage():
    return (
        "CD usage",
        psutil.disk_usage("/").free,
        psutil.disk_usage("/").used,
        psutil.disk_usage("/").percent,
    )


def reqGpuLoad():
    command = "vcgencmd get_mem gpu"
    gpu_mem_str = subprocess.check_output(command, shell=True).decode("utf-8").strip()
    return "GPU load", int(gpu_mem_str.split("=")[1][:-1])


def reqCpuTemp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
        cpu_temp = int(temp_file.read()) / 1000
    return "CPU temperature", (cpu_temp, 1)


def reqGpuTemp():
    process = subprocess.Popen(["vcgencmd", "measure_temp"], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    output = output.decode("utf-8")

    temp_str = output.split("=")[1].split("'")

    return "GPU temperature", round(float(temp_str), 1)


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()

    ### FUNCTIONS
    ## DATA VISUALISATION
    def graphBuilder(
        centerY,
        centerX,
        height,
        width,
        statsTuple,
        pairN,
        symbol="█",
        stdscr=stdscr,
    ):
        inWork = True
        while inWork == True:
            if len(statsTuple) >= width:
                for horSpread in range(width):
                    for vertSpread in range(
                        int(statsTuple[horSpread] / (100 / height) + 1)
                    ):
                        if vertSpread < height:
                            stdscr.addstr(
                                int(centerY + height // 2 - vertSpread),
                                int(centerX - width + 1 + horSpread * 2),
                                symbol,
                                curses.color_pair(pairN),
                            )
                inWork = False
            else:
                statsTuple.insert(0, 0)

    winHeight, winWidth = stdscr.getmaxyx()

    cpuLoadStats = []
    gpuLoadStats = []
    ramLoadStats = []
    redBlink = False

    def screenOne():
        ### CPU LOAD GRAPH
        cpuLoad = reqCpuLoad()[1]
        cpuLoadStats.append(cpuLoad)
        cpuLoadStats.pop(0)
        if cpuLoad < 50:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        elif cpuLoad < 85:
            curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        else:
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        graphBuilder(
            winHeight // 4,
            winWidth // 2 // 3,
            5,
            6,
            cpuLoadStats,
            1,
        )

        stdscr.addstr(
            winHeight // 4,
            (winWidth // 2 // 3) * 2,
            str(cpuLoad) + "%",
            curses.color_pair(1),
        )

        ### GPU LOAD GRAPH
        gpuLoad = reqGpuLoad()[1]
        gpuLoadStats.append(gpuLoad)
        gpuLoadStats.pop(0)
        if gpuLoad < 50:
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        elif gpuLoad < 85:
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        else:
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        graphBuilder(
            winHeight // 4, winWidth // 2 + winWidth // 2 // 3, 5, 6, gpuLoadStats, 2
        )

        stdscr.addstr(
            winHeight // 4,
            winWidth - winWidth // 2 // 3,
            str(gpuLoad) + "%",
            curses.color_pair(2),
        )

        ### RAM LOAD GRAPH
        ramLoad = reqRamLoad()[1]
        ramLoadStats.append(ramLoad)
        ramLoadStats.pop(0)
        if ramLoad < 50:
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        elif ramLoad < 85:
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        else:
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        graphBuilder(
            (winHeight // 4) * 3,
            winWidth // 2 // 3,
            5,
            6,
            ramLoadStats,
            3,
        )

        stdscr.addstr(
            (winHeight // 4) * 3,
            winWidth // 2 - winWidth // 2 // 3,
            str(ramLoad) + "%",
            curses.color_pair(2),
        )

        ### CD USAGE INDICATOR
        stdscr.addstr(
            (winHeight // 2) + winHeight // 6,
            winWidth // 2 + winWidth // 8,
            "Free space: " + str(reqCDUsage()[1] // 1000000) + " Mbytes",
        )
        stdscr.addstr(
            (winHeight // 2) + 2 * (winHeight // 6),
            winWidth // 2 + winWidth // 8,
            "Used space: " + str(reqCDUsage()[2] // 1000000) + " Mbytes",
        )
        stdscr.addstr(
            (winHeight // 4) * 3,
            winWidth // 2 + winWidth // 3,
            str(reqCDUsage()[3]) + "%",
        )

        ### SYS LOAD INDICATOR
        sysLoad = reqSysLoad()[1]
        stdscr.hline(
            winHeight // 2,
            0,
            curses.ACS_HLINE,
            winWidth // 2 - winHeight // 6,
        )
        stdscr.hline(
            winHeight // 2,
            winWidth // 2 + winHeight // 6,
            curses.ACS_HLINE,
            winWidth // 2,
        )
        stdscr.vline(
            0,
            winWidth // 2,
            curses.ACS_VLINE,
            winHeight // 2 - winHeight // 7,
        )
        stdscr.vline(
            winHeight // 2 + winHeight // 7,
            winWidth // 2,
            curses.ACS_VLINE,
            winHeight // 2,
        )

        ## SYS GRAPHICS
        stdscr.hline(
            winHeight // 2 - winHeight // 7,
            winWidth // 2 - winHeight // 6 + 1,
            curses.ACS_HLINE,
            winHeight // 3 - 1,
        )
        stdscr.hline(
            winHeight // 2 + winHeight // 7,
            winWidth // 2 - winHeight // 6 + 1,
            curses.ACS_HLINE,
            winHeight // 3 - 1,
        )
        stdscr.vline(
            winHeight // 2 - winHeight // 7 + 1,
            winWidth // 2 - winHeight // 6,
            curses.ACS_VLINE,
            winHeight // 7 * 2 - 1,
        )
        stdscr.vline(
            winHeight // 2 - winHeight // 7 + 1,
            winWidth // 2 + winHeight // 6,
            curses.ACS_VLINE,
            winHeight // 7 * 2 - 1,
        )
        # ANGLES
        stdscr.addch(
            winHeight // 2 - winHeight // 7,
            winWidth // 2 - winHeight // 6,
            curses.ACS_ULCORNER,
        )
        stdscr.addch(
            winHeight // 2 - winHeight // 7,
            winWidth // 2 + winHeight // 6,
            curses.ACS_URCORNER,
        )
        stdscr.addch(
            winHeight // 2 + winHeight // 7,
            winWidth // 2 - winHeight // 6,
            curses.ACS_LLCORNER,
        )
        stdscr.addch(
            winHeight // 2 + winHeight // 7,
            winWidth // 2 + +winHeight // 6,
            curses.ACS_LRCORNER,
        )

        stdscr.addstr(
            winHeight // 2,
            winWidth // 2 - len(str(reqSysLoad()[1]) + "%") // 2,
            str(sysLoad) + "%",
        )

        ### MONITOR IDs
        stdscr.addstr(winHeight // 10, winWidth // 10, "CPU load:")
        stdscr.hline(
            winHeight // 10 + 1, winWidth // 10, curses.ACS_HLINE, len("CPU load:")
        )

        stdscr.addstr(winHeight // 10, winWidth // 2 + winWidth // 10, "GPU load:")
        stdscr.hline(
            winHeight // 10 + 1,
            winWidth // 2 + winWidth // 10,
            curses.ACS_HLINE,
            len("GPU load:"),
        )

        stdscr.addstr(winHeight // 2 + winHeight // 10, winWidth // 10, "RAM usage:")
        stdscr.hline(
            winHeight // 2 + winHeight // 10 + 1,
            winWidth // 10,
            curses.ACS_HLINE,
            len("RAM usage:"),
        )

        stdscr.addstr(
            winHeight // 2 + winHeight // 10,
            winWidth // 2 + winWidth // 10,
            "CD usage:",
        )
        stdscr.hline(
            winHeight // 2 + winHeight // 10 + 1,
            winWidth // 2 + winWidth // 10,
            curses.ACS_HLINE,
            len("CD usage:"),
        )

        nonlocal redBlink
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        if cpuLoad > 90 and not redBlink:
            stdscr.hline(
                winHeight // 10 + 2,
                winWidth // 10,
                curses.ACS_HLINE,
                len("CPU load:"),
                curses.color_pair(4),
            )
        if gpuLoad > 90 and not redBlink:
            stdscr.hline(
                winHeight // 10 + 2,
                winWidth // 2 + winWidth // 10,
                curses.ACS_HLINE,
                len("GPU load:"),
                curses.color_pair(4),
            )
        if ramLoad > 90 and not redBlink:
            stdscr.hline(
                winHeight // 10 + 2,
                winWidth // 10,
                curses.ACS_HLINE,
                len("RAM usage"),
                curses.color_pair(4),
            )
        redBlink = not redBlink

    while True:
        stdscr.clear()
        screenOne()
        key = stdscr.getch()
        if key != -1:
            os.system("chvt 1")
            exit()
        stdscr.refresh()
        time.sleep(0.5)


curses.wrapper(main)
