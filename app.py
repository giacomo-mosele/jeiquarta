from flask import Flask, render_template, request, redirect, url_for
import json
import math
import datetime
import logging
import random

app = Flask(__name__)

minuti_oscuri = 5

numero_minimo_di_squadre_da_nascondere_a_fine_gara = 10 # sì, il nome della variabile DEVE essere così lungo :)
squadre_nascoste = 0

# APERTURA E LETTURA DEL FILE JSON, CON ASSEGNAZIONE DELLE VARIABILI
f = open("gara.json")
json_data = json.load(f)
n = json_data["n"]
fine_incremento = json_data["fine_incremento"]
incremento_errore = json_data["incremento_errore"]
bonus_risposte = json_data["bonus_risposte"] # esce come list
bonus_fullato = json_data["bonus_fullato"] # esce come list
risultati = json_data["risultati"] #esce come list
squadre = json_data["squadre"] # esce come list
durata_in_minuti = json_data["durata"]
tempo_jolly = json_data["tempo_jolly"]
f.close()

datetime_inizio = datetime.datetime.now()
unix_improprio_inizio = datetime.datetime.timestamp(datetime_inizio)
unix_improprio_fine = unix_improprio_inizio + durata_in_minuti * 60

data_log = f"{datetime_inizio.year}.{datetime_inizio.month:02}.{datetime_inizio.day:02}_{datetime_inizio.hour:02}.{datetime_inizio.minute:02}.{datetime_inizio.second:02}"
logger = logging.getLogger("werkzeug")
logging.basicConfig(level=logging.WARNING, filename=f"logs/log_gara_{data_log}.log", filemode="w", # i "veri" log saranno dei warning, tutta la roba delle richieste GET e POST non sarà loggata
                    format="%(asctime)s - %(levelname)s - %(message)s")


numero_problemi = len(risultati)
numero_squadre = len(squadre)
numero_full = 0

for i in range(numero_squadre):
    squadre[i] += f" ({(i + 1):02})"


class Problema():
    def __init__(self, NUMERO_PROBLEMA, VALORE, NUMERO_SOLUZIONI):
        self.NUMERO_PROBLEMA = NUMERO_PROBLEMA
        self.VALORE = VALORE
        self.NUMERO_SOLUZIONI = NUMERO_SOLUZIONI
db_problemi = [Problema(i, 20, 0) for i in range(1, numero_problemi + 1)]

class Cella(): # IMPORTANTE: se il problema è jollato "PUNTEGGIO" è già raddoppiato
    def __init__(self, STATO, BONUS, JOLLY, PUNTEGGIO):
        self.STATO = STATO # 0 bianco, 1 giusto, -1 sbagliato
        self.BONUS = BONUS
        self.JOLLY = JOLLY # 0 non messo, 1 messo prima di aver risolto, -1 messo dopo aver risolto
        self.PUNTEGGIO = PUNTEGGIO

db_celle = [[Cella(0, 0, 0, 0) for index in range(0, numero_problemi + 2)] for codice_squadra in range(1, numero_squadre + 1)] # ho provato anche a migliorare questa scrittura ma non ci sono riuscito, boh, strano

# SETUP DEGLI HEADER
headings = tuple(["Squadra", "Punteggio"] + [f"{i + 1}" for i in range (0, numero_problemi)])

easter_egg = True
onorificienze = ["il boss", "il dev", "il migliore", "il supremo", "l'ineguagliabile", "l'insuperabile", "il modesto", "il magnifico", "il non TDNaro", "il geometra", "Mosele"]

# SETUP DEL RESTO DELLA TABELLA
def RIGA(i):
    if i == 0:
        return [("", 0, 0), ("", 0, 0)] + [(db_problemi[j].VALORE, 0, 0) for j in range(0, numero_problemi)]
    nome = squadre[i - 1]
    return [(nome if not (easter_egg and "Mosele" in nome and random.randint(1, 5) == 1) else (nome[:-4] + random.choice(onorificienze) + " " + nome[-4:]), 0, 0), (numero_problemi * 10 + sum(db_celle[i - 1][index].PUNTEGGIO for index in range (0, numero_problemi + 2)), 0, 0)] + [(db_celle[i - 1][k].PUNTEGGIO, db_celle[i - 1][k].STATO, db_celle[i - 1][k].JOLLY) for k in range(0, numero_problemi)]

data = []

def check_full():
    global numero_full
    if numero_full < len(bonus_fullato):
        for id_squadra in range(0, numero_squadre):
            if db_celle[id_squadra][numero_problemi].STATO != 1:
                res = True
                for id_cella in range(0, numero_problemi):
                    if db_celle[id_squadra][id_cella].STATO != 1:
                        res = False
                        break
                if res:
                    print(f"LOG: La squadra \"{squadre[id_squadra]}\" ha fullato e ha ottenuto un bonus di {bonus_fullato[numero_full]} punti")
                    logging.warning(f"LOG: La squadra \"{squadre[id_squadra]}\" ha fullato e ha ottenuto un bonus di {bonus_fullato[numero_full]} punti")
                    db_celle[id_squadra][numero_problemi].PUNTEGGIO += bonus_fullato[numero_full]
                    db_celle[id_squadra][numero_problemi].STATO = 1
                    numero_full += 1

def update_data():
    check_full()

    global data
    data = [RIGA(squadra) for squadra in range(0, numero_squadre + 1)]
update_data()

def sorta_squadre():
    global data
    data = [data[0]] + sorted(data[1: len(data)], key=lambda R: int(R[1][0]), reverse=True)

durata_gara = durata_in_minuti * 60
secondi = durata_gara % 60
minuti = int((durata_gara // 60) % 60) # sì, lo so che non ha senso definire in questo modo ma lascia stare così
ore = int(durata_gara // 3600)
tempo_rimanente = durata_gara

suffisso_classifica = ""

gia_oscurata = False
gia_finita = False

def sveglia(): # nome un po' creativo, è la funzione che gestisce il tempo qui su python
    global suffisso_classifica
    global squadre_nascoste
    global gia_oscurata
    global gia_finita

    prev_tempo_passato = durata_gara - tempo_rimanente
    puo_ancora_incrementare = (prev_tempo_passato < fine_incremento * 60) and not gia_finita
    update_tempo()
    curr_tempo_passato = durata_gara - tempo_rimanente

    if tempo_rimanente < minuti_oscuri * 60 and not gia_oscurata:
        gia_oscurata = True
        print("LOG: Classifica oscurata")
        logging.warning("LOG: Classifica oscurata")
        suffisso_classifica = "_oscurata"
    
    if tempo_rimanente <= 0 and not gia_finita:
        gia_finita = True
        print("LOG: Gara terminata")
        logging.warning("LOG: Gara terminata")
        suffisso_classifica = "_fine"
        puo_ancora_incrementare = False
        squadre_nascoste = min(numero_squadre, numero_minimo_di_squadre_da_nascondere_a_fine_gara)

    if (prev_tempo_passato // 60) != (curr_tempo_passato // 60) and puo_ancora_incrementare and curr_tempo_passato >= 60:
        for id_problema in range(0, numero_problemi):
            if db_problemi[id_problema].NUMERO_SOLUZIONI < n:
                db_problemi[id_problema].VALORE += 1
                for id_squadra in range(0, numero_squadre):
                    if db_celle[id_squadra][id_problema].STATO == 1:
                        db_celle[id_squadra][id_problema].PUNTEGGIO += 2 if (db_celle[id_squadra][id_problema].JOLLY == 1) else 1

    if curr_tempo_passato >= tempo_jolly * 60:
        for id_squadra in range(0, numero_squadre):
            hanno_jolly = False
            for id_cella in range(0, numero_problemi):
                if db_celle[id_squadra][id_cella].JOLLY != 0:
                    hanno_jolly = True
                    break
            if not hanno_jolly:
                print(f"LOG: Jolly impostato di default sul problema 1 per la squadra \"{squadre[id_squadra]}\"")
                logging.warning(f"LOG: Jolly impostato di default sul problema 1 per la squadra \"{squadre[id_squadra]}\"")
                db_celle[id_squadra][0].JOLLY = 1 if (db_celle[id_squadra][0].STATO != 1) else -1

    update_data()
    sorta_squadre()

def update_tempo():
    global secondi
    global minuti
    global ore
    global tempo_rimanente
    tempo_rimanente = unix_improprio_fine - datetime.datetime.timestamp(datetime.datetime.now())
    secondi = math.floor(tempo_rimanente % 60)
    minuti = math.floor((tempo_rimanente // 60) % 60)
    ore = math.floor(tempo_rimanente // 3600)


codice_squadra = 0
numero_problema = 0
risultato = 0

def check_risultato():
    sveglia() # sveglia() va chiamata spesso, quindi chiamiamola anche qua dentro

    local_cs = codice_squadra # ottimizzazione
    local_np = numero_problema # ottimizzazione

    moltiplicatore = 2 if (db_celle[local_cs - 1][local_np - 1].JOLLY == 1) else 1

    if risultato == -1:
        if durata_gara - tempo_rimanente < tempo_jolly * 60:
            print(f"LOG: La squadra \"{squadre[local_cs - 1]}\" ha impostato il jolly sul problema {local_np}")
            logging.warning(f"LOG: La squadra \"{squadre[local_cs - 1]}\" ha impostato il jolly sul problema {local_np}")
            for prob in range(0, numero_problemi):
                db_celle[local_cs - 1][prob].JOLLY = 0
            db_celle[local_cs - 1][local_np - 1].JOLLY = 1 if (db_celle[local_cs - 1][local_np - 1].STATO != 1) else -1
            update_data()
            sorta_squadre()
        return
        
    if db_celle[local_cs - 1][local_np - 1].STATO != 1:
        if risultato == risultati[local_np - 1]:
            print(f"LOG: La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato è giusto.")
            logging.warning(f"LOG: La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato è giusto.")
            db_celle[local_cs - 1][local_np - 1].PUNTEGGIO += db_problemi[local_np - 1].VALORE * moltiplicatore # assegno alla squadra il valore del problema
            if (db_problemi[local_np - 1].NUMERO_SOLUZIONI < len(bonus_risposte)):
                db_celle[local_cs - 1][local_np - 1].PUNTEGGIO += bonus_risposte[db_problemi[local_np - 1].NUMERO_SOLUZIONI] * moltiplicatore # assegno alla squadra l'eventuale bonus
            db_celle[local_cs - 1][local_np - 1].STATO = 1 # segno che il problema è giusto
            db_problemi[local_np - 1].NUMERO_SOLUZIONI += 1 # aggiungo 1 al numero di soluzioni del problema
        else:
            print(f"LOG: La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato è sbagliato.")
            logging.warning(f"LOG: La squadra \"{squadre[local_cs - 1]}\" ha consegnato {risultato} sul problema {local_np}. Questo risultato è sbagliato.")
            db_celle[local_cs - 1][local_np - 1].PUNTEGGIO -= 10 * moltiplicatore # levo 10 (o 20) punti alla squadra
            if db_celle[local_cs - 1][local_np - 1].STATO != -1:
                db_problemi[local_np - 1].VALORE += incremento_errore # incremento il valore del problema se è il primo errore
                for squadra in range(0, numero_squadre): # incremento il punteggio alla squadre che hanno risolto il problema
                    if (db_celle[squadra][local_np - 1].STATO == 1):
                        db_celle[squadra][local_np - 1].PUNTEGGIO += incremento_errore * (2 if (db_celle[squadra][local_np - 1].JOLLY == 1) else 1)
            db_celle[local_cs - 1][local_np - 1].STATO = -1 # segno che il problema è sbagliato
    update_data()
    sorta_squadre()


@app.route("/classifica", methods=["POST", "GET"]) # classifica
def classifica():
    global squadre_nascoste
    sveglia()
    if request.method == "POST":
        squadre_nascoste -= 1
    return render_template(f"classifica{suffisso_classifica}.html", headings=headings, data= [data[0]] + [[("?????", 0, 0), ("???", 0, 0)] + [("?", 0, 0)] * numero_problemi] * squadre_nascoste + data[squadre_nascoste + 1: numero_squadre + 1], tempo=f"{f'{ore}:' if ore > 0 else ''}{minuti:02}:{secondi:02}", squadre_nascoste=squadre_nascoste)

@app.route("/inserimento", methods=["POST", "GET"]) # pagina di inserimento
def inserimento():
    if request.method == "POST":
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
        if codice_squadra < 1 or numero_problema < 1 or codice_squadra > numero_squadre or numero_problema > numero_problemi or risultato < -1 or risultato > 9999:
            return redirect(url_for("errore"))
        check_risultato()
    return render_template("inserimento.html", squadre=squadre)

@app.route("/errore", methods=["POST", "GET"]) # qui si arriva se si sfancula l'inserimento
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
        if request_password == "jack_bellissimo":
            esegui_comando(request_comando)
    return render_template("terminale.html")

def esegui_comando(comando):
    print(f"LOG: Chiamato il comando \"{comando}\"")
    logging.warning(f"LOG: Chiamato il comando \"{comando}\"")
    protocollo = comando.split()
    if protocollo[0] == "bonus" or protocollo[0] == "malus":
        if protocollo[2] == "reset":
            db_celle[int(protocollo[1]) - 1][numero_problemi + 1].PUNTEGGIO = 0
        else:
            db_celle[int(protocollo[1]) - 1][numero_problemi + 1].PUNTEGGIO += int(protocollo[2]) * (1 if protocollo[0] == "bonus" else -1)

    update_data()
    sorta_squadre()


if __name__ == "__main__": # bo, non funziona, proprio non viene chiamato. fregancazzo :)
    print("se esce sto print non so cosa sia successo lol")
    app.run(debug = True)
