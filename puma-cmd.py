# Skryt do prostego zarządzanie użytkownikami w programie PUMA firmy ZETOSOFTWARE
# Testowane na wersji 2.7.9
# Moduły:
# - pyreadline (https://pypi.python.org/pypi/pyreadline/2.0)
# - psycopg2 (http://www.stickpeople.com/projects/python/win-psycopg/2.5.3/psycopg2-2.5.3.win32-py2.7-pg9.3.4-release.exe)   
import psycopg2
import sys
import readline 

try:
	connection=psycopg2.connect("dbname='PUMA' user='puma' password='z3T0so13Pum1' host='192.168.0.1' port='5433'")
	print "$ Polaczenie ustanowione"
	print "------------------------"
except:
	print "Nie udalo sie polaczyc"
	sys.exit()

conn=connection.cursor()
COMMANDS = {'exit':'','show':{'cashboxes':'','connections':'','locks':'','users':''},'login':'','kill':'','unlock':'','whoami':''}

def funkcja_zlozona(COMMANDS,text,bufor):
    lista = []
    try:#szuka spacji
        pierwsza_spacja=bufor.index(" ")
        el_pierwszego=bufor[:pierwsza_spacja]#do spacji
        COMMANDS=COMMANDS[el_pierwszego]
        lista = funkcja_zlozona(COMMANDS,text,bufor[pierwsza_spacja+1:])#szuka dalej do nastepnej spacji
        return lista
    except:
        COMMANDS=COMMANDS
        if COMMANDS=='':
            return lista
        else:
            for key,value in sorted(COMMANDS.iteritems()):
                if key.startswith(text):
                    lista.append(key)
            return lista  

def complete(text,state):
    bufor = readline.get_line_buffer()
    result = [x for x in funkcja_zlozona(COMMANDS,text,bufor)] #wyszukuje w liscie polecen
    return result[state]

def whoami(kursor):
    conn.execute("begin")
    conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
    try:
        conn.execute("SELECT nazwa FROM pg_stat_activity \
join admi.uz_zalogowani on pg_stat_activity.procpid=uz_zalogowani.pid \
join admi.uzytkownicy on uz_zalogowani.id_uzytkownika=admi.uzytkownicy.id where procpid=pg_backend_pid()")
        wiersz=conn.fetchone()
        print 'Uzytkownik '+str(wiersz[0]) 
        return 1
    except:
        print "Blad: Nie jestes zalogowany" 
        return 0
    finally:
        conn.execute("COMMIT")

readline.parse_and_bind("tab: complete")
readline.set_completer(complete)
while True:
       cmd=raw_input("$ ")
       if cmd=='exit':
            conn.close()
            connection.close()
            sys.exit()
       elif cmd=='help':
            print "\n"
            print "help - wypisuje to co widzisz teraz"
            print "kill <pid> - konczy polaczenie danego uzytkownika"
            print "login <uid> - logowanie do programu"
            print "show connections - pokazuje aktualnie zalogowanych"
            print "show cashboxes - pokazuje status kas"
            print "unlock <nr_kasy> - odblokowanie kasy"
            print "whoami - sprawdza czy jestes zalogowany"
            print "exit - konczy prace"
            print "\n"
       elif cmd=='show connections':
            conn.execute("BEGIN")
            conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            conn.execute("DELETE FROM admi.uz_zalogowani WHERE 0=(SELECT COUNT(datid) FROM pg_stat_activity WHERE procpid=pid)")
            conn.execute("SELECT procpid,nazwa,client_addr,client_port,id_uzytkownika,to_char(uz_zalogowani.t_data_utworzenia, \
'FMDay, DD MM HH24:MI:SS YYYY') as data FROM pg_stat_activity \
left join admi.uz_zalogowani on pg_stat_activity.procpid=uz_zalogowani.pid \
left join admi.uzytkownicy on uz_zalogowani.id_uzytkownika=admi.uzytkownicy.id order by client_addr,data,pid")
            lista=conn.fetchall()
            print "\n"
            print "{:<6}{:<23}{:<17}{:<30}".format('PID', 'Uzytkownik', 'Adres IP', 'Ustanowienie polaczenia')
            print "{:<6}{:<23}{:<17}{:<30}".format('-----', '----------------------', '----------------','------------------------------')
            for wiersz in lista:
                if wiersz[1]=='komunikator':
                    print "{:<8}{:<21}{:<17}{:<30}".format(wiersz[0], wiersz[1], wiersz[2], wiersz[5])
                else:
                    print "{:<6}{:<23}{:<17}{:<30}".format(wiersz[0], wiersz[1], wiersz[2], wiersz[5])
            conn.execute("COMMIT")
            print '\n'
       elif cmd.startswith('kill '):
            pierwsza_spacja=cmd.index(" ")
            parametr = cmd[pierwsza_spacja+1:]
            try:
                parametr = int(parametr)
                try:
                    conn.execute("BEGIN")
                    conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                    conn.callproc("pg_terminate_backend",[parametr])
                    conn.execute("COMMIT")
                    print "Polaczenia zostalo zamkniete"
                except:
                    print "Blad: Nie udalo sie zamknac polaczenia"
            except:
                print "Blad: Nieprawidlowy parametr\nUsage: kill <pid>"
       elif cmd.startswith('login '):
            pierwsza_spacja=cmd.index(" ")
            parametr = cmd[pierwsza_spacja+1:]
            try:
                parametr = int(parametr)
                try:
                    conn.execute("BEGIN")
                    conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                    conn.callproc("ustaw_id_uzytkownika",[parametr])
                    conn.callproc("admi.fu_pobierzPID",[parametr])
                    conn.execute("commit")
                    try:
                        conn.execute("select id,nazwa from admi.uzytkownicy where id=%(parametr)s",dict(parametr=parametr))
                        wiersz=conn.fetchone()
                        print 'Zalogowano jako '+str(wiersz[1])
                    except:
                        print "Blad: Nie jestes zalogowany"
                except:
                    print "Blad: Ustawienie id uzytkownika"
            except:
                print "Blad: Nieprawidlowy parametr\nUsage: login <uid>"
       elif cmd=='show cashboxes':
            print "\n"
            conn.execute("BEGIN")
            conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            conn.execute("SELECT K.id, kasa, k.nazwa, rok, nrkp, nrkw, walutowa, aktywna, u.nazwa AS uzytkownikm FROM kasa.kasy k LEFT OUTER JOIN admi.uzytkownicy u ON k.aktywna=u.id ORDER BY to_number(kasa, text(99999999)) asc")
            lista=conn.fetchall()
            print "{:<4}{:<20}{:<4}".format('Nr', 'Nazwa', 'Pracuje')
            print "{:<4}{:<20}{:<4}".format('---', '-------------------','------------')
            for wiersz in lista:
                if wiersz[8] is not None:
                    print "{:<4}{:<20}{:<20}".format(wiersz[1], wiersz[2], wiersz[8])
                else:
                    print "{:<4}{:<20}{:<20}".format(wiersz[1], wiersz[2], '')
            conn.execute("COMMIT")
            print "\n"
       elif cmd=='show users':
            print '\n'
            conn.execute("BEGIN")
            conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            conn.execute("select cast(id as int) as id,nazwa,imie,nazwisko from admi.uzytkownicy order by id")
            wiersze=conn.fetchall()
            print "{:<6}{:<23}{:<14}{:<21}".format('ID', 'Nazwa', 'Imie','Nazwisko')
            print "{:<6}{:<23}{:<14}{:<21}".format('-----', '----------------------','-------------','------------------------------')
            for wiersz in wiersze:
                print "{:<6}{:<23}{:<14}{:<21}".format(wiersz[0],wiersz[1],wiersz[2],wiersz[3])
            conn.execute("COMMIT")
            print "\n"
       elif cmd.startswith('unlock '):
            pierwsza_spacja=cmd.index(" ")
            parametr = cmd[pierwsza_spacja+1:]
            try:
                parametr = int(parametr)
                if whoami(conn)==1:
                    conn.execute("BEGIN")
                    conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                    conn.execute("update kasa.kasy set aktywna=0 where kasy.kasa='%(parametr)s'",dict(parametr=parametr))
                    conn.execute("COMMIT")
                    print "Kasa jest odblokowana"
                else:
                    print "Blad: Nie udalo sie odblokowac kasy, musisz sie zalogowac"                              
            except:
                print "Blad: Nieprawidlowy parametr\nUsage: unlock <nr_kasy>"
       elif cmd=='whoami':
            x = whoami(conn)
       else:
            print "Blad: Nieprawidlowe polecenie"