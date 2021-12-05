
import string,types,sys
import logs
KNOWNFUNCTIONS = ('ext sxt resize conv_std_logic_vector conv_integer unsigned').split()

DB = {}
count = 0
totalcount=0

def resetIt():
    global DB,count,totalcount
    DB = {}
    count = 0
    totalcount=0
    logs.log_info('reset It')


def matches_l(List,Seq,Verbose=False):
    Lseq = Seq.split()
    Lseq2 = gatherLists(Lseq)
    return listMatches(List,Lseq2,Verbose)
    


def matches(List,Seq,Verbose=False):
    global count,totalcount
    Res = matches__(List,Seq,Verbose)
    if Res:
        recordIt(Seq,count)
        totalcount += count
        count=0
    else:
        count += 1
    return Res

def recordIt(Seq,Pos):
    Seq = str(Seq)
    if Seq not in DB:
        DB[Seq] = (1,Pos)
    else:
        Was,Waspos = DB[Seq]
#        if Waspos!=Pos:
#            logs.log_info('strange pos of "%s" was %d now %d'%(Seq,Waspos,Pos))
        DB[Seq] = (Was+1,Pos)

def reportIt():
    logs.log_info('total steps = %d'%totalcount)
    LL = []
    for Seq in DB:
        (Num,Pos) = DB[Seq]
        LL.append((Num*Pos,Num,Pos,Seq))
    LL.sort()
    LL.reverse()
    for A,B,C,D in LL:
        logs.log_info('%10d : %50s   num=%d pos=%d'%(A,D,B,C))
    resetIt()

def matches__(List,Seq,Verbose=False):
    if Verbose:
        logs.log_info('try list=%s pattern=%s'%(List,Seq))
    if type(Seq) is list:
        return listMatches(List,Seq,Verbose)
    if type(Seq) is tuple:
        return listMatches(List,Seq,Verbose)
    Lseq = Seq.split()
    if len(List)!=len(Lseq): 
        if Verbose: logs.log_info('matches stopped at length %d<>%d iseq=%s who=%s '%(len(Lseq),len(List),Lseq,List))
        return False
    Vars=[]
    for ind,Iseq in enumerate(Lseq):
        Lind = List[ind]
        if (type(Lind) is tuple)and(len(Lind)==4):
            Litem = Lind[1]
            Litem0 = Lind[0]
        elif (isinstance(Lind,(tuple,list)))and(len(Lind)>0):
            Litem = Lind[-1]
            Litem0 = Lind[-1]
        else:
            Litem = Lind
            Litem0 = Lind

        if Iseq[0]=='?':
            RC = match_one(Iseq,List,ind,Vars,Verbose)
            if not RC: return False

        elif (Iseq[0] == '!')and(Iseq!='!'): 
            if (Iseq[1:]!=List[ind][0])and(Iseq[1:]!=List[ind][1]): 
                if Verbose: logs.log_info('matches stopped(0) at iseq=%s who=%s '%(Iseq,List[ind]))
                return False
            Vars.append(List[ind])
        elif Iseq == '$': 
            Who = List[ind]
            if Who in KNOWNFUNCTIONS:
                Vars.append(List[ind])
            else:
                if Verbose: logs.log_info('matches stopped(1) at iseq=%s who=%s '%(Iseq,Who))
                return False
        elif (Iseq[0] == '#')and(Iseq!='#'):  # check kind
            Kind = Iseq[1:]
            Act = List[ind][1]
            if (Kind!=Act): return False
            Vars.append(List[ind])

        elif (Iseq!=Litem)and(Iseq!=Litem0):
            if Verbose: logs.log_info('matches stopped(2) at iseq=|%s| who=|%s| %s '%(Iseq,Litem,List[ind]))
            return False
    if Vars==[]: return True 
    return Vars 


def match_one(Iseq,List,ind,Vars,Verbose):
    if Iseq == '?t':
        Tok = List[ind]
        if (type(Tok)is tuple)and(len(Tok)==4):
            Vars.append(Tok[0])
            return True
        else:
            return False
    elif Iseq == '?l':
        Tok = List[ind]
        if isinstance(Tok,(tuple,list)):
            Vars.append(Tok)
            return True
        else:
            return False
    elif Iseq == '?sI':
        Tok = List[ind]
        if type(Tok) is str:
            try:
                X = eval(Tok)
                Vars.append(Tok)
                return True
            except:
                if Verbose: logs.log_info('matches stopped ?sI %s != number'%(Tok))
                return False
        else:
            if Verbose: logs.log_info('matches stopped ?sI %s != token'%(Tok))
            return False
    elif Iseq == '?sD':
        Tok = List[ind]
        if type(Tok) is str:
            if (Tok in ['TO','DOWNTO']):
                Vars.append(Tok)
                return True
            else:
                if Verbose: logs.log_info('matches stopped ?sD %s != TO,DOWNTO'%(Tok))
                return False
        else:
            if Verbose: logs.log_info('matches stopped ?sD %s != token'%(Tok))
            return False
    elif Iseq == '?s':
        Tok = List[ind]
        if isinstance(Tok,(str,int)):
            Vars.append(Tok)
            return True
        else:
            return False
    elif Iseq == '?':
        Vars.append(List[ind])
        return True
    return True

def listMatches(List,Seq,Verbose):
    if type(List)is int:
        List = str(List)
    if Seq=='?t':
        if (type(List)is tuple)and(len(List)==4):
            Vars.append(Tok[0])
        else:
            return False
        
    elif Seq=='?s':
        if type(List)is str: return [List]
    elif Seq=='?l':
        if type(List)is list: return [List]
    elif Seq=='?sI':
        if type(List)is str:
            try:
                X = eval(List)
                return [List]
            except:
                if Verbose: logs.log_info('matches stopped ?sI %s != number'%(List))
                return False
        return False
    elif Seq=='?sD':
        if type(List)is str: 
            if (List in ['TO','DOWNTO']):
                return [List]
        return False
    elif Seq=='?':
        return [List]

    if type(List)is tuple:
        List = list(List)
    if Verbose:
        logs.log_info('try list=%s pattern=%s'%(List,Seq))

    if type(List)!=type(Seq): 
        if Verbose: logs.log_info('failed on dff types %s %s list=%s pattern=%s'%(type(List),type(Seq),List,Seq))
        return False
    if type(List)is str:
        if Seq=='?': return [List]
        Ok =  Seq==List
        if Verbose and not Ok: logs.log_info('failed on dff token list=%s pattern=%s'%(List,Seq))
        return Ok
    if len(List)!=len(Seq): 
        if Verbose: logs.log_info('failed on dff len %d<>%d list=%s pattern=%s'%(len(List),len(Seq),List,Seq))
        return False
    Res=[]
    for ind,Item in enumerate(List):
        V = listMatches(Item,Seq[ind],Verbose)
        if not V: 
            if Verbose: logs.log_info('failed165 on item=%s pattern=%s'%(Item,Seq[ind]))
            return False
        if isinstance(V,(tuple,list)):               
            Res.extend(V)
    if Res==[]: return True
    return Res 


def gatherLists(List0):
    res = List0[:]
    while ']' in res:
        ind = res.index(']')
        strt = ind-1
        while res[strt]!='[': strt -= 1
        New = res[strt+1:ind]
        Bef = res[:strt]
        Aft = res[ind+1:]
        res = Bef + [New] + Aft
    return res
            
X = 'aa [ bb cc ] [ dd ee ] ff'
print(gatherLists(X.split()))

