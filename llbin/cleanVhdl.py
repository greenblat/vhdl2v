#! /usr/bin/python

import os,sys,string

START = 'synthesis_off'
STOP = 'synthesis_on'
def main():
    Fname = sys.argv[1]
    run(Fname)


def run(Fname):
    File = open(Fname)
    lines = File.readlines()
    Fout = open('cleaned.vhd','w')
    state='idle'
    for line in lines:
        wrds = string.split(line)
        if wrds==[]:
            fwrite(Fout,line)
        elif state=='idle':
            fwrite(Fout,line)
            if '--' in wrds[0]:
                if START in line:
                    state= 'off'
        elif (state=='off'):
            if '--' in wrds[0]:
                if STOP in line:
                    state= 'idle'
                fwrite(Fout,line)
            else:
                fwrite(Fout,'--   '+line)
            
def fwrite(Fout,line):
    if '--' in line:
        X = line.index('--')
        line = line[:X]+'\n'
    res = ''
    for Chr in line:
        if ord(Chr) in [0xd]:
            pass
        else:
            res = res + Chr
    Fout.write(res)


if __name__=='__main__': main()

