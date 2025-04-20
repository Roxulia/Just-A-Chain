import tkinter as tk
from GUI.GUI import NodeGUI
from blockchain.transaction import Transaction
from blockchain.blockchain import Blockchain
from server.flask_server import BlockchainServer
import os
if __name__ == "__main__":
    root = tk.Tk()
    appdata = os.environ['APPDATA']
    folder = os.path.join(appdata, 'JAC_Node')
    os.makedirs(folder, exist_ok=True)
    a = Blockchain(data_path=folder)
    app = NodeGUI(root,a)
    root.mainloop()