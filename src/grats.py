from pretty import rgb, rgbb
from run import IMAGE_DIRECTORY, SAD_IMAGE_DIRECTORY, run_cmd, LINUX


import os
import random
import struct
from pathlib import Path

HEIGHT = 0.9
WIDTH = 0.6


def get_png_size(name: Path) -> tuple[int, int]:
    with open(name, 'rb') as f:
        data = f.read(25)
        if data[:8] != b'\211PNG\r\n\032\n' or data[12:16] != b'IHDR':
            raise Exception(f"{name} is not a png")
        w, h = struct.unpack('>LL', data[16:24])
        return int(w), int(h)

def ppm_to_ansi(imgf: list[bytes]) -> list[str]:
    w, h = [int(x) for x in imgf[1].decode('utf-8').split()]
    maxcol = int(imgf[2].decode('utf-8'))
    img =  (imgf[3]) #list(imgf[3])
    for x in imgf[4:]:
        img += x
    img_str = ''
    buffer: list[int] = []
    for i, c in enumerate(img):
        buffer.append(c)
        if len(buffer) != 3: continue
        r, g, b = buffer
        buffer=[]
        img_str += f"\x1b[48;2;{r};{g};{b}m \x1b[0m"
        if (i // 3 + 1) % w == 0:
            img_str += '\n'
            
    return img_str.split('\n')

def ppm_to_ansi2(imgf: list[bytes]) -> list[str]:
    w, h = [int(x) for x in imgf[1].decode('utf-8').split()]
    maxcol = int(imgf[2].decode('utf-8'))
    img =  (imgf[3]) #list(imgf[3])
    for x in imgf[4:]:
        img += x
    img_str = ''
    lines: list[list[tuple[int, int, int]]] = [[]]
    buffer: list[int] = []
    for i, c in enumerate(img):
        buffer.append(c)
        if len(buffer) != 3: continue
        r, g, b = buffer
        buffer=[]
        if len(lines[-1]) == w:
            lines.append([])
        lines[-1].append((r, g, b))
    for i in range(len(lines)//2):
        for c1, c2 in zip(lines[2*i], lines[2*i+1]):
            img_str += f"{rgb(*c1)}{rgbb(*c2)}▀\x1b[0m"
        img_str += '\n'
            
    return img_str.split('\n')


def png_to_ansi(name: Path) -> list[str]:
    pw, ph = list(map(float, get_png_size(name)))
    ph *= 1 # aspect ratio of one symbol is 1:2.5, except it's halved bc of ▀ character
    tw, th = os.get_terminal_size()
    w = tw * WIDTH
    h = th * HEIGHT * 2
    if ph > h:
        pw *= h / ph
        ph = h
    if pw > w:
        ph *= w / pw
        pw = w

    ph *= 2
    ph //= 2
    
    inp = name.as_posix()
    result = name.with_name('0.ppm')
    out = result.as_posix()
    cmd = 'convert' if LINUX else 'magick'
    run_cmd([cmd, inp, '-background', 'black', '-alpha', 'remove', '-define',  'filter:blur=0.5', '-resize', f'{int(pw)}x{int(ph)}!', out])
    with open(result, 'rb') as f:
        return ppm_to_ansi2(f.readlines())


def pick_grats(bad: bool) -> list[str] | None:
    img_dir = SAD_IMAGE_DIRECTORY if bad else IMAGE_DIRECTORY
    pngs: list[str] = [img for img in os.listdir(img_dir) if img.endswith('png')]
    if len(pngs) == 0:
        return None
    png_name = img_dir / pngs[random.randint(0, len(pngs)-1)]
    return png_to_ansi(png_name)
    
