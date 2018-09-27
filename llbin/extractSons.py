#! /usr/bin/python
import os,sys,string

def main():
    Fname = sys.argv[1]
    File = open(Fname)
    workInFile(File)
    print DATA['entity'],DATA['architecture'],len(DATA['insts'])
    if DATA['entity'] == DATA['architecture']:
        createSonsFile(DATA['entity'],DATA['insts'])


def createSonsFile(Module,Sons):
    Fout = open('sons/%s.sons'%(Module),'w')
    for Son in Sons:
        Fout.write('  %s\n'%(Son))
    Fout.close()

def workInFile(File):
    WRDS = []
    while 1:
        line = File.readline()
        if line=='': 
            work(WRDS)
            return
        if '--' in line:
            line = line[:line.index('--')]
        for Chr in '():;':
            line = string.replace(line,Chr,' %s '%Chr)
        wrds = string.split(string.lower(line))
        WRDS.extend(wrds)
        if len(WRDS)>10000:
            WRDS = work(WRDS)
state = 'idle'
DATA = {}
DATA['insts'] = []
def work(Words):
    global state
    if state=='idle':
         Find = lookFor(Words,'entity ? is')
         if Find:
             First,Vars = Find
             Words = Words[First+3:]
             DATA['entity']=Vars[0]
             state =  'arch'
    if state=='arch':
        Find = lookFor(Words,'architecture ? of ? is')
        if Find:
            First,Vars = Find
            Words = Words[First+5:]
            DATA['architecture']=Vars[1]
            state =  'insts'
    if state=='insts':
        Ok = True
        while Ok:
            Find = lookFor(Words,'port map (')
            if Find:
                First,Vars = Find
                Start=First
                This = Words[First-1]
                if This==')':
                    Find = lookFor(Words,'generic map (')
                    if Find:
                        First,Vars = Find
                        This = Words[First-1]


                if '.' in This:
                    ww = string.split(This,'.')
                    This = ww[-1]
                if This not in DATA['insts']:
                    DATA['insts'].append(This)
                Words = Words[Start+3:]
            else:
                Ok=False
             

    return Words
        
def lookFor(Words,Seq):
    ww = string.split(Seq)
    Vars = []
    Pos = 0
    First = 0
    while 1:
        if ww[0]=='?':
            Vars.append(Words[Pos])
            if First==0: First=Pos
            Pos += 1
            ww.pop(0)
        elif ww[0] not in Words:
            return False
        elif ww[0] in Words:
            ind = Words.index(ww[0])
            if First==0: First=ind
            Pos = ind+1
            ww.pop(0)
        if ww==[]: return First,Vars




main()


