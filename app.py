from flask import Flask, render_template, request, redirect, url_for
import json
import math
import datetime
import logging
import random
import os

app = Flask(__name__)

print_warning = False

MODALITA_ALLENAMENTO = True # se si sta facendo un allenamento a squadre, mettere True per disattivare il sorting e i punteggi
nome_allenamento = "allenamento_prima"

MODALITA_100_PROBLEMS = False # deprecated, probabilmente non funziona
parziale_classifica = 0 # cicla tra 0 e 3

minuti_oscuri = 5

numero_massimo_di_squadre_da_nascondere_a_fine_gara = 999 # sì, il nome della variabile DEVE essere così lungo :)

password_inserimento_terminale = "dsa321"

# APERTURA E LETTURA DEL FILE JSON, CON ASSEGNAZIONE DELLE VARIABILI
file_json = open(f"{nome_allenamento}.json" if MODALITA_ALLENAMENTO else "gara_100.json" if MODALITA_100_PROBLEMS else "gara.json", "r", encoding="utf-8")
json_data = json.load(file_json)
n = json_data["n"]
fine_incremento = json_data["fine_incremento"]
incremento_errore = json_data["incremento_errore"]
bonus_risposte = json_data["bonus_risposte"] # esce come list
bonus_fullato = json_data["bonus_fullato"] # esce come list
risultati = json_data["risultati"] #esce come list
squadre = json_data["squadre"] # esce come list
durata_in_minuti = json_data["durata"]
tempo_jolly = json_data["tempo_jolly"]
file_json.close()


numero_problemi = len(risultati)
numero_squadre = len(squadre)

ospiti = 0
for i in range(numero_squadre):
    if "(ospite)" in squadre[i].lower():
        ospiti += 1
    squadre[i] += f" ({(i + 1):02})"


# SETUP DEL TEMPO
datetime_inizio = datetime.datetime.now()
unix_improprio_inizio = datetime.datetime.timestamp(datetime_inizio)
unix_improprio_fine = unix_improprio_inizio + durata_in_minuti * 60

# SETUP LOGGER
data_log = f"{datetime_inizio.year}.{datetime_inizio.month:02}.{datetime_inizio.day:02}_{datetime_inizio.hour:02}.{datetime_inizio.minute:02}.{datetime_inizio.second:02}"
logger = logging.getLogger("werkzeug")
logging.basicConfig(level=logging.WARNING, filename=f"logs/log_{'allenamento' if MODALITA_ALLENAMENTO else 'gara'}_{data_log}.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s") # i "veri" log saranno dei warning, tutta la roba delle richieste GET e POST sarà info

if MODALITA_ALLENAMENTO:
    logging.warning("Questo e' un allenamento. Sono disattivati il sorting e i punteggi")
    if print_warning:
        print("Questo e' un allenamento. Sono disattivati il sorting e i punteggi")

# SETUP CLASSE PROBLEMA E "DATABASE" PROBLEMI
class Problema():
    def __init__(self, VALORE, NUMERO_SOLUZIONI):
        self.VALORE = VALORE
        self.NUMERO_SOLUZIONI = NUMERO_SOLUZIONI
db_problemi = [Problema(20, 0) for _ in range(numero_problemi)]

# SETUP CLASSE CELLA E "DATABASE" CELLE
class Cella(): # IMPORTANTE: se il problema è jollato "PUNTEGGIO" è già raddoppiato
    def __init__(self, STATO, JOLLY, PUNTEGGIO):
        self.STATO = STATO # 0 bianco, 1 giusto, -1 sbagliato
        self.JOLLY = JOLLY # 0 non messo, 1 messo prima di aver risolto, -1 messo dopo aver risolto
        self.PUNTEGGIO = PUNTEGGIO
db_celle = [[Cella(0, 0, 0) for _ in range(numero_problemi + 2)] for __ in range(numero_squadre)]


numero_full = 0

def check_full():
    global numero_full
    if numero_full >= len(bonus_fullato):
        return
    
    for id_squadra in range(numero_squadre):
        if db_celle[id_squadra][numero_problemi].STATO == 1: # se il full è già stato registrato
            continue

        res = True
        for id_cella in range(numero_problemi):
            if db_celle[id_squadra][id_cella].STATO != 1:
                res = False
                break
        if res:
            logging.warning(f"La squadra \"{squadre[id_squadra]}\" ha fullato e ha ottenuto un bonus di {bonus_fullato[numero_full]} punti")
            if print_warning:
                print(f"La squadra \"{squadre[id_squadra]}\" ha fullato e ha ottenuto un bonus di {bonus_fullato[numero_full]} punti")
            db_celle[id_squadra][numero_problemi].PUNTEGGIO += bonus_fullato[numero_full]
            db_celle[id_squadra][numero_problemi].STATO = 1
            if id_squadra + 1 <= numero_squadre - ospiti: # se la squadra non è ospite
                numero_full += 1


# SETUP DEGLI HEADER
def headings():
    problemi_mostrati = range(numero_problemi)

    if MODALITA_100_PROBLEMS:
        problemi_mostrati = range(parziale_classifica * 25, (parziale_classifica + 1) * 25)
    
    return ["Pos.", "Squadra", "Punteggio"] + [f"{i + 1}" for i in problemi_mostrati]

easter_egg = False
onorificienze = ["il boss", "il dev", "il migliore", "il supremo", "l'ineguagliabile", "l'insuperabile", "il modesto", "il magnifico", "il non TDNaro", "il geometra", "Mosele"]

# SETUP DEL RESTO DELLA TABELLA
def RIGA(i):
    problemi_mostrati = range(numero_problemi)

    if MODALITA_100_PROBLEMS:
        problemi_mostrati = range(parziale_classifica * 25, (parziale_classifica + 1) * 25)

    if i == 0:
        return [("", 0, 0) for _ in range(3)] + [(db_problemi[j].VALORE, 0, 0) for j in problemi_mostrati]
    
    nome = squadre[i - 1]

    if easter_egg:
        if ("mosele" in nome.lower() or "mosy" in nome.lower()) and random.randint(1, 10) == 1:
            nome = nome[:-4] + random.choice(onorificienze) + " " + nome[-4:]

    cella_pos = (i, 0, 0)
    cella_nome = (nome, 0, 0)
    cella_punteggio = ("chupa" if MODALITA_ALLENAMENTO else numero_problemi * 10 + sum(db_celle[i - 1][index].PUNTEGGIO for index in range(numero_problemi + 2)), 0, 0)

    return [cella_pos, cella_nome, cella_punteggio] + [(db_celle[i - 1][k].PUNTEGGIO, db_celle[i - 1][k].STATO, db_celle[i - 1][k].JOLLY) for k in problemi_mostrati]

data = []

def update_data():
    check_full()

    global data
    data = [RIGA(squadra) for squadra in range(numero_squadre + 1)]
update_data()

problema_jollato = [0 for _ in range(numero_squadre)]

def sorta_squadre():
    global data
    data = [data[0]] + sorted(data[1: numero_squadre + 1 - ospiti], key=lambda R: (int(R[2][0]), 0 if problema_jollato[int(R[1][0][-3:-1]) - 1] == 0 else db_celle[int(R[1][0][-3:-1]) - 1][problema_jollato[int(R[1][0][-3:-1]) - 1] - 1].PUNTEGGIO), reverse=True) + sorted(data[numero_squadre + 1 - ospiti:], key=lambda R: (int(R[2][0]), 0 if problema_jollato[int(R[1][0][-3:-1]) - 1] == 0 else db_celle[int(R[1][0][-3:-1]) - 1][problema_jollato[int(R[1][0][-3:-1]) - 1] - 1].PUNTEGGIO), reverse=True)
    for i in range(1, numero_squadre + 1):
        data[i][0] = (i, 0, 0)

durata_gara = durata_in_minuti * 60
secondi = durata_gara % 60
minuti = int((durata_gara // 60) % 60) # sì, lo so che non ha senso definire i minuti in questo modo ma lascia stare così
ore = int(durata_gara // 3600)
tempo_rimanente = durata_gara

suffisso_classifica = ""

gia_oscurata = False
gia_finita = False
gia_gestito_jolly = False


squadre_da_nascondere = min(numero_squadre - ospiti, numero_massimo_di_squadre_da_nascondere_a_fine_gara)

def sveglia(): # nome un po' creativo, è la funzione che gestisce il tempo qui su python
    global suffisso_classifica

    global gia_oscurata
    global gia_finita
    global gia_gestito_jolly

    prev_tempo_passato = durata_gara - tempo_rimanente
    puo_ancora_incrementare = (prev_tempo_passato < fine_incremento * 60)
    update_tempo()
    curr_tempo_passato = durata_gara - tempo_rimanente

    if tempo_rimanente < minuti_oscuri * 60 and not gia_oscurata:
        gia_oscurata = True
        logging.warning("Classifica oscurata")
        if print_warning:
            print("Classifica oscurata")
        suffisso_classifica = "_oscurata"
    
    if tempo_rimanente <= 0 and not gia_finita:
        gia_finita = True
        logging.warning("Allenamento terminato" if MODALITA_ALLENAMENTO else "Gara terminata")
        if print_warning:
            print("Allenamento terminato" if MODALITA_ALLENAMENTO else "Gara terminata")
        suffisso_classifica = "_fine"
        puo_ancora_incrementare = False # per evitare casini
        
        try:
            file_html = open(f"{os.getcwd()}/archivio_gare/{'tabellone_finale_allenamento' if MODALITA_ALLENAMENTO else 'classifica_finale'}_{data_log}.html", "w", encoding="utf-8")
            file_html.write(render_template("classifica_fine.html", headings=headings(), data=data, squadre_nascoste=0).replace("/static/", ""))
            file_html.close()
        except:
            logging.error("E' stato riscontrato un errore nel salvataggio della classifica finale")

    differenza = min((curr_tempo_passato // 60) - (prev_tempo_passato // 60), fine_incremento - (prev_tempo_passato // 60))

    if puo_ancora_incrementare and curr_tempo_passato >= 60 and differenza != 0:
        problemi_incrementati = []
        for id_problema in range(numero_problemi):
            if db_problemi[id_problema].NUMERO_SOLUZIONI >= n:
                continue

            db_problemi[id_problema].VALORE += int(differenza) # no, non si rischia che nel frattempo qualcuno abbia cappato un problema perché check_risultato() per prima cosa chiama sveglia()
            problemi_incrementati.append(id_problema + 1)
            for id_squadra in range(numero_squadre):
                if db_celle[id_squadra][id_problema].STATO == 1:
                    db_celle[id_squadra][id_problema].PUNTEGGIO += int(differenza) * (2 if (db_celle[id_squadra][id_problema].JOLLY == 1) else 1)

        if problemi_incrementati:
            logging.warning(f"{'Incrementato' if len(problemi_incrementati) == 1 else 'Incrementati'} di {int(differenza)} {'punto' if differenza == 1 else 'punti'} il valore {'del problema' if len(problemi_incrementati) == 1 else 'dei problemi'} {', '.join(map(str, problemi_incrementati))}")
            if print_warning:
                print(f"{'Incrementato' if len(problemi_incrementati) == 1 else 'Incrementati'} di {int(differenza)} {'punto' if differenza == 1 else 'punti'} il valore {'del problema' if len(problemi_incrementati) == 1 else 'dei problemi'} {', '.join(map(str, problemi_incrementati))}")

    if not gia_gestito_jolly and curr_tempo_passato >= tempo_jolly * 60:
        gia_gestito_jolly = True
        for id_squadra in range(numero_squadre):
            hanno_jolly = False
            for id_cella in range(numero_problemi):
                if db_celle[id_squadra][id_cella].JOLLY != 0:
                    hanno_jolly = True
                    break
            if not hanno_jolly and not MODALITA_ALLENAMENTO:
                logging.warning(f"Jolly impostato di default sul problema 1 per la squadra \"{squadre[id_squadra]}\"")
                if print_warning:
                    print(f"Jolly impostato di default sul problema 1 per la squadra \"{squadre[id_squadra]}\"")
                db_celle[id_squadra][0].JOLLY = 1 if (db_celle[id_squadra][0].STATO != 1) else -1
                problema_jollato[id_squadra] = 1


    update_data()
    if not MODALITA_ALLENAMENTO:
        sorta_squadre()

def update_tempo():
    global secondi
    global minuti
    global ore
    global tempo_rimanente

    tempo_rimanente = unix_improprio_fine - datetime.datetime.timestamp(datetime.datetime.now())
    secondi = math.floor(tempo_rimanente % 60)
    minuti = math.floor((tempo_rimanente // 60) % 60)
    ore = int(tempo_rimanente // 3600)

sveglia()


codice_squadra = 0
numero_problema = 0
risultato = 0

def check_risultato():
    sveglia() # sveglia() va chiamata spesso, quindi chiamiamola anche qua dentro

    local_cs = codice_squadra # ottimizzazione
    local_np = numero_problema # ottimizzazione

    squadra_ospite = local_cs > numero_squadre - ospiti

    if risultato == -1:
        if durata_gara - tempo_rimanente < tempo_jolly * 60:
            logging.warning(f"La squadra \"{squadre[local_cs - 1]}\" ha impostato il jolly sul problema {local_np}")
            if print_warning:
                print((f"La squadra \"{squadre[local_cs - 1]}\" ha impostato il jolly sul problema {local_np}"))
            for prob in range(numero_problemi):
                db_celle[local_cs - 1][prob].JOLLY = 0
            db_celle[local_cs - 1][local_np - 1].JOLLY = 1 if (db_celle[local_cs - 1][local_np - 1].STATO != 1) else -1
            problema_jollato[local_cs - 1] = local_np
            update_data()
            if not MODALITA_ALLENAMENTO:
                sorta_squadre()

        elif MODALITA_ALLENAMENTO and local_cs == 1:
            logging.warning(f"Il capitano \"{squadre[0]}\" ha impostato il jolly della squadra sul problema {local_np}")
            if print_warning:
                print(f"Il capitano \"{squadre[0]}\" ha impostato il jolly della squadra sul problema {local_np}")

            problema_gia_risolto = False
            for id_squadra in range(numero_squadre):
                if db_celle[id_squadra][local_np - 1].STATO == 1:
                    problema_gia_risolto = True
                    break

            for id_squadra in range(numero_squadre):
                for prob in range(numero_problemi):
                    db_celle[id_squadra][prob].JOLLY = 0
                db_celle[id_squadra][local_np - 1].JOLLY = -1 if problema_gia_risolto else 1
            update_data()

        return


    moltiplicatore = (5 if MODALITA_100_PROBLEMS else 2) if (db_celle[local_cs - 1][local_np - 1].JOLLY == 1) else 1
        
    if db_celle[local_cs - 1][local_np - 1].STATO != 1:
        if risultato == risultati[local_np - 1]:
            logging.warning(f"La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato e' giusto.")
            if print_warning:
                print(f"La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato e' giusto.")
            db_celle[local_cs - 1][local_np - 1].PUNTEGGIO += db_problemi[local_np - 1].VALORE * moltiplicatore # assegno alla squadra il valore del problema
            if (db_problemi[local_np - 1].NUMERO_SOLUZIONI < len(bonus_risposte)):
                db_celle[local_cs - 1][local_np - 1].PUNTEGGIO += bonus_risposte[db_problemi[local_np - 1].NUMERO_SOLUZIONI] * moltiplicatore # assegno alla squadra l'eventuale bonus
            db_celle[local_cs - 1][local_np - 1].STATO = 1 # segno che il problema è giusto
            if not squadra_ospite: # se la squadra non è ospite
                db_problemi[local_np - 1].NUMERO_SOLUZIONI += 1 # aggiungo 1 al numero di soluzioni del problema
        else:
            logging.warning(f"La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato e' sbagliato.")
            if print_warning:
                print(f"La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato e' sbagliato.")
            db_celle[local_cs - 1][local_np - 1].PUNTEGGIO -= 10 * moltiplicatore # levo 10 (o 20) punti alla squadra
            if db_celle[local_cs - 1][local_np - 1].STATO != -1 and not squadra_ospite: # se è il primo errore e la squadra non è ospite
                db_problemi[local_np - 1].VALORE += incremento_errore # incremento il valore del problema
                logging.warning(f"Incrementato di {incremento_errore} {'punto' if incremento_errore == 1 else 'punti'} il valore del problema {local_np} a seguito dell'errore")
                if print_warning:
                    print(f"Incrementato di {incremento_errore} {'punto' if incremento_errore == 1 else 'punti'} il valore del problema {local_np} a seguito dell'errore")
                for squadra in range(numero_squadre): # incremento il punteggio alle squadre che hanno risolto il problema
                    if (db_celle[squadra][local_np - 1].STATO == 1):
                        db_celle[squadra][local_np - 1].PUNTEGGIO += incremento_errore * ((5 if MODALITA_100_PROBLEMS else 2) if (db_celle[squadra][local_np - 1].JOLLY == 1) else 1)
            db_celle[local_cs - 1][local_np - 1].STATO = -1 # segno che il problema è sbagliato

    update_data()
    if not MODALITA_ALLENAMENTO:
        sorta_squadre()


@app.route("/classifica") # classifica (gestisce anche quella oscurata e quella finale)
def classifica():
    global parziale_classifica
    
    sveglia()

    squadre_nascoste = request.args.get("nascoste")

    if squadre_nascoste:
        try:
            squadre_nascoste = int(squadre_nascoste)
        except:
            squadre_nascoste = squadre_da_nascondere
    else:
        squadre_nascoste = squadre_da_nascondere
    
    if squadre_nascoste > numero_squadre - ospiti:
        squadre_nascoste = squadre_da_nascondere

    if suffisso_classifica != "_fine": #funziona ma la logica potrebbe essere scritta molto meglio. tuttavia, non ho voglia
        squadre_nascoste = 0

    classifica_html = render_template(f"classifica{suffisso_classifica}.html", headings=headings(), data= [data[0]] + [[("?", 0, 0), ("?????", 0, 0), ("???", 0, 0)] + [("?", 0, 0)] * numero_problemi] * squadre_nascoste + data[squadre_nascoste + 1:], tempo=f"{f'{ore}:' if ore > 0 else ''}{minuti:02}:{secondi:02}", squadre_nascoste=squadre_nascoste)
    
    if suffisso_classifica == "_fine":
        classifica_html = render_template(f"classifica_fine.html", headings=headings(), data= [data[0]] + [[("?", 0, 0), ("?????", 0, 0), ("???", 0, 0)] + [("?", 0, 0)] * numero_problemi] * squadre_nascoste + data[squadre_nascoste + 1:], tempo=f"{f'{ore}:' if ore > 0 else ''}{minuti:02}:{secondi:02}", squadre_nascoste=squadre_nascoste)
        
        if squadre_nascoste == 0: # sì, la classifica viene salvata due volte. questo perché potrebbero essere stati inseriti degli ultimi risultati dopo il termine della gara, ma voglio comunque assicurarmi il salvataggio a fine gara
            try:
                file_html = open(f"{os.getcwd()}/archivio_gare/{'tabellone_finale_allenamento' if MODALITA_ALLENAMENTO else 'classifica_finale'}_{data_log}.html", "w", encoding="utf-8")
                file_html.write(classifica_html.replace("/static/", ""))
                file_html.close()
            except:
                logging.error("E' stato riscontrato un errore nel salvataggio della classifica finale")
    
    if suffisso_classifica == "" and ("127.0.0.1" in request.url_root or "localhost" in request.url_root):
        classifica_html = render_template(f"classifica_veloce.html", headings=headings(), data= [data[0]] + [[("?", 0, 0), ("?????", 0, 0), ("???", 0, 0)] + [("?", 0, 0)] * numero_problemi] * squadre_nascoste + data[squadre_nascoste + 1:], tempo=f"{f'{ore}:' if ore > 0 else ''}{minuti:02}:{secondi:02}", squadre_nascoste=squadre_nascoste)
    

    if MODALITA_100_PROBLEMS:
        parziale_classifica = (parziale_classifica + 1) % 4

    return classifica_html

@app.route("/inserimento", methods=["POST", "GET"]) # pagina di inserimento
def inserimento():
    if request.method == "POST":
        request_password = request.form["password"]
        request_codice_squadra = request.form["codice_squadra"]
        request_numero_problema = request.form["numero_problema"]
        request_risultato = request.form["risultato"]
        try:
            global codice_squadra
            global numero_problema
            global risultato
            codice_squadra = int(request_codice_squadra)
            numero_problema = int(request_numero_problema)
            risultato = int(request_risultato)
        except:
            return redirect(url_for("errore"))
        
        if codice_squadra < 1 or codice_squadra > numero_squadre or numero_problema < 1 or numero_problema > numero_problemi or risultato < -1 or risultato > 9999:
            return redirect(url_for("errore"))
        
        if request_password == password_inserimento_terminale:
            check_risultato()

    return render_template("inserimento.html", squadre=squadre)

@app.route("/errore", methods=["POST", "GET"]) # qui si arriva se si sbaglia l'inserimento
def errore():
    if request.method == "POST":
        return redirect(url_for("inserimento"))
    return render_template("errore.html")

@app.route("/") # la root redirecta subito alla classifica
def root():
    return redirect(url_for("classifica"))

@app.route("/i") # /i redirecta subito all'inserimento
def i():
    return redirect(url_for("inserimento"))

@app.route("/terminale", methods = ["POST", "GET"]) # terminale per admin
def terminale():
    if request.method == "POST":
        request_password = request.form["password"]
        request_comando = request.form["comando"]
        if request_password == password_inserimento_terminale:
            esegui_comando(request_comando)
    return render_template("terminale.html")


file_partecipanti = open("partecipanti.txt", "r", encoding="utf-8")
partecipanti = []

temp = []
for line in file_partecipanti.readlines():
    if line == "\n":
        partecipanti.append(temp)
        temp = []
        continue
    temp.append(line.replace("\n", ""))
partecipanti.append(temp)

@app.route("/squadre") # lista di squadre partecipanti e membri
def squadre_page():
    return render_template("squadre.html", partecipanti=partecipanti)

def esegui_comando(comando):
    global n
    global fine_incremento
    global incremento_errore

    sveglia()

    logging.warning(f"Chiamato il comando \"{comando}\"")
    if print_warning:
        print(f"Chiamato il comando \"{comando}\"")
    
    protocollo = comando.split()

    try:
        match protocollo[0]:
            case "bonus" | "malus":
                if protocollo[2] == "reset":
                    db_celle[int(protocollo[1]) - 1][numero_problemi + 1].PUNTEGGIO = 0
                else:
                    db_celle[int(protocollo[1]) - 1][numero_problemi + 1].PUNTEGGIO += int(protocollo[2]) * (1 if protocollo[0] == "bonus" else -1)
        
            case "modifica":
                match protocollo[1]:
                    case "risultato":
                        risultati[int(protocollo[2]) - 1] = int(protocollo[3])
                    case "valore":
                        db_problemi[int(protocollo[2]) - 1].VALORE = int(protocollo[3])

                    case "n":
                        n = int(protocollo[2])
                    case "fine_incremento":
                        fine_incremento = int(protocollo[2])
                    case "incremento_errore":
                        incremento_errore = int(protocollo[2])
                    case _:
                        logging.error("Comando non valido")

            case "salva":
                try:
                    adesso = datetime.datetime.now()
                    ora_formattata = f"{adesso.hour:02}.{adesso.minute:02}.{adesso.second:02}"

                    nome_file = f"{'salvataggio_allenamento' if MODALITA_ALLENAMENTO else 'salvataggio_classifica'}_{data_log}_eseguito_{ora_formattata}.html"                    
                    classifica_html = render_template("classifica_ferma.html", headings=headings(), data=data, tempo=f"{f'{ore}:' if ore > 0 else ''}{minuti:02}:{secondi:02}")


                    file_html = open(f"{os.getcwd()}/archivio_gare/{nome_file}", "w", encoding="utf-8")
                    file_html.write(classifica_html.replace("/static/", ""))
                    file_html.close()
                except:
                    logging.error("E' stato riscontrato un errore nel salvataggio della classifica istantanea")

            case _:
                logging.error("Comando non valido")
    except:
        logging.error("Comando non valido")

    update_data()
    if not MODALITA_ALLENAMENTO:
        sorta_squadre()


if __name__ == "__main__": # bo, non viene chiamato. strano lol (comunque funziona)
    print("app.py sta runnando come processo main")
    app.run(debug = False)
