#! /usr/bin/python


import os,sys,string


def main():
    Fnamein = sys.argv[1]
    Fnameout = sys.argv[2]
    run(Fnamein,Fnameout)

def run(Fnamein,Fnameout):
    Fin = open(Fnamein)
    Fout = open(Fnameout,'w')
    while 1:
        line = Fin.readline()
        if line=='':
            keepWindow('',Fout,True)
            Fout.close()
            Fin.close()
            return
        modified = modifyLine(line)
        keepWindow(modified,Fout)

WINDOW = []
def keepWindow(Line,Fout,Flush=False):
    if (Flush):
        for II in range(5): WINDOW.append('comment a b c')
        doWindow()
        while WINDOW!=[]:
            LLL = WINDOW.pop(0)
            if 'comment' not in LLL:
                Fout.write(LLL)
            if (len(WINDOW)>2): doWindow()
        return 
    WINDOW.append(Line)
    if len(WINDOW)>4:
        Fout.write(WINDOW.pop(0))
    else:
        return
    doWindow()

def doWindow():
    wrds0 =  string.split(WINDOW[0])
    wrds1 =  string.split(WINDOW[1])
    if len(WINDOW)>=3: wrds2 =  string.split(WINDOW[2])
    if len(WINDOW)>=4:
        wrds3 =  string.split(WINDOW[3])
        if (wrds0[0]=='END')and(wrds3[0]=='Semicolon'):
            if wrds1[0] in string.split('ENTITY ARCHITECTURE PROCESS CASE GENERATE PACKAGE'):
                WINDOW.pop(2)
                if wrds1[0]=='ARCHITECTURE':
                    WINDOW.pop(1)
                if wrds1[0]=='ENTITY':
                    WINDOW.pop(1)
        elif (wrds0[1]=='Identifier')and(wrds1[0]=='Colon')and(wrds2[0]=='ENTITY')and(wrds3[1]=='DOTTED'):
            WINDOW.pop(2)
            WINDOW[2] = '%s Identifier %s %s\n'%(wrds3[0],wrds3[2],wrds3[3])

    if len(WINDOW)>=3:
        if (wrds0[0]=='END')and(wrds2[0]=='Semicolon')and(wrds1[0] not in ['PROCESS','CASE','IF','RECORD','COMPONENT','LOOP','GENERATE']):
            WINDOW.pop(1)
        elif (wrds0[0]=='COMPONENT')and(wrds1[1]=='Identifier')and(wrds2[0]=='IS'):
            WINDOW.pop(2)
        elif (wrds0[0]=='END')and(wrds2[0]=='Semicolon')and(wrds1[1]=='Identifier'):
                WINDOW.pop(1)
    if (wrds0[0]=='END')and(wrds1[0]=='ENTITY'):
            WINDOW.pop(1)




LIST0 = string.split('''
    Library Use Package End Return Downto Is Function Body Entity Port In Inout Out
    Architecture Of Signal  Process If Then Else Variable Range Wait  Until
    To And  Elsif Not Or Xor Xnor Nor Nand Case When Others Component Map For Loop Exit Srl
    Type Assert Report Generic Buffer Array Generate Alias
    Record Subtype
''')
LIST1 = {'token':'Identifier','dotted':'DOTTED'
    ,'number':'DecimalInt'
    ,'Types':'Identifier'
    ,'Constant':'CONSTANT'
    ,'Cassign':'VarAsgn'
    ,'string':'BitStringLit'
    ,'Assign':'LESym'
    ,'tick':'Apostrophe'
    ,'Event':'Identifier'
    ,'Neq':'NESym'
    ,'power':'DoubleStar'
    ,'floating':'DecimalReal'
    ,'hexdig':'BasedInt'
    ,'+':'Plus'
    ,'-':'Minus'
    ,'|':'Bar'
    ,'<>':'Box'
    ,'sm_gr':'Box'
    ,'characters':'StringLit'
    ,'Null':'NULL_'
}
LIST2 = { 
     '(':'LeftParen'
    ,')':'RightParen'
    ,':':'Colon'
    ,';':'Semicolon'
    ,',':'Comma'
    ,'.':'Dot'
    ,'*':'Star'
    ,'**':'DoubleStar'
    ,'/':'Slash'
    ,'=':'EQSym'
    ,'<=':'LESym'
    ,'<':'LTSym'
    ,'=>':'GESym'
    ,'>=':'GESym'
    ,'>':'GTSym'
    ,'gr_eq':'GESym'
    ,'&':'Ampersand'
    ,'Begin':'BEGIN_'
    ,'Mod':'MOD'
}

def modifyLine(line):
    wrds = string.split(line)
    if (len(wrds)>4)and(wrds[0][0]=='"'):
        New = wrds[0]
        ind=1
        while '"' not in wrds[ind]:
            New += '.'+wrds[ind]
            ind += 1
        New += '.'+wrds[ind]
        wrds = [New,'characters',wrds[-2],wrds[-1]]
        
    if len(wrds)==4:
        Key = wrds[0]
        if wrds[0]=='severity':
            modified = 'SEVERITY SEVERITY %s %s\n'%(wrds[2],wrds[3])
            return modified
        if Key in LIST0:
            New = string.upper(Key)
            modified = '%s %s %s %s\n'%(New,New,wrds[2],wrds[3])
            return modified
        if wrds[1] in LIST1:
            New = LIST1[wrds[1]]
            if (New=='BitStringLit')and(wrds[0][1] in '+*/'):
                New = 'Identifier'
            if New=='Identifier':
                Token = string.lower(wrds[0])
            else:
                Token = wrds[0]
            modified = '%s %s %s %s\n'%(Token,New,wrds[2],wrds[3])
            return modified
        if wrds[1] in LIST2:
            New = LIST2[wrds[1]]
            modified = '%s %s %s %s\n'%(New,New,wrds[2],wrds[3])
            return modified
            


    return line


if __name__=='__main__': main()


