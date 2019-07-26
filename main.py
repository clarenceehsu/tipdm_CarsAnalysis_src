# -*- encoding: utf-8 -*-

from module.cmd_Line import cmd_Line

if __name__ == '__main__':
    cmd_line = cmd_Line()
    L = cmd_line.building()
    cmd_line.preprocess_line(L)
    print('Done.')