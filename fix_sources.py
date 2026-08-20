import sqlite3
names=['cshot8','LoveU','am_you','eshgholaneofficial','eshgholanehman','eshgham','ProfiileSet','ProfileSet1','loverlike1990','Ashoftegi_official','Mentalist_Persian','+Zim57Xc01AxjYTk0','PROFILE_BHN02','TOP_PROFILE_SA','nabz_ehsasa','Aysaan_ft','okjjjegool','lux_o_v','9076','giiif_69','yavashakidoostetdaramm','romance_kiss','Limitllless','mydeream','+45l5pGAWg3IyZTdk','seshot6','storytime44','+lktyyIMFX-k2Y2Vi','+NepSdZCOvyhhOWRk','WibeOfMe','pink_cigaaarette','vippluschannel','Brayeeeetoo','+OPEHRZG6Ql050TQ0','tehrani','Pickupm','Horniam2','besthotiran','dirty_lovee']
con=sqlite3.connect('auto_pub.db')
con.execute('DELETE FROM sources')
for n in names:
    try: con.execute('INSERT INTO sources (username) VALUES (?)',(n,))
    except Exception: pass
con.commit(); print('sources rebuilt:', con.execute('SELECT COUNT(*) FROM sources').fetchone()[0])
