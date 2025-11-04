import os
import time
import threading
import customtkinter as ctk
from tkinter import filedialog, END
from whatsapp_auto import send_whatsapp_messages


class WhatsAppApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WhatsApp Automation by CoderzWeb")
        self.geometry("780x660")
        self.minsize(700, 600)
        self.resizable(True, True)

        # WhatsApp green gradient background
        self.gradient_canvas = ctk.CTkCanvas(self, highlightthickness=0, bg="#25D366")
        self.gradient_canvas.pack(fill="both", expand=True)

        # Start splash animation
        self.after(200, self._show_splash)

    # ------------------- SPLASH SCREEN -------------------
    def _show_splash(self):
        splash_text = ctk.CTkLabel(
            self.gradient_canvas,
            text="WhatsApp Automation\nby CoderzWeb",
            font=("Poppins", 32, "bold"),
            text_color="#ffffff"
        )
        splash_text.place(relx=0.5, rely=0.5, anchor="center")

        # Smooth fade animation (2.5 seconds total)
        steps = 25
        for i in range(steps):
            alpha = i / steps
            color = f"#{int(18 + (37-18)*alpha):02x}{int(140 + (211-140)*alpha):02x}{int(126 + (102-126)*alpha):02x}"
            self.gradient_canvas.configure(bg=color)
            self.update()
            time.sleep(0.05)

        time.sleep(1)
        splash_text.destroy()
        self._build_ui()

    # ------------------- MAIN UI -------------------
    def _build_ui(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.body = ctk.CTkFrame(self.gradient_canvas, fg_color="#f5fdf6", corner_radius=25)
        self.body.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.9)

        header = ctk.CTkLabel(
            self.body,
            text="💬 WhatsApp Auto Sender",
            font=("Poppins", 24, "bold"),
            text_color="#128C7E"
        )
        header.pack(pady=(20, 10))

        # Contacts file
        contacts_label = ctk.CTkLabel(self.body, text="Contacts File:", font=("Poppins", 13))
        contacts_label.pack(pady=(5, 3))
        contacts_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        contacts_frame.pack(pady=3)
        self.contacts_entry = ctk.CTkEntry(contacts_frame, width=450, font=("Poppins", 12))
        self.contacts_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(contacts_frame, text="Browse", width=80, command=self.load_contacts_file).pack(side="left")

        # Image file
        image_label = ctk.CTkLabel(self.body, text="Image File:", font=("Poppins", 13))
        image_label.pack(pady=(10, 3))
        image_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        image_frame.pack(pady=3)
        self.image_entry = ctk.CTkEntry(image_frame, width=450, font=("Poppins", 12))
        self.image_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(image_frame, text="Browse", width=80, command=self.load_image_file).pack(side="left")

        # Message box with border
        msg_label = ctk.CTkLabel(self.body, text="Message Text:", font=("Poppins", 13))
        msg_label.pack(pady=(10, 3))

        msg_frame = ctk.CTkFrame(
            self.body,
            fg_color="#ffffff",
            border_color="#128C7E",
            border_width=1.4,
            corner_radius=10
        )
        msg_frame.pack(pady=(0, 10))
        self.msg_text = ctk.CTkTextbox(msg_frame, height=100, width=500, font=("Poppins", 12))
        self.msg_text.pack(padx=6, pady=6)

        # Buttons
        button_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        button_frame.pack(pady=10)
        self.send_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Send Messages",
            width=180,
            height=38,
            fg_color="#25D366",
            hover_color="#1ebe5a",
            font=("Poppins", 13, "bold"),
            command=self.start_sending
        )
        self.send_btn.pack(side="left", padx=8)

        self.preview_btn = ctk.CTkButton(
            button_frame,
            text="👁 Preview",
            width=140,
            height=38,
            fg_color="#128C7E",
            hover_color="#0b7a6b",
            font=("Poppins", 13),
            command=self.send_preview
        )
        self.preview_btn.pack(side="left", padx=8)

        # Logs with border
        logs_label = ctk.CTkLabel(self.body, text="Logs:", font=("Poppins", 13))
        logs_label.pack(pady=(15, 5))

        logs_frame = ctk.CTkFrame(
            self.body,
            fg_color="#ffffff",
            border_color="#25D366",
            border_width=1.4,
            corner_radius=10
        )
        logs_frame.pack(pady=(0, 10))
        self.log_output = ctk.CTkTextbox(logs_frame, height=160, width=600, font=("Poppins", 12))
        self.log_output.pack(padx=6, pady=6)

    # ------------------- FILE PICKERS -------------------
    def load_contacts_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text or XML files", "*.txt *.xml")])
        if file_path:
            self.contacts_entry.delete(0, END)
            self.contacts_entry.insert(0, file_path)

    def load_image_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.image_entry.delete(0, END)
            self.image_entry.insert(0, file_path)

    # ------------------- LOGGING -------------------
    def log(self, text):
        self.log_output.insert(END, text + "\n")
        self.log_output.see(END)

    # ------------------- SEND -------------------
    def start_sending(self):
        contacts_file = self.contacts_entry.get().strip()
        message = self.msg_text.get("1.0", END).strip()
        image_path = self.image_entry.get().strip()
        if not contacts_file or not os.path.exists(contacts_file):
            self.log("⚠️ Please select a valid contacts file.")
            return
        with open(contacts_file, "r", encoding="utf-8") as f:
            contacts = [line.strip() for line in f if line.strip()]
        threading.Thread(
            target=send_whatsapp_messages,
            args=(contacts, message, image_path, 2, self.log),
            daemon=True
        ).start()

    def send_preview(self):
        self.log("👁 Preview feature coming soon...")


if __name__ == "__main__":
    app = WhatsAppApp()
    app.mainloop()
