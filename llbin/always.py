

import logs


def run(dbscan):
    for Module in dbscan.Modules:
        Mod = dbscan.Modules[Module]
        always(Mod)

def always(Mod):
    for Alw in Mod.alwayses:
        logs.log_info('TELL len=%d len1=%d  %s'%(len(Alw),len(Alw[1]),Alw[0]))
        LL = Alw[1]
        for A1 in LL:
            logs.log_info('TELL %d %s\nTELL\nTELL\n'%(len(A1),str(A1)))
   
