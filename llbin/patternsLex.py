#! /usr/bin/env python3
'''
looks for patterns in lex and replaces them
'''
Verbose = -1
PATTERNS = [
    ("LeftParen OTHERS => 0 RightParen","0",1)
#    ,("LeftParen 0 Arrow ?1 Comma OTHERS Arrow 0 RightParen","?1",2)
    ,("SUBTYPE","TYPE",3)
    ,("GENERATE BEGIN_","GENERATE",4)
    ,("natural","integer",5)
    ,("Shared","",6)
    ,("END ?1 Semicolon","END Semicolon",7)
    ,("END ?1 ?2 Semicolon","END Semicolon",8)
    ,("<= (","<= assignment (",8)
    ,("? : PROCESS","PROCESS",9)
#    ,(" ( ?1(int) => ?2 ( ?3(int) ) , ?4 DOWNTO ?5 => 0 ) ","@assemble",9)
]


import os,sys,string
LONG = []
def main():
    Fname = sys.argv[1]
    Foutname = sys.argv[2]
    run(Fname,Foutname)

def dbgfile():
    Fout= open('dbg.vxx','w')
    Lnum = 0
    for Item in LONG:
        Line = int(Item[2])
        if Line>Lnum:
            Fout.write('\n')
            Lnum = Line
        Fout.write('%s ' % token(Item))
    Fout.close()

def token(Item):
    if Item[1] == 'Identifier':
        return Item[0]

    if Item[0] in Backs:
        return Backs[Item[0]]

    return Item[0]

Backs = {}
Backs['Semicolon'] = ';'
Backs['Colon'] = ':'
Backs['Comma'] = ','
Backs['RightParen'] = ')'
Backs['LeftParen'] = '('
Backs['Minus'] = '-'
Backs['Star'] = '*'
Backs['VarAsgn'] = ':='
Backs['EQSym'] = '=='
Backs['LESym'] = '<='
Backs['BEGIN_'] = 'begin'

Forwards = {}
for Key in Backs:
    Forwards[Backs[Key]] = Key

def run(Fname,Foutname):
    File = open(Fname)
    Fout = open(Foutname,'w')
    buildLong(File) 
    scan0Long()
    scan1Long()
    scan1Long()
    for Item in LONG:
        Fout.write('%s %s %s %s\n' % tuple(Item))
    Fout.close()
    dbgfile()

def scan0Long():
    ind = 0
    while ind < len(LONG):
        for Pat in PATTERNS:
            Pat0 = Pat[0].split()
            if len(Pat0) == 1:
                applyMatch(Pat0,Pat[1].split(),ind,Pat[2])
        ind += 1

def scan1Long():
    for Pat in PATTERNS:
        Pat0 = Pat[0].split()
        if len(Pat0)>1:
            ind = 0
            while ind < (len(LONG)-len(Pat0)):
                applyMatch(Pat0,Pat[1].split(),ind,Pat[2])
                ind += 1

def applyMatch(Pat0,Pat1,ind,Rule,Pos=0,Trans={}):
    if Rule == Verbose:
        print("try pos=%d %s %s %s     tok=%s  %s %s %s" % (Pos,LONG[ind+Pos],Pat0[Pos],matches(Pat0[Pos],LONG[ind+Pos],{}),LONG[ind:ind+len(Pat0)],Pat0,Pat1,Trans))
    if matches(Pat0[Pos],LONG[ind+Pos],Trans):
        if len(Pat0) == (Pos+1):
            activateMatch(Pat0,Pat1,ind,Trans)
        else:
            applyMatch(Pat0,Pat1,ind,Rule,Pos+1,Trans) 
    else:
        return

def matches(Token,Item,Trans):
    if Token in Forwards:
        Token = Forwards[Token]

    if (Token[0] == '?') and ('(' in Token):
        WW = Token.split('(')
        Token = WW[0]
        Kind = WW[1][:-1]
        if not okKind(Kind,Item): return False

    if Token[0] == '?':
        Trans[Token] = Item
        return True
    if Token in Item[:2]:
        return True
    if (Token == '0') and (Item[0] in "'0'"): 
        return True
    if (Token == '1') and (Item[0] in "'1'"): 
        return True
    return False

def okKind(Kind,Item):
    if Kind == 'int':
        if Item[1] == 'DecimalInt': return True
        if Item[1] == 'Identifier': return False
    print('okKind',Kind,Item)
    return False

def activateMatch(Pat0,Pat1,ind,Trans):
    Was = LONG[ind:ind+len(Pat0)]
    for ii in range(len(Pat0)):
        LONG.pop(ind)
    if (len(Pat1) == 1) and (Pat1[0][0] == '@'):
        Call = "%s(Trans)" % Pat1[0][1:]
        X = eval(Call)
        Lnum = Was[0][2]
        print('LLLLL',X)
        for ii,Tok in enumerate(X):
            LONG.insert(ind+ii,makeTok(Tok,Lnum))
        return
        
    for ii in range(len(Pat1)):
        Rpl = Pat1[ii]
        if Rpl[0] == '?':
            Rpl = Trans[Rpl]
        else:
            Rpl = Rpl,typing(Rpl),0,0
        New = [Rpl[0],Rpl[1],Was[0][2],Was[0][3]]
        LONG.insert(ind+ii,New)
        
def makeTok(Tok,Lnum):
    if Tok in Forwards:
        Tok = Forwards[Tok]
    return (Tok,typing(Tok),Lnum,0)
        
def typing(Token):
    if Token[0] in '0123456789': return 'DecimalInt'
    if Token in ['TYPE','END']:
        return Token
    if Token in Backs: 
        return Token
    if Token in Forwards: 
        return Forwards[Token]
    return 'Identifier'




def buildLong(File):
    while 1:
        line = File.readline()
        if line=='': 
            File.close()
            return
        wrds = line.split()
        if len(wrds) == 4:
            LONG.append(wrds)


def assemble(Trans):
    Shift = Trans['?1'][0]
    Bus = Trans['?2'][0]
    Ind = Trans['?3'][0]
    return ['shift_left','(',Bus,'(',Ind,')',',',Shift,')']
    


if __name__ == '__main__': main()
