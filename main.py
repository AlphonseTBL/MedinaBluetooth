import customtkinter as ctk
def centrar_ventana(ventana, ancho, alto):
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    x = (pantalla_ancho // 2) - (ancho // 2)
    y = (pantalla_alto // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

app = ctk.CTk()
app.title("Registro de datos bluetooth")
app.geometry("600x900")
centrar_ventana(app, 600, 500)

lbl_titulo = ctk.CTkLabel(
    app, 
    text="Datos de audifonos bluetooth", 
    font=("Arial", 22, "bold")
)
lbl_audifIzq = ctk.CTkLabel(
    app,
    text = "audifono izquierdo",
    font = ("Arial", 18, "bold")
)
lbl_audifDer = ctk.CTkLabel(
    app,
    text = "audifono derecho",
    font = ("Arial", 18, "bold")
)
lbl_resultadoaudfizq = ctk.CTkLabel(
    app,
    text = "resultado audifono izquierdo",
    font = ("Arial", 18, "bold")
)
lbl_resultadoaudder = ctk.CTkLabel(
    app,
    text = "resultado audifono derecho",
    font = ("Arial", 18, "bold")
)


lbl_titulo.pack(pady=10)
frame_audifonos = ctk.CTkFrame(app, fg_color="transparent")
frame_audifonos.pack(fill="x", padx=10) 
frame_resultados = ctk.CTkFrame(app, fg_color="transparent")
frame_resultados.pack(fill="x", padx=10, pady=10)


lbl_audifIzq = ctk.CTkLabel(frame_audifonos, text="audifono izquierdo", font=("Arial", 18, "bold"))
lbl_audifIzq.pack(side="left") 

lbl_audifDer = ctk.CTkLabel(frame_audifonos, text="audifono derecho", font=("Arial", 18, "bold"))
lbl_audifDer.pack(side="right") 

lbl_resultadoaudfizq = ctk.CTkLabel(frame_resultados, text="resultado audifono izquierdo", font=("Arial", 18, "bold"))
lbl_resultadoaudfizq.pack(side="left")

lbl_resultadoaudder = ctk.CTkLabel(frame_resultados, text="resultado audifono derecho", font=("Arial", 18, "bold"))
lbl_resultadoaudder.pack(side="right")
app.mainloop()