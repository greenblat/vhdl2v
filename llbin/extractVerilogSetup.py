#! /usr/bin/python
import os,sys,string
import logs

def main():
    Fname = sys.argv[1]
    workFile(Fname)

def workFile(Fname):
    if not os.path.exists(Fname):
        logs.log_error('cannot open file %s'%Fname)
        return
    File = open(Fname)
    AbsPath = absPath(Fname)
    Wrds = []
    while 1:
        line = File.readline()
        if line=='': 
            work(Wrds,AbsPath,Fname)
            return 
        for Chr in ':()#,':
            line = string.replace(line,Chr,' %s '%Chr)
        line = string.replace(line,'/*',' /* ')
        line = string.replace(line,'*/',' */ ')
        if '//' in line: line = line[:line.index('//')]
        wrds = string.split(line)
        Wrds.extend(wrds)
        if len(wrds)==0:
            pass
        else:
            Wrds = work(Wrds,AbsPath,Fname)

def work(Wrds,AbsPath,Fname):
    ok,Wrds = removeRemarks(Wrds)
    if not ok: return Wrds
    if 'endmodule' not in Wrds: return Wrds
    if 'module' not in Wrds:
        logs.log_error('work got endmodule but not module')
        return Wrds
    
    Includes = extractIncludes(Wrds,AbsPath)

    ind0 = Wrds.index('module') 
    ind1 = Wrds.index('endmodule') 
    Back = Wrds[ind1+1:]
    This = Wrds[ind0:ind1+1]

    doTheJob(This,AbsPath,Fname,Includes)
    return Back


def extractIncludes(Wrds,AbsPath):
    Paths = []
    for ind,Token in enumerate(Wrds):
        if Token == '`include':
            Incfile = Wrds[ind+1][1:-1]
            if '/' not in Incfile:
                if AbsPath not in Paths: Paths.append(AbsPath)
            else:
                ww = string.split('/')
                Path = string.join(ww[:-1],'/')
                Path = joinPaths(AbsPath,Path)
                if Path not in Paths: Paths.append(Path)
    return Paths


def joinPaths(Head,Path):
    W0 = string.split(Head,'/')
    W1 = string.split(Path,'/')
    while W1[0]=='..':
        W0.pop(-1)
        W1.pop(0)
    WW = W0+W1
    Res = string.join(WW,'/')
    return Res

def doTheJob(This,AbsPath,Fname,Includes):
    This = cleanParams(This)
    if This[2]=='(':
        Module = This[1]
    else:
        logs.log_error(' "(" token is not following module name')
        return
    Sons = []
    for ind,Token in enumerate(This):
        if Token=='(':
            if goodToken(This[ind-2])and goodToken(This[ind-1]):
                Type = This[ind-2]
                if Type not in Sons: Sons.append(Type)
    report(Module,Sons,AbsPath,Fname,Includes)                

def report(Module,Sons,AbsPath,Fname,Includes):
    if not os.path.exists('sons'):
        os.mkdir('sons')
    Fout = open('sons/%s.sons'%Module,'w')
    Fout.write('module %s\n'%Module)
    Fout.write('abspath %s\n'%AbsPath)
    Fout.write('fname %s\n'%Fname)
    for Inc in Includes:
        Fout.write('include %s\n'%Inc)
    for Son in Sons:
        Fout.write('son %s\n'%Son)
    Fout.close()        
                
KEYWORDS = string.split('module for if else case end endcase when begin always')            
def goodToken(Token):
    if Token[0] not in string.letters: return False
    if Token in KEYWORDS: return False
    return True
    
def cleanParams(Wrds):
    State = 0
    Res = []
    for ind,Token in enumerate(Wrds):
        if State==0:
            if (Token=='(')and(Wrds[ind-1]=='#'):
                State = 1
                Res.pop(-1)
            else:
                Res.append(Token)
        elif (Token=='('):
            State += 1
        elif (Token==')'):
            State -= 1
    return Res

def removeRemarks(Wrds):
    if '/*' not in Wrds: return True,Wrds
    if '*/' not in Wrds:
        return False,Wrds
    ind0 = Wrds.index('/*')
    ind1 = Wrds.index('*/')
    Res = Wrds[:ind0]+Wrds[ind1+1:]
    return removeRemarks(Res)

    



def absPath(Fname):
    if Fname[0]=='/':
        wrds = string.split(Fname,'/')
        Path = string.join(wrds[:-1],'/')
        return Path
#    Pwd =  os.path.expandvars(os.path.expanduser(Fname))
    Pwd2 = os.path.dirname(os.path.abspath(Fname))
    return Pwd2




if __name__ == '__main__': main()



