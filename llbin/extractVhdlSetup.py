#! /usr/bin/python
import os,sys,string

def main():
    Fname = sys.argv[1]
    File = open(Fname)
    workInFile(File)
    print DATA['entity'],DATA['architecture'],len(DATA['insts'])
    if DATA['entity'] == DATA['architecture']:
        createSonsFile(Fname,DATA['entity'],DATA['insts'],DATA['uses'])
    else:
        Fempty = open('empty.files','a')
        Fempty.write('%s\n'%Fname)
        Fempty.close()



def createSonsFile(Fname,Module,Sons,Uses):
    Fout = open('sons/%s.sons'%(Module),'w')
    Fout.write('fname vhdl %s\n'%(Fname))
    for Son in Sons:
        Fout.write('son %s  %s\n'%(Module,Son))
    for Use in Uses:
        Fout.write('use %s  %s\n'%(Module,Use))
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
DATA['entity'] = 'none'
DATA['architecture'] = 'blank'
DATA['insts'] = []
DATA['uses'] = []
def work(Words):
    global state
    Len = len(Words)
    Ok = True
    while Ok:
        Find = lookFor(Words,'use ? ;')
        if Find:
            First,Vars = Find
            Words = Words[:First]+Words[First+3:]
            if 'ieee' not in Vars[0]:
                DATA['uses'].append(Vars[0])
        else:
            Ok=False

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
    if len(Words)==Len:
        Lim = max(Len-100,0)
        if Lim>0: Words = Words[Lim:]

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


