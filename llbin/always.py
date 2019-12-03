

import logs
import module_class


def run(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        parameters(Mod)
        expressions(Mod)
        always(Mod)

        removeTypdefs(Mod)

def always(Mod):
    for Alw in Mod.alwayses:
        logs.log_info('TELL len=%d len1=%d  %s'%(len(Alw),len(Alw[1]),Alw[0]))
        LL = Alw[1]
        for A1 in LL:
            logs.log_info('TELL %d %s\nTELL\nTELL\n'%(len(A1),str(A1)))
   
def parameters(Mod):
    Params = []
    for Net in Mod.nets:
        _,Wid = Mod.nets[Net]
        if (type(Wid) is tuple)and(Wid[0] in ['double','triple']):
            Sup = module_class.support_set(Wid[1:])
        else:
            Sup = module_class.support_set(Wid)
        if Sup != []:
            for Sp in Sup:
                if Sp not in Params:
                    Params.append(Sp)
    Params.sort()
    if Params!=[]:
        logs.log_info('TELL params %s'%str(Params))
        for Prm in Params:
            if Prm not in Mod.parameters:
                if Prm not in Mod.localparams:
                    Mod.parameters[Prm]=10


def expressions(Mod):
    for ind,(Dst,Src,A,B) in enumerate(Mod.hard_assigns):
        Src = pacifyExpr(Src)
        Mod.hard_assigns[ind]=(Dst,Src,A,B)
    for ind,Alw in enumerate(Mod.alwayses):
        LL = pacifyExpr(Alw[1])
        Mod.alwayses[ind] = (Alw[0],LL,Alw[2])


def pacifyExpr(Expr):
    if isinstance(Expr,(str,int)): return Expr
    if (type(Expr) is list) and (len(Expr)==1): 
        return pacifyExpr(Expr[0])
    if type(Expr) is tuple:
        if Expr[0]=='subbit':
            if Expr[1] in ['to_integer','unsigned']:
                return pacifyExpr(Expr[2])
            return Expr
        if Expr[0] in ['integer','reg','logic','funccall','bin']:
            return Expr
        if Expr[0] in ['if','ifelse','<=','==','!=','+','-','&','~']:
            Res = [Expr[0]]+list(map(pacifyExpr,Expr[1:]))
            return Res
        if Expr[0] in ['for']:
            Res = [Expr[0],Expr[1]]+list(map(pacifyExpr,Expr[2:]))
            return Res
        if Expr[0]=='subbus':
            return Expr

    if (type(Expr) is list) and (len(Expr)>0) and (Expr[0]=='list'):
        Res = ['list']+list(map(pacifyExpr,Expr[1:]))
        return Res
    if (type(Expr) is list) and (len(Expr)==0):
        return []
    logs.log_error('pacifyExpr got %s'%str(Expr))
    return Expr
def removeTypdefs(Mod):
    Mod.typedefs={}
