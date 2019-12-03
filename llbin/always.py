

import logs
import module_class
import matches


def run(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        parameters(Mod)
        expressions(Mod)
        always(Mod)
        removeTypdefs(Mod)
        connections(Mod)


def connections(Mod):
    for Inst in Mod.insts:
        Obj = Mod.insts[Inst]
        Pins = Obj.conns.keys()
        for Pin in Pins:
            if isinstance(Pin,tuple):
                if Pin[0]=='aggregate':
                    Obj.conns[Pin[1]] = Obj.conns[Pin]
                    Obj.conns.pop(Pin)


def always(Mod):
    for Ind,Alw in enumerate(Mod.alwayses):
        LL = Alw[1]
        if LL[0]=='ifelse':
            Cond,Yes,No = LL[1],LL[2],LL[3]
            Vars =  matches.matches(Cond,'== ? ?')
            if Vars and (Vars[0] in Alw[0]):
                if (No[0]=='if'):
                    Cond2 = No[1]
                    Vars2 =  matches.matches_l(Cond2,'& [ funccall anyedge  [ ? ] ] [ == ? ? ]')
                    if Vars2:
                        if (Vars2[0]==Vars2[1])and(Vars2[2] in ['0','1']):
                            if (Vars[0] in Alw[0])and(Vars2[0] in Alw[0]):
                                if Vars[1]=='0': 
                                    Alw[0][0]= ('negedge',Vars[0])
                                else:
                                    Alw[0][0]= ('posedge',Vars[0])

                                if Vars2[2]=='0':
                                    Alw[0][1]= ('negedge',Vars2[0])
                                else:
                                    Alw[0][1]= ('posedge',Vars2[0])
                                Alw[1][3] = No[2]
                    Vars3 = matches.matches_l(Cond2,'subbit rising_edge ?',True)
                    if Vars3:
                        if Vars[1]=='0': 
                            Alw[0][0]= ('negedge',Vars[0])
                        else:
                            Alw[0][0]= ('posedge',Vars[0])

                        Alw[0][1]= ('posedge',Vars3[0])
                        Alw[1][3] = No[2]
        elif LL[0]=='if':
            Cond,Yes = LL[1],LL[2]
            if (Cond[0]=='subbit')and(Cond[1] in ['rising_edge','falling_edge']):
                Clk = Cond[2]
                if Cond[1]=='rising_edge': X0 = ('posedge',Clk)
                if Cond[1]=='falling_edge': X0 = ('negedge',Clk)
                New = (X0,LL[2],'always')
                Mod.alwayses[Ind] = New

        else:
            for ind,Item in enumerate(LL):
                if Item[0] == 'logic':
                    LL[ind] = ('reg',Item[1],Item[2])
                    
            New = ('*',LL,'always')
            Mod.alwayses[Ind] = New
            logs.log_info('TELL always len=%d len1=%d  %s'%(len(Alw),len(Alw[1]),Alw[0]))
            for A1 in LL:
                logs.log_info('TELL alwaysxx cond=%s %d %s\nTELL\nTELL\n'%(LL[0],len(A1),str(A1)))
   
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
        if Expr[0] in ['integer','reg','logic','funccall','bin','hex']:
            return Expr
        if Expr[0] in ['|','if','ifelse','<=','==','!=','+','-','&','~','curly','<','>']:
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
    if (type(Expr) is list) and (Expr[0] in ['ifelse','if']):
            Res = [Expr[0]]+list(map(pacifyExpr,Expr[1:]))
            return Res

    logs.log_error('pacifyExpr got %s'%str(Expr))
    return Expr
def removeTypdefs(Mod):
    Mod.typedefs={}
