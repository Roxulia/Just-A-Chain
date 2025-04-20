import tkinter as tk
from tkinter import messagebox
import requests,os,signal,json,socket
import threading,uuid
from server.flask_server import BlockchainServer
class NodeGUI:
    def __init__(self,root,blockchain):
        self.blockchain = blockchain
        self.data_path = self.blockchain.data_path
        self.id = self.load_id() or f'{uuid.uuid4()}'
        self.mine = 0
        self.host = self.get_ip()
        self.port = 5051
        self.blockchain.host = self.host
        self.blockchain.port = self.port
        self.root = root
        self.root.title("JAC Node")
        root.protocol("WM_DELETE_WINDOW", self.onclose)
        self.stop_event = threading.Event()
        self.frame = tk.Frame(self.root)
        self.frame.pack()

        self.start_page()
    
    def load_id(self):
        file_path = os.path.join(self.data_path, 'id.json')
        try:
            with open(file_path, 'r') as file:
                id = json.load(file)
                return id
        except FileNotFoundError:
            return None

    def save_id(self):
        file_path = os.path.join(self.data_path, 'id.json')
        with open(file_path, 'w') as file:
            json.dump(self.id, file)

    def start_page(self):
        self.clear_frame()

        connect_button = tk.Button(self.frame, text="Connect to Network", command=self.show_loading_screen)
        connect_button.pack(pady=20)

    def show_loading_screen(self):
        # Clear the current page
        self.clear_frame()

        # Loading Label
        self.loading_label = tk.Label(self.frame, text="Connecting to Seed Node...")
        self.loading_label.pack(pady=20)
        self.animate_loading_text()
        # Start initializing the camera on a separate thread so UI doesn't freeze
        threading.Thread(target=self.start_connection).start()

    def animate_loading_text(self):
        # Sequence of texts to simulate animation
        loading_texts = ["Connecting", "Connecting.", "Connecting..", "Connecting..."]

        # Get the current text in the label
        current_text = self.loading_label.cget("text")

        # Find the next text in the sequence
        if current_text in loading_texts:
            next_index = (loading_texts.index(current_text) + 1) % len(loading_texts)
        else:
            next_index = 0

        # Update the label with the next text
        self.loading_label.config(text=loading_texts[next_index])

        # Repeat the animation every 500 milliseconds (0.5 seconds)
        self.loading_animation = self.frame.after(500, self.animate_loading_text)

    def start_connection(self):
        if self.stop_event.is_set():
            return
        try:
            data = {'node' : [f'http://{self.host}:{self.port}'],'node_id':self.id}
            #print(data)
            #response = requests.get(f'https://{self.blockchain.seed_node}/seed_node.php?action=check_node')
            response = requests.get(f'https://{self.blockchain.seed_node}/seed_node.php?action=get_all_nodes')
            if(response.status_code==200):
                response = response.json()['links']
                data = {'node' : [f'http://{self.host}:{self.port}']}
                for i in response:
                    if(i!=""):
                        self.blockchain.register_node(f'{i}')
                    
                for node in self.blockchain.nodes :
                    try:
                        if(node != "" and node != f'{self.host}:{self.port}'):
                            res = requests.post(f'http://{node}/nodes/register',json=data)
                            print(res.json())
                    except requests.ConnectionError:
                        print(f'Cant Connect with {node}')
            self.frame.after_cancel(self.loading_animation)
            self.frame.after(0, self.second_page)
        except requests.ConnectionError:
            messagebox.showerror("Error","Can't Connect to Seed Node")
            self.frame.after_cancel(self.loading_animation)
            self.frame.after(0, self.start_page)
        
    
    def second_page(self):
        self.clear_frame()

        start_server_button = tk.Button(self.frame, text="Start Server", command=self.start_server)
        start_server_button.pack(pady=20)

    def start_server(self):
        threading.Thread(target=self.run).start()
        data = {'node' : [f'http://{self.host}:{self.port}'],'node_id':self.id}
        try:
            response = requests.post(f'https://{self.blockchain.seed_node}/seed_node.php?action=register_node',data=data)
            if(response.status_code == 200):
                self.dashboard()
        except requests.ConnectionError:
            messagebox.showerror("Error","Can't Connect to Seed Node")
        

    def run(self):
        self.a = BlockchainServer(self.blockchain,self.host,self.port)
        self.a.run()
        
        messagebox.showinfo("Server", "Server started and accepting requests.")

    def dashboard(self):
        self.clear_frame()

        # Example dashboard widgets
        block_info_label = tk.Label(self.frame, text="Blockchain Information", font=("Arial", 16))
        block_info_label.pack(pady=10)
        
        # You would add widgets here to display real-time blockchain data
        self.block_data_text = tk.Text(self.frame, height=10, width=50)
        self.block_data_text.pack(pady=10)
        self.showchain = tk.Button(self.frame,text="Show Chain",command=self.request_data)
        self.showchain.pack(padx=20,pady=10)
        self.getnode = tk.Button(self.frame,text="get nodes",command=self.get_nodes)
        self.getnode.pack(padx=20,pady=10)
        self.btnmine = tk.Button(self.frame,text="mining : On",command=self.activate_mining)
        self.btnmine.pack(padx=20,pady=10)
        # Example button to refresh data (you'd implement the actual logic)
    
    def get_nodes(self):
        if self.block_data_text.get(1.0,tk.END) != "\n":
            self.block_data_text.delete(1.0,tk.END)
            #print(self.block_data_text.get(1.0,tk.END))
        self.block_data_text.insert(tk.END,self.blockchain.nodes)

    def request_data(self):
        res = requests.get(f'http://{self.host}:{self.port}/nodes/resolve')
        res = res.json()['message']
        res = json.dumps(res,indent=4)
        if self.block_data_text.get(1.0,tk.END) != "\n":
            self.block_data_text.delete(1.0,tk.END)
            #print(self.block_data_text.get(1.0,tk.END))
        self.block_data_text.insert(tk.END,res)

    def activate_mining(self):
        if(self.mine == 0):
            self.blockchain.automineOnOff(1)
            self.mine = 1
            self.btnmine.config(text="Mining : Off")
        else:
            self.blockchain.automineOnOff(0)
            self.mine = 0
            self.btnmine.config(text="Mining : On")

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def onclose(self):
        self.save_id()
        os.kill(os.getpid(), signal.SIGTERM)
        print("Closing app")
        
        self.root.destroy()

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to an external server (does not actually send any data)
            s.connect(('8.8.8.8', 80))
            ip_address = s.getsockname()[0]
        finally:
            s.close()
            return ip_address
