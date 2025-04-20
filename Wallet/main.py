from GUI.GUI import WalletGUI
import tkinter as tk
import customtkinter as ctk
import os

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    #ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    appdata = os.environ['APPDATA']
    folder = os.path.join(appdata, 'JAC_Wallet')
    os.makedirs(folder, exist_ok=True)
    app = WalletGUI(root=root,data_path=folder)
    root.mainloop()