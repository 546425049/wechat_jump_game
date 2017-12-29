import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image
import time
import os


def pull_screenshot():
    os.system('adb shell screencap -p /sdcard/1.png >/dev/null 2>&1')
    os.system('adb pull /sdcard/1.png . >/dev/null 2>&1')


def jump(distance):
    # 这里的 2.04 是经验值，在我自己手机上这个值是合适的，不确定不同手机上是否通用
    press_time = distance * 2.04
    press_time = int(press_time)
    cmd = 'adb shell input swipe 320 410 320 410 ' + str(press_time) + ' >/dev/null 2>&1'
    os.system(cmd)


fig = plt.figure()
index = 0
cor = [0, 0]

pull_screenshot()
img = np.array(Image.open('1.png'))

update = True
click_count = 0
cor = []


def update_data():
    return np.array(Image.open('1.png'))


im = plt.imshow(img, animated=True)


# 寻找目标坐标
# 按行自顶向下遍历像素
# 滤掉背景色，直接取行尾的像素点，因为是渐变的
# 除去背景色的我们都认为是一种颜色，这样可以避免图形上花纹的干扰
# 滤掉顶部 y < 200 的行
# 滤掉颜色线开头像素点小于 10 的线，因为图形在画面中间，可以安全滤
# 判断现在这条线对比刚才的线的 x 是否有增加，因为图形都是倾斜的，方块和圆柱的顶部最右侧的 x 不再增加时说明这条线就是顶部的切线了，然后取这条切线的中点
# 当无法拿到切线时，一般是自己的跳动块头太高了，比切线还高，这里会滤掉跳动块附近的像素
# 还无法拿到切线时，刚才遇到了一次是下面的像素块都不符合条件了，比如在跳动块附近被跳过，这里就取最后一条线的中心
def findTarget(data, me):
    y = 1
    lastPoint = [0, 0, 0, 0]
    for line in data:
        y += 1
        colorL = 0
        x = 1
        for point in line:
            x += 1
            now = point.tolist()
            background = abs(now[0] - line[len(line) - 10][0]) < 10 and abs(now[1] - line[len(line) - 10][1]) < 10 and abs(now[2] - line[len(line) - 10][2]) < 10
            if not background:
                colorL += 1
            else:
                if y > 200 and x - colorL > 10 and colorL > 35 and ((x - colorL / 2) < (me[0] - 30) or (x - colorL / 2) > (me[0] + 30)):
                    if x <= lastPoint[3]:
                        return (lastPoint[0], lastPoint[1])

                    lastPoint = [x - colorL / 2, y, colorL, x]
                colorL = 0

    return (lastPoint[0], lastPoint[1])


# 寻找跳动块坐标
# 也是按行自顶向下遍历像素
# 直接跟跳动块像素的 rgb 对比..
# 然后拿到这些像素线里最长的也就是底部那一坨的最中间的位置
def findMe(data):
    y = 1
    points = []
    for line in data:
        y += 1
        colorL = 0
        x = 1
        for point in line:
            x += 1
            now = point.tolist()
            isme = abs(now[0] - 54) < 10 and abs(now[1] - 52) < 10 and abs(now[2] - 92) < 10
            if isme:
                colorL += 1
            else:
                if y > 200 and x - colorL > 10 and colorL > 30:
                    points.append([x - colorL / 2, y, colorL])
                colorL = 0
    maxPoint = [0, 0, 0]
    for point in points:
        if point[2] > maxPoint[2]:
            maxPoint = point
    return maxPoint


def updatefig(*args):
    global update
    if update:
        time.sleep(1)
        pull_screenshot()
        data = update_data()
        im.set_array(data)
        cor1 = findMe(data)
        cor2 = findTarget(data, cor1)
        print 'me = ', cor1
        print 'target = ', cor2

        update = False
        distance = (cor1[0] - cor2[0])**2 + (cor1[1] - cor2[1])**2
        distance = distance ** 0.5
        print 'distance = ', distance
        if distance > 20 or cor1[0] == 0:
            jump(distance)
            update = True
        else:
            update = False
    return im,


def onClick(event):
    global update
    global ix, iy
    global click_count
    global cor

    # next screenshot

    ix, iy = event.xdata, event.ydata
    coords = []
    coords.append((ix, iy))
    print 'now = ', coords
    cor.append(coords)

    click_count += 1
    if click_count > 1:
        click_count = 0

        cor1 = cor.pop()
        cor2 = cor.pop()

        distance = (cor1[0][0] - cor2[0][0])**2 + (cor1[0][1] - cor2[0][1])**2
        distance = distance ** 0.5
        print 'distance = ', distance
        jump(distance)
        update = True


fig.canvas.mpl_connect('button_press_event', onClick)
ani = animation.FuncAnimation(fig, updatefig, interval=50, blit=True)
plt.show()
