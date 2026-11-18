"""Tkinter quick-message editor and sender."""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from templates import load_templates, make_template, render_message, save_templates


class QuickMessages:
    def __init__(self, root):
        self.root = root
        self.templates = load_templates()
        self.busy = False
        self.events = queue.Queue()
        self.recipient = tk.StringVar()
        self.sender = tk.StringVar()
        self.status = tk.StringVar(value="Bir mesaj seçin; gönderilecek metni kartın altında görebilirsiniz.")
        self.cards = []
        root.title("Remote WhatsApp • Hazır Mesajlar")
        root.geometry("820x720")
        root.minsize(640, 520)
        root.configure(bg="#eef5f1")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#eef5f1")
        style.configure("TLabel", background="#eef5f1", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"), foreground="#075e54")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
        style.configure("Send.TButton", background="#087f5b", foreground="white")
        style.map("Send.TButton", background=[("active", "#075e54"), ("disabled", "#9aa9a1")])

        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Hazır mesajların, tek tık uzağında.", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Kendi mesajlarını oluştur, kişiselleştir ve WhatsApp üzerinden gönder.").pack(anchor="w", pady=(4, 18))
        fields = ttk.Frame(frame)
        fields.pack(fill="x")
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        ttk.Label(fields, text="Alıcı · WhatsApp sohbetindeki tam ad").grid(row=0, column=0, sticky="w")
        ttk.Label(fields, text="Senin adın · {ad} alanı için").grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Entry(fields, textvariable=self.recipient).grid(row=1, column=0, sticky="ew", pady=6)
        ttk.Entry(fields, textvariable=self.sender).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=6)
        ttk.Label(frame, text="Gönder düğmesi mesajı doğrudan yollar. İlk kullanımda Chrome'daki QR kodunu okut.", wraplength=710).pack(anchor="w", pady=(4, 16))
        bar = ttk.Frame(frame)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Label(bar, text="MESAJ KOLEKSİYONUN").pack(side="left")
        self.add_button = ttk.Button(bar, text="+ Yeni mesaj", command=self.edit)
        self.add_button.pack(side="right")

        area = ttk.Frame(frame)
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, bg="#eef5f1", highlightthickness=0)
        scrollbar = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.list_frame = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.window, width=event.width))
        ttk.Label(frame, textvariable=self.status, wraplength=710).pack(anchor="w", pady=(14, 0))
        self.recipient.trace_add("write", self.update_previews)
        self.sender.trace_add("write", self.update_previews)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()
        root.after(100, self.poll)

    def refresh(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.cards = []
        self.action_buttons = [self.add_button]
        if not self.templates:
            ttk.Label(self.list_frame, text="Henüz mesaj yok. + Yeni mesaj ile ilk mesajını ekle.").pack(pady=24)
        for item in self.templates:
            card = tk.Frame(self.list_frame, bg="white", padx=16, pady=14)
            card.pack(fill="x", pady=(0, 10))
            tk.Label(card, text=item["title"], bg="white", fg="#153b30", font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w")
            preview = tk.Label(card, bg="white", fg="#405b50", justify="left", anchor="w", font=("Segoe UI", 10), wraplength=650)
            preview.pack(fill="x", pady=(8, 10))
            card.bind("<Configure>", lambda event, label=preview: label.configure(wraplength=max(150, event.width - 32)))
            self.cards.append((item, preview))
            actions = tk.Frame(card, bg="white")
            actions.pack(fill="x")
            for text, command, style in [
                ("Gönder ↗", lambda item=item: self.send(item), "Send.TButton"),
                ("Düzenle", lambda item=item: self.edit(item), "TButton"),
                ("Sil", lambda item=item: self.delete(item), "TButton"),
            ]:
                button = ttk.Button(actions, text=text, command=command, style=style)
                button.pack(side="left", padx=(0, 8))
                button.configure(state="disabled" if self.busy else "normal")
                self.action_buttons.append(button)
        self.update_previews()

    def update_previews(self, *_):
        for item, label in self.cards:
            try:
                text = render_message(item["text"], self.sender.get(), self.recipient.get())
            except ValueError:
                text = item["text"]
            label.configure(text=text)

    def persist(self, items):
        try:
            save_templates(items)
        except (OSError, ValueError) as error:
            messagebox.showerror("Kaydedilemedi", str(error), parent=self.root)
            return False
        self.templates = items
        self.refresh()
        return True

    def edit(self, item=None):
        if self.busy:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Mesajı düzenle" if item else "Yeni hazır mesaj")
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Düğme başlığı").pack(anchor="w")
        title = ttk.Entry(frame, width=52)
        title.pack(fill="x", pady=(6, 12))
        ttk.Label(frame, text="Mesaj · {ad}: senin adın, {alici}: alıcının adı").pack(anchor="w")
        body = tk.Text(frame, width=56, height=7, font=("Segoe UI", 11), wrap="word")
        body.pack(fill="both", expand=True, pady=6)
        if item:
            title.insert(0, item["title"])
            body.insert("1.0", item["text"])

        def save():
            try:
                updated = make_template(title.get(), body.get("1.0", "end-1c"), item["id"] if item else None)
            except ValueError as error:
                messagebox.showerror("Mesajı kontrol et", str(error), parent=dialog)
                return
            items = [updated if old["id"] == updated["id"] else old for old in self.templates] if item else [*self.templates, updated]
            if self.persist(items):
                dialog.destroy()

        ttk.Button(frame, text="Kaydet", command=save, style="Send.TButton").pack(anchor="e", pady=(10, 0))
        title.focus_set()

    def delete(self, item):
        if not self.busy and messagebox.askyesno("Mesajı sil", f'“{item["title"]}” silinsin mi?', parent=self.root):
            self.persist([old for old in self.templates if old["id"] != item["id"]])

    def send(self, item):
        if self.busy:
            return
        recipient = self.recipient.get().strip()
        try:
            text = render_message(item["text"], self.sender.get(), recipient)
        except ValueError as error:
            messagebox.showerror("Eksik bilgi", str(error), parent=self.root)
            return
        self.busy = True
        for button in self.action_buttons:
            button.configure(state="disabled")
        self.status.set(f"{recipient} için gönderiliyor… Açılan Chrome penceresinde gerekirse QR kodunu okut.")

        def work():
            try:
                from main import send_message
                send_message(recipient, text)
            except Exception as error:
                self.events.put((False, str(error)))
            else:
                self.events.put((True, f"Gönderme komutu uygulandı: {recipient}. WhatsApp'tan kontrol edebilirsin."))

        threading.Thread(target=work, daemon=False).start()

    def poll(self):
        try:
            success, text = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.refresh()
            self.status.set(text if success else "Gönderim tamamlanamadı. Alıcıyı, bağlantıyı ve Chrome oturumunu kontrol et.")
            if not success:
                messagebox.showerror("Gönderim hatası", text, parent=self.root)
        self.root.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo("Gönderim sürüyor", "İşlem bitince pencereyi kapatabilirsin.", parent=self.root)
        else:
            self.root.destroy()


def launch():
    root = tk.Tk()
    try:
        QuickMessages(root)
    except (OSError, ValueError) as error:
        messagebox.showerror("Hazır mesajlar açılamadı", f"Yerel mesaj dosyasını kontrol edin. Dosyanız değiştirilmedi.\n\n{error}", parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    launch()
