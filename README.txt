J^4
DISCLAIMER:
Questo programma è nato per diletto prima che per utilità, è possibile che contenga piccoli bug.
Per avere la sicurezza che il programma funzioni correttamente, bisogna che almeno un client abbia la pagina della classifica aperta

Istruzioni per l'uso:
Modificare il file json inserendo tutte le informazioni e assicurandosi che sia nella stessa directory di app.py
E' possibile avere delle squadre ospite aggiungendo la stringa "(ospite)" senza virgolette al nome della squadra nel momento del setup. Le squadre ospite DEVONO essere le ultime ad essere inserite nel setup, e compariranno dietro all'ultima squadra non ospite.
Per runnare bisogna, al momento di inizio gara, eseguire sul terminale il comando "python -m flask run" (dalla stessa directory di app.py). Prima di farlo, però, bisogna avere installato python, avere installato flask ("pip install flask") e aver eseguito (nella stessa directory di app.py) i comandi "set FLASK_APP=app" e "set FLASK_ENV=development".

Se volete mostrare più squadre o problemi, potete manipolare rispettivamente "padding" e "width" di table__cell dentro style.css

Mentre la gara si svolge, vengono scritti su un file di log (nella cartella logs) tutti gli eventi divisi in tre categorie: INFO per le informazioni di tipo tecnico, WARNING per gli eventi importanti e ERROR per eventuali problemi.
Inoltre, a fine gara viene salvata nella cartella archivio_gare la classifica finale. Il file styles.css che si trova in questa cartella serve affinché il file html sia visualizzato correttamente.

Se si sta facendo un allenamento a squadre si può cambiare a True il valore del bool MODALITA_ALLENAMENTO (in cima allo script) per disattivare il sorting e i punteggi. Per far funzionare correttamente questa modalità consiglio di settare n=0, fine_incremento=0, incremento_errore=0, bonus_risposte=[0], bonus_full=[0], tempo_jolly=0. I nomi delle squadre sono i nomi dei membri della squadra che si sta allenando.
In modalità allenamento, il capitano (che deve avere il codice 01) può impostare il jolly normalmente dalla pagina di inserimento e il jolly verrà impostato a tutti i membri della squadra. Per impostare il jolly non ci sono limiti di tempo
Se si è in modalità allenamento, il file json che verrà cercato non sarà gara.json, bensì il nome di file specificato.
