import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import requests,json,threading
from Backend.wallet import Wallet
import os
class WalletGUI:
    def __init__(self,root,data_path):
        self.data_path = data_path
        self.wallets = []
        self.seednode = ""
        self.nodes = set()
        self.pin = ""
        self.claimed = False
        self.active_index = 0
        self.active_page = "start_page"
        self.prev = ""
        self.receive = ""
        self.amount = 0
        self.trx_result = ""
        self.root=root
        self.root.title("JAC Wallet")
        self.root.geometry("600x400")
        root.protocol("WM_DELETE_WINDOW", self.onclose)
        self.load_wallets()
        self.load_nodes()
        self.load_meta()
        self.stop_event = threading.Event()
        threading.Thread(target=self.load_nodes_from_network).start()
        self.frame = ctk.CTkFrame(self.root,width = 600,height=400,fg_color="#675598")
        self.frame.pack_propagate(0) 
        self.frame.pack()
        if not self.wallets : 
            self.start_page()
        elif self.pin == "":
            self.pin_page()
        else:
            self.enter_pin_page()

    def start_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 
        self.active_page = "start_page"
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        create_button = ctk.CTkButton(main_frame, text="Create Wallet",fg_color="#673298", command=self.generate_wallet)
        create_button.pack(padx=10,pady=20)

        import_button = ctk.CTkButton(main_frame, text="Import Wallet",fg_color="#673298", command=self.import_wallet_page)
        import_button.pack(padx=10,pady=20)

        if self.prev == "home_page":
            cancel = ctk.CTkButton(main_frame, text="Cancel",fg_color="#673298", command=self.home_page)
            cancel.pack(padx=10,pady=10)

    def create_wallet_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 
        self.active_page = "create_wallet_page"
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        wallet_list = self.wallets
        lblKeyphrase = ctk.CTkTextbox(main_frame, width=300, height=100, font=("Arial", 12))
        lblKeyphrase.insert(tk.END, wallet_list[-1].key_phrase)
        lblKeyphrase.pack(padx=10,pady=20)
        lblKeyphrase.configure(state='disabled')

        continue_button = ctk.CTkButton(main_frame, text="Start Using Wallet",fg_color="#673298", command=self.home_page if self.pin else self.pin_page)
        continue_button.pack(padx=10,pady=10)

        cancel_button = ctk.CTkButton(main_frame, text="Cancel",fg_color="#673298", command=self.cancel_wallet_creation)
        cancel_button.pack(padx=10,pady=10)

    def pin_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 
        self.active_page = "pin_page"
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        lblPin = ctk.CTkLabel(main_frame,text_color="#FFF", text="Enter PIN:")
        lblPin.pack(padx=10,)

        self.pinBox = ctk.CTkEntry(main_frame, show="*")
        self.pinBox.pack(padx=10,)

        lblConfirm = ctk.CTkLabel(main_frame,text_color="#FFF", text="Re-enter PIN:")
        lblConfirm.pack(padx=10,)

        self.pinConfirm = ctk.CTkEntry(main_frame, show="*")
        self.pinConfirm.pack(padx=10,)

        continue_button = ctk.CTkButton(main_frame, text="Confirm PIN",fg_color="#673298", command=self.set_pin)
        continue_button.pack(padx=10,pady=10)

    def enter_pin_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 

        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        lblPin = ctk.CTkLabel(main_frame, text="Enter PIN:",text_color="#FFFFFF")
        lblPin.pack(padx=10,pady=(10,0))

        self.pinBox = ctk.CTkEntry(main_frame, show="*")
        self.pinBox.pack(padx=10,pady=10)

        continue_button = ctk.CTkButton(main_frame, text="Confirm PIN",fg_color="#673298", command=self.check_pin)
        continue_button.pack(padx=10,pady=10)

    def import_wallet_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.import_key = ctk.CTkEntry(main_frame, width=300)
        self.import_key.pack(padx=10,)

        confirmButton = ctk.CTkButton(main_frame, text="Confirm",fg_color="#673298", command=self.import_wallet)
        confirmButton.pack(padx=10,pady=10)

        cancelButton = ctk.CTkButton(main_frame, text="Cancel",fg_color="#673298", command=self.start_page)
        cancelButton.pack(padx=10,pady=10)

    def home_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 
        self.active_page = "home_page"
        
        # Main Frame
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Address and Balance Frame
        info_frame = ctk.CTkFrame(main_frame,fg_color="#984499")
        info_frame.grid(row=0,column =0,pady=(20, 10),sticky='nsew',padx=5)

        lblAddress = ctk.CTkLabel(info_frame,text_color="#FFF", text="Wallet Address:", font=("Arial", 14))
        lblAddress.grid(row=0, column=0, sticky="w", padx=(10, 5))

        address_text = ctk.CTkTextbox(info_frame, width=250, height=40, font=("Arial", 12))
        address_text.insert(tk.END, self.wallets[self.active_index].address)
        address_text.grid(row=1, column=0, pady=(5, 10), padx=(10, 5))
        address_text.configure(state = 'disabled')

        lblBalance = ctk.CTkLabel(info_frame,text_color="#FFF", text="Balance:", font=("Arial", 14))
        lblBalance.grid(row=2, column=0, sticky="w", padx=(10, 5))

        self.balance = ctk.CTkLabel(info_frame,text_color="#FFF", text=self.wallets[self.active_index].balance, font=("Arial", 12))
        self.balance.grid(row=3, column=0, pady=(5, 10), padx=(10, 5))

        # Actions Frame
        actions_frame = ctk.CTkFrame(main_frame,fg_color="#984499")
        actions_frame.grid(row = 1,column = 0,columnspan=2,pady=(10, 20),sticky='nsew',padx=5)

        if not self.claimed:
            self.claim_button = ctk.CTkButton(actions_frame, text="Claim Reward",fg_color="#673298", command=self.claim_reward_press)
            self.claim_button.pack(padx=3,pady=7,expand=True,fill='both')

        self.refresh_button = ctk.CTkButton(actions_frame, text="Refresh Balance",fg_color="#673298", command=self.balance_check_press)
        self.refresh_button.pack(padx=3,pady=7,expand=True,fill='both')

        send_button = ctk.CTkButton(actions_frame, text="Send Coin",fg_color="#673298", command=self.send_page)
        send_button.pack(padx=3,pady=7,expand=True,fill='both')

        # Wallet Selection Frame
        wallet_frame = ctk.CTkFrame(main_frame,fg_color="#984499")
        wallet_frame.grid(row = 0,rowspan = 2,column = 1,pady=(20, 10),sticky='n',padx=5)

        wallet_buttons_frame = ctk.CTkFrame(wallet_frame,fg_color="#984499")
        wallet_buttons_frame.pack(pady=5)

        for i, wallet in enumerate(self.wallets):
            button = ctk.CTkButton(wallet_buttons_frame, text=f'Wallet {i}',fg_color="#673298", command=lambda i=i: self.set_active(index=i))
            button.grid(row = i,column=0,pady=2,padx=2)
            del_button = ctk.CTkButton(wallet_buttons_frame, text=f'Delete',fg_color="#DD0000", command=lambda i=i: self.delete_wallet(index=i))
            del_button.grid(row=i,column=1,pady=2,padx=2)
            if i == self.active_index:
                button.configure(state="disabled")
                del_button.configure(state="disabled")

        self.addWalletButton = ctk.CTkButton(wallet_frame, text="+ Add Wallet",fg_color="#673298", command=self.add_wallet)
        self.addWalletButton.pack(anchor='s', pady=10, padx=10,fill='both')
        
    def send_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 
        self.active_page = "send_page"
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        lblReceive = ctk.CTkLabel(main_frame,text_color="#FFF", text="Receiver Address:")
        lblReceive.pack(padx=10,)

        self.receiverAddress = ctk.CTkEntry(main_frame, width=300)
        self.receiverAddress.pack(padx=10,)

        lblAmount = ctk.CTkLabel(main_frame,text_color="#FFF", text="Amount:")
        lblAmount.pack(padx=10,)

        self.amountEntry = ctk.CTkEntry(main_frame, width=300)
        self.amountEntry.pack(padx=10,)

        sendButton = ctk.CTkButton(main_frame, text="Send",fg_color="#673298", command=self.send)
        sendButton.pack(padx=10,pady=10)

        cancelButton = ctk.CTkButton(main_frame, text="Cancel",fg_color="#673298", command=self.home_page)
        cancelButton.pack(padx=10,pady=10)

    def result_page(self):
        self.clear_frame()
        self.frame.pack_propagate(0) 

        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        txtResult = ctk.CTkTextbox(main_frame, height=100, width=300)
        txtResult.insert("0.0", self.trx_result)
        txtResult.pack(padx=10,pady=20)

        btnOK = ctk.CTkButton(main_frame, text="OK",fg_color="#673298", command=self.home_page)
        btnOK.pack(padx=10,pady=10)

    
    def add_wallet(self):
        self.prev = "home_page"
        self.start_page()

    def import_wallet(self):
        key = self.import_key.get()
        w = Wallet(mnemonic_phrase=key)
        if w not in self.wallets:
            self.wallets.append(w)
        self.home_page()

    def delete_wallet(self,index):
        self.wallets.remove(self.wallets[index])
        self.home_page()

    def cancel_wallet_creation(self):
        w = self.wallets[-1]
        self.wallets.remove(w)
        self.start_page()

    def set_pin(self):
        pin = self.pinBox.get()
        confirm_pin = self.pinConfirm.get()
        if pin == "" or confirm_pin =="":
            messagebox.showerror('Requirement not fulfill','Please Fill both info')
        else:
            if pin == confirm_pin:
                self.pin = pin
                self.save_meta()
                self.home_page()
            else :
                messagebox.showerror("Error","Pin and Confirm Pin must be same")
        #self.pin_page()

    def check_pin(self):
        pin = self.pinBox.get()
        #print(f'{pin}:{self.pin}')
        if self.pin == pin:
            self.next_page()
        else:
            messagebox.showerror("Error","Incorrect PIN")
            self.pinBox.delete(0, tk.END) 
    
    def next_page(self):
        if self.active_page == "start_page":
            self.home_page()
        elif self.active_page == "send_page":
            threading.Thread(target=self.start_trx).start()
            self.show_loading_screen()

    def start_trx(self):
        if self.stop_event.is_set():
            return
        wallet_list = self.wallets
        nodes = list(self.nodes)
        self.trx_result = wallet_list[self.active_index].send_transaction(self.receive, self.amount, nodes)
        self.frame.after_cancel(self.loading_animation)
        self.frame.after(10,self.result_page)

    def show_loading_screen(self):
        # Clear the current page
        self.clear_frame()
        self.frame.pack_propagate(0) 
        main_frame = ctk.CTkFrame(self.frame,fg_color="#A855B9")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        # Loading Label
        self.loading_label = ctk.CTkLabel(main_frame,text_color="#FFF", text="Connecting to Nodes...")
        self.loading_label.pack(padx=10,pady=20)
        self.animate_loading_text()
        # Start initializing the camera on a separate thread so UI doesn't freeze
       

    def animate_loading_text(self):
        # Sequence of texts to simulate animation
        loading_texts = ["Loading", "Loading.", "Loading..", "Loading..."]

        # Get the current text in the label
        current_text = self.loading_label.cget("text")

        # Find the next text in the sequence
        if current_text in loading_texts:
            next_index = (loading_texts.index(current_text) + 1) % len(loading_texts)
        else:
            next_index = 0

        # Update the label with the next text
        self.loading_label.configure(text=loading_texts[next_index])

        # Repeat the animation every 500 milliseconds (0.5 seconds)
        self.loading_animation = self.frame.after(500, self.animate_loading_text)

    def set_active(self,index):
        self.active_index = index
        threading.Thread(target=self.balance_check).start()
        #print(f"{self.active_index} : {index}")
        self.home_page()

    def generate_wallet(self):
        w = Wallet()
        if w not in self.wallets:
            self.wallets.append(w)
            self.save_wallets()
            self.create_wallet_page()
        else:
            self.home_page()

    def send(self):
        self.receive = self.receiverAddress.get()
        a = self.amountEntry.get()
        if self.receive == "" or not a.isdigit():
            messagebox.showerror("Error","Check Ur input.There is something wrong")
        else:
            self.amount = int(a)
            self.enter_pin_page()

    def balance_check_press(self):
        threading.Thread(target=self.balance_check).start()
        self.show_loading_screen()

    def balance_check(self):
        wallet_list = self.wallets
        nodes = list(self.nodes)
        balance = wallet_list[self.active_index].request_balance(nodes)
        if self.active_page == "home_page":
            if not balance:
                #self.balance.configure(text=wallet_list[self.active_index].balance)
                messagebox.showerror("Error","Connection Error!!")
            self.frame.after_cancel(self.loading_animation)
            self.frame.after(10,self.home_page)

    def claim_reward_press(self):
        threading.Thread(target=self.claim_reward).start()
        self.show_loading_screen()

    def claim_reward(self):
        wallet_list = self.wallets
        trx = {'recipient':wallet_list[self.active_index].address}
        nodes = list(self.nodes)
        done = False
        for node in nodes:
            try:
                response = requests.post(f'{node}/reward',json=trx)
                if(response.status_code == 201):
                    response = response.json()['message']
                    #messagebox.showinfo('Response',message=json.dumps(response))
                    print(response)
                    self.claimed = True
                    #self.claim_button.configure(state='disabled')
                    done = True
                    break
            except requests.ConnectionError:
                #messagebox.showerror('Error',message=f'Cant connect to : {node}')
                #print(f'cant connect to {node}')
                continue
        if not done:
            messagebox.showerror("Error","Connection Error!!")
        self.frame.after_cancel(self.loading_animation)
        self.frame.after(10,self.home_page)
        self.save_meta()
        
    def check_connectivity(self):
        pass
    
    def load_wallets(self):
        file_path = os.path.join(self.data_path, 'wallets.json')
        try:
            with open(file_path, 'r') as file:
                phrases = json.load(file)
                list,index = [],0
                for p in phrases:
                    if p['index'] == index:
                        list.append(Wallet(mnemonic_phrase=p['wallet']['mnemonic'],balance=p['wallet']['balance']))
                        index = index+1
                self.wallets = list
        except FileNotFoundError:
            print("file not found")

    def load_nodes(self):
        file_path = os.path.join(self.data_path, 'nodes.json')
        try:
            with open(file_path, 'r') as file:
                nodes = json.load(file)
                for n in nodes:
                    self.nodes.add(n)
        except FileNotFoundError:
            print("File not found")
        
        
    def load_nodes_from_network(self):
        try:
            response = requests.get(f'http://{self.seednode}/seed_node.php?action=get_all_nodes')
            if(response.status_code == 200):
                response = response.json()['links']
                for i in response:
                    if i != "":
                        self.nodes.add(i)
        except requests.ConnectionError:
            print(f'cant connect with : {self.seednode}')
        self.save_nodes()

    def load_meta(self):
        file_path = os.path.join(self.data_path, 'meta.json')
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.pin = data['pin']
                self.claimed = data['claimed']
        except FileNotFoundError:
            return "File couldn't find!! Creating..."
    
    def save_wallets(self):
        file_path = os.path.join(self.data_path, 'wallets.json')
        data = []
        i = 0
        for wallet in self.wallets:
            d = {'index' : i,'wallet':wallet.toJSON()}
            data.append(d)
            i=i+1
        with open(file_path, 'w') as file:
            json.dump(data,file,indent=4)

    def save_nodes(self):
        file_path = os.path.join(self.data_path, 'nodes.json')
        with open(file_path, 'w') as file:
            json.dump(list(self.nodes), file)

    def save_meta(self):
        file_path = os.path.join(self.data_path, 'meta.json')
        with open(file_path,'w') as file:
            json.dump({'pin':self.pin,'claimed' : self.claimed},file)

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
    
    def onclose(self):
        self.save_nodes()
        self.save_wallets()
        self.save_meta()
        self.root.destroy()
