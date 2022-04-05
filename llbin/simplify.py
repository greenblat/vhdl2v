
import logs


def simplifyModule(Mod,Context):
    for ind,(Dst,Src,_,_) in enumerate(Mod.hard_assigns):
        Src0 = simplifyExpr(Context,Src)
        Mod.hard_assigns[ind] = (Dst,Src0,'','')

    for ind,Always in enumerate(Mod.alwayses):
        Sense,Body,Kind = Always
        Context = []
        Edged = edgedSense(Sense)
        if Edged: 
            Context.append('edged')
            Context.append(('remove',Edged))
            Sense = fixEdges(Sense,Body)

        Body0 = simplifyBody(Context,Body)
        Mod.alwayses[ind] = Sense,Body0,Kind


def fixEdges(Sense,Body):
    if Body[0] == 'list':
        return fixEdges(Sense,Body[1])

    if Body[0][0] != 'ifelse':
        return Sense

    Cond = Body[0][1]
    if (Cond[0] == '==')and(Cond[2] in ['0',0]):
        Rst = Cond[1],'negedge'
    elif (Cond[0] == '==')and(Cond[2] in ['1',1]):
        Rst = Cond[1],'posedge'
    else:
        return Sense 
    if Sense[0] == 'list':
        Res = ['list']
        for Item in Sense[1:]:
            if (type(Item) is str) and (Rst[0] == Item):
               Res.append( (Rst[1],Item) )
            else:
                Res.append(Item)
        return Res                
    return Sense


def edgedSense(Sense):
    if Sense == '*': return False
    if type(Sense) is tuple:
        if Sense[0] in ['posedge','negedge']: return Sense[1]
    if type(Sense) is list:
        for Item in Sense:
            if edgedSense(Item): return edgedSense(Item)
    return False

def removeEdged(Context):
    if 'edged' in Context: 
        Cont = Context[:]
        Cont.remove('edged')
        return Cont
    return Context


def simplifyBody(Context,Body):
    if Body == '': return ''
    if type(Body) is list:
        if len(Body) == 0:
            return Body
        if Body[0] == 'list':
            if len(Body[1])==1:
                return simplifyBody(Context,Body[1][0])
            Res = []
            for Item in Body[1]:
                Res.append(simplifyBody(Context,Item))
            return Res
    if type(Body) is tuple:
        if Body[0] == 'ifelse':
            Cond = simplifyExpr(Context,Body[1])
            Yes = simplifyBody(Context,Body[2])
            No  = simplifyBody(Context,Body[3])
            return ('ifelse',Cond,Yes,No)
        if Body[0] == 'if':
            Cond = simplifyExpr(Context,Body[1])
            Yes = simplifyBody(Context,Body[2])
            if Cond in [1,'1']:
                return Yes
            if (Cond[0] == 'subbit')and(Cond[1] == 'rising_edge'):
                return Yes
            return ('if',Cond,Yes)
        if Body[0] == '=':
            Dst = simplifyExpr(Context,Body[1])
            Src = simplifyExpr(Context,Body[2])
            if 'edged' in Context:
                return ('<=',Dst,Src)
            return ('=',Dst,Src)
        if Body[0] == 'for':
            St = simplifyBody(removeEdged(Context),Body[1])
            Cond = simplifyExpr(Context,Body[2])
            Advance = simplifyBody(removeEdged(Context),Body[3])
            Body4 = simplifyBody(Context,Body[4])
            return ('for',St,Cond,Advance,Body4)
        if Body[0] == 'case':
            Res = []
            for Case in Body[2]:
                Label,Code = Case
                Code1 = simplifyBody(Context,Code)
                Res.append((Label,Code1))
            
            return ('case',Body[1],Res)

    logs.log_error('simpliyfBody failed on "%s"' % (str(Body)))
    return Body
RESERVED = 'int '.split()
def simplifyExpr(Context,Expr):
    if type(Expr) is str: 
        if Expr in RESERVED: return 'x_'+Expr
        for Item in Context:
            if (type(Item) is tuple) and (Item[0] == 'remove') and (Item[1] == Expr):
                return 1
        return Expr
    if type(Expr) is int: return Expr
    if type(Expr) is tuple:
        if Expr[0] == 'question':
            A = simplifyExpr(Context,Expr[1])
            B = simplifyExpr(Context,Expr[2])
            C = simplifyExpr(Context,Expr[3])
            if (B in ['1',1])and(C in ['0',0]):
                return A
            if (C in ['1',1])and(A in ['0',0]):
                return ('!',A)
            return ('question',A,B,C)

        if Expr[0] in ('bus'):
            return ('subbus',Expr[1],Expr[2][0],Expr[3][0])

        if Expr[0] in ('**'):
            A = simplifyExpr(Context,Expr[1])
            B = simplifyExpr(Context,Expr[2])
            if A == '2':
                return ('<<',1,B)
            return (Expr[0],A,B)
        if Expr[0] in ('>=','=>','<=','>','/','*','^','-','+','<','|','&','%','^'):
            A = simplifyExpr(Context,Expr[1])
            B = simplifyExpr(Context,Expr[2])
            if Expr[0] == '&':
                if (A in ['1',1]): return B
                if (B in ['1',1]): return A
            return (Expr[0],A,B)

        if Expr[0] == '!':
            A = simplifyExpr(Context,Expr[1])
            return ('!',A)
        if Expr[0] == '==':
            if Expr[2] in ['0',0]:
                return ('!',simplifyExpr(Context,Expr[1]))
            if Expr[2] in ['1',1]:
                return simplifyExpr(Context,Expr[1])
            A = simplifyExpr(Context,Expr[1])
            B = simplifyExpr(Context,Expr[2])
            return (Expr[0],A,B)
        if Expr[0] == '!=':
            if Expr[2] in ['0',0]:
                return simplifyExpr(Context,Expr[1])
            if Expr[2] in ['1',1]:
                return ('!',simplifyExpr(Context,Expr[1]))
            A = simplifyExpr(Context,Expr[1])
            B = simplifyExpr(Context,Expr[2])
            return (Expr[0],A,B)

        if Expr[0] == 'function':
            if Expr[1] == 'edge': return 1
        if Expr[0] == 'subbit':
            if Expr[1] == 'rising_edge': return 1
            if Expr[1] == 'unsigned': return simplifyExpr(Context,Expr[2])
            if Expr[1] == 'std_logic_vector': return simplifyExpr(Context,Expr[2])
            B = simplifyExpr(Context,Expr[2])
            return (Expr[0],Expr[1],B)
        if Expr[0] == 'subbus':
            Hi = simplifyExpr(Context,Expr[2][0])
            Lo = simplifyExpr(Context,Expr[2][1])
            return (Expr[0],Expr[1],(Hi,Lo))
        if Expr[0] == 'funcall':
            Func = Expr[1]
            if Func == 'shift_left':
                Who = Expr[2][0]
                By  = Expr[2][1]
                return ('<<',Who,simplifyExpr(Context,By))
            if Func == 'shift_right':
                Who = Expr[2][0]
                By  = Expr[2][1]
                return ('>>',Who,simplifyExpr(Context,By))

    logs.log_error('simpliyfExpr failed on "%s"' % (str(Expr)))
    return Expr
