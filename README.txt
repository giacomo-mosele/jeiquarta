J^4
DISCLAIMER:
Quest'app l'ho fatta sia per divertimento sia per utilità, non è niente di che. Se trovate un bug serio ditemelo e cercherò di fixarlo
La grafica non vi piace? Ve la fate andare bene
Il programma è lento, poco ottimizzato e fa diventare il vostro computer un motore di aereo? Ve lo fate andare bene
Perché il programma funzioni correttamente, bisogna che almeno un client abbia la pagina della classifica aperta, altrimenti non funzionano gli incrementi (potevo trovare una soluzione più intelligente ma troppi sbatti)
Se crasha/si chiude il server durante lo svolgimento della gara, vi attaccate. Non ho ancora implementato un sistema di backup quindi state attenti

Istruzioni per l'uso:
Aprire SetupGareMate.exe e inserire tutte le informazioni. Verrà creato un file .json che va messo nella stessa directory di app.py
Attenzione: il programma python da per scontato che il file si chiami gara.json, ma volendo si può modificare
Per runnare bisogna, al momento di inizio gara, eseguire sul terminale il comando "python -m flask run" (dalla stessa directory di app.py). Prima di farlo, però, bisogna avere installato python, avere installato flask ("pip install flask") e aver eseguito (nella stessa directory di app.py) i comandi "set FLASK_APP=app" e "set FLASK_ENV=development". Su quest'ultimo non sono sicurissimo che sia la cosa migliore, ma sono sicuro che funziona quindi ve lo fate andare bene :)

Se volete mostrare più squadre o problemi, potete manipolare rispettivamente "padding" e "width" di table__cell dentro style.css