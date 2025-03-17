import tkinter as tk
import requests

SQUADRE = 8
PROBLEMI = 21

FONT = ("Arial", 11)

online = True
local = True
online_url = "https://jeiquarta.pythonanywhere.com/inserimento"
local_url = "http://localhost:5000/inserimento"

password = "dsa321"

def request_manager(sq, prob, res):
    if online:
        requests.post(online_url, data = {"password": password, "codice_squadra": str(sq), "numero_problema": str(prob), "risultato": str(res)})
    if local:
        requests.post(local_url, data = {"password": password, "codice_squadra": str(sq), "numero_problema": str(prob), "risultato": str(res)})


def open_ins_win(sq, prob):
    def send(event):
        request_manager(sq, prob, entry.get())
        ins_win.destroy()

    def send_jolly():
        request_manager(sq, prob, -1)
        ins_win.destroy()

    shown = False
    def jolly_clicked():
        nonlocal conf_jolly
        nonlocal shown

        if shown:
            conf_jolly.place_forget()
            shown = False
        else:
            conf_jolly.place(x = 260, y = 170)
            shown = True

    ins_win = tk.Toplevel()
    ins_win.geometry(f"400x250")
    ins_win.title(f"J^4 | Squadra {sq:02} problema {prob}")
    ins_win.resizable(False, False)

    tk.Label(ins_win, text = f"Squadra {sq:02}", font = ("Arial", 18)).pack(pady = 10)
    tk.Label(ins_win, text = f"Problema {prob}", font = ("Arial", 18)).pack()

    entry = tk.Entry(ins_win, font = ("Arial", 26), width = 5, justify = "center")
    entry.bind("<Return>", send)
    entry.focus_set()
    entry.pack(pady = 20)

    tk.Button(ins_win, text = "Jolly", font = ("Arial", 14), command = jolly_clicked).pack()

    conf_jolly = tk.Button(ins_win, text = "Conferma", font = ("Arial", 14), command = send_jolly)


root = tk.Tk()

#width = 100 * (PROBLEMI + 1)
#height = 33 * (SQUADRE + 1)

#root.geometry(f"{width}x{height}")
root.state("zoomed")
root.title("J^4 | Inserimento")

frame = tk.Frame(root)
for i in range(PROBLEMI + 1):
    frame.columnconfigure(i, weight=1)
for j in range(SQUADRE + 1):
    frame.rowconfigure(i, weight=1)

for i in range(1, PROBLEMI + 1):
    lab = tk.Label(frame, text = f"P{i}", font = FONT)
    lab.grid(row = 0, column = i, sticky = "news")
for j in range(1, SQUADRE + 1):
    lab = tk.Label(frame, text = f"Sq. {j:02}", font = FONT)
    lab.grid(row = j, column = 0, sticky = "news")

for prob in range(1, PROBLEMI + 1):
    for sq in range(1, SQUADRE + 1):
        btn = tk.Button(frame, text = f'S{sq:02} - P{prob}', font = FONT, command = lambda sq=sq, prob=prob: open_ins_win(sq, prob)) # don't ask why.
        btn.grid(row = sq, column = prob, sticky = "news")

frame.pack(fill = "both")

root.mainloop()