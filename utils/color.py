import colorsys
import random


def random_color():
    """
    Generates random color.
    :return: (R, G, B) all values between 0-1
    """
    h = random.randint(0, 360) / 360
    s = random.randint(40, 70) / 100
    v = random.randint(50, 100) / 100

    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return r, g, b


def rgb2hex(r, g, b):
    """
    Encode RGB color to hexadecimal notation.
    :param r: red channel 0-1
    :param g: green channel 0-1
    :param b: blue channel 0-1
    :return: str: encoded color in the '#RRBBGG' format
    """
    r, g, b = round(r * 255), round(g * 255), round(b * 255)
    return '#%02x%02x%02x' % (r, g, b)


def contrast_color(r, g, b):
    """
    Finds color to be visible against the input background.
    :param r: red channel 0-1
    :param g: green channel 0-1
    :param b: blue channel 0-1
    :return: (R, G, B) all values between 0-1
    """
    # https://www.w3.org/TR/AERT/#color-contrast
    brightness = (r * 255 * 299 + g * 255 * 587 + b * 255 * 114) / 1000

    c = int(brightness < 125)

    return c, c, c


if __name__ == '__main__':
    print(rgb2hex(*random_color()))
