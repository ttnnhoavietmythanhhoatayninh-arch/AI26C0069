"""Optional Tkinter local interface. Not the BTC container ENTRYPOINT."""
import csv
import json
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from local_runner import prepare_run,ROOT

class App:
    def __init__(self,root):
        self.root=root;root.title('ExcelQA | AI26C0069');root.geometry('1080x760');root.minsize(860,640)
        self.events=queue.Queue();self.process=None;self.busy=False
        style=ttk.Style();style.theme_use('clam')
        style.configure('TFrame',background='#f3f6fb');style.configure('TLabel',background='#f3f6fb',font=('Segoe UI',10))
        style.configure('Title.TLabel',font=('Segoe UI',24,'bold'),foreground='#12223c')
        style.configure('TButton',padding=8);style.configure('Treeview',rowheight=28,font=('Segoe UI',10))
        frame=ttk.Frame(root,padding=24);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='ExcelQA',style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame,text='AI26C0069 · Hỏi đáp bảng tính · Giao diện chạy thử local').pack(anchor='w',pady=(0,18))
        config=ttk.Frame(frame);config.pack(fill='x');config.columnconfigure(1,weight=1)
        self.data=tk.StringVar();self.output=tk.StringVar(value=str(Path.home()/'ExcelQA_KetQua'))
        self.mode=tk.StringVar(value='offline');self.key=tk.StringVar();self.status=tk.StringVar(value='Sẵn sàng. Chọn thư mục chứa queries.json và xlsx_files.')
        for row,(label,var) in enumerate([('Thư mục dữ liệu',self.data),('Thư mục kết quả',self.output)]):
            ttk.Label(config,text=label).grid(row=row,column=0,sticky='w',padx=(0,12),pady=6)
            ttk.Entry(config,textvariable=var).grid(row=row,column=1,sticky='ew')
            ttk.Button(config,text='Chọn thư mục',command=lambda v=var:self.browse(v)).grid(row=row,column=2,padx=(10,0))
        ttk.Label(config,text='Chế độ').grid(row=2,column=0,sticky='w',pady=8)
        ttk.Combobox(config,textvariable=self.mode,values=['offline','hybrid'],state='readonly',width=18).grid(row=2,column=1,sticky='w')
        ttk.Label(config,text='OpenRouter key').grid(row=3,column=0,sticky='w',pady=8)
        ttk.Entry(config,textvariable=self.key,show='*').grid(row=3,column=1,sticky='ew')
        ttk.Label(frame,text='Offline: không gọi API. Hybrid: chỉ Qwen BTC quy định; có thể phát sinh phí. Key không được lưu vào tệp.').pack(anchor='w',pady=(12,14))
        buttons=ttk.Frame(frame);buttons.pack(fill='x')
        self.run_button=ttk.Button(buttons,text='Chạy bộ câu hỏi',command=self.start);self.run_button.pack(side='left')
        ttk.Button(buttons,text='Dừng',command=self.stop).pack(side='left',padx=8)
        ttk.Label(buttons,textvariable=self.status,wraplength=650).pack(side='left',padx=12)
        self.progress=ttk.Progressbar(frame,mode='determinate');self.progress.pack(fill='x',pady=14)
        self.table=ttk.Treeview(frame,columns=('id','answer'),show='headings',height=8)
        self.table.heading('id',text='ID');self.table.heading('answer',text='Đáp án');self.table.column('id',width=90,stretch=False);self.table.column('answer',width=800)
        self.table.pack(fill='both',expand=True)
        ttk.Label(frame,text='Nhật ký thực thi — “có đáp án” không đồng nghĩa “đã đúng đáp án BTC”.').pack(anchor='w',pady=(12,4))
        self.logs=tk.Text(frame,height=6,font=('Consolas',9),state='disabled',bg='#142238',fg='#dae6fa');self.logs.pack(fill='x')
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll)
    def browse(self,var):
        value=filedialog.askdirectory()
        if value:var.set(value)
    def start(self):
        if self.busy:return
        try:args,env,total=prepare_run(self.data.get(),self.output.get(),self.mode.get(),self.key.get())
        except Exception as e:messagebox.showerror('Chưa chạy',str(e));return
        self.key.set('');self.busy=True;self.run_button.configure(state='disabled');self.progress.configure(maximum=total,value=0)
        for item in self.table.get_children():self.table.delete(item)
        self.run_output=Path(self.output.get()).resolve()
        self.status.set('Đang xử lý...')
        threading.Thread(target=self.worker,args=(args,env),daemon=True).start()
    def worker(self,args,env):
        try:
            self.process=subprocess.Popen(args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in self.process.stdout:self.events.put(('line',line))
            code=self.process.wait();self.events.put(('done',code))
        except Exception as e:self.events.put(('failure',type(e).__name__))
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='line':
                    self.logs.configure(state='normal');self.logs.insert('end',value);self.logs.see('end');self.logs.configure(state='disabled')
                    try:
                        event=json.loads(value)
                        if event.get('event')=='question':self.progress.step(1)
                    except ValueError:pass
                else:
                    self.busy=False;self.process=None;self.run_button.configure(state='normal')
                    self.status.set('Hoàn tất lượt chạy.' if kind=='done' and value==0 else 'Lượt chạy chưa hoàn tất; xem nhật ký.')
                    if kind=='done' and value==0:
                        try:
                            with (self.run_output/'submission.csv').open(encoding='utf-8',newline='') as f:
                                for r in csv.DictReader(f):self.table.insert('', 'end',values=(r['id'],r['answer']))
                            report=json.loads((self.run_output/'run_report.json').read_text(encoding='utf-8'))
                            self.status.set(f"Có đáp án {report['solved']}/{report['questions']} · API {report['llm_calls']} lượt · Xem CSV trong thư mục kết quả")
                        except (OSError,ValueError,KeyError):self.status.set('Đã chạy; chưa đọc được báo cáo. Kiểm tra thư mục kết quả.')
        except queue.Empty:pass
        self.root.after(100,self.poll)
    def stop(self):
        if self.process is not None:self.process.terminate();self.status.set('Đang dừng; không dùng CSV dở dang để nộp.')
    def close(self):
        self.stop();self.root.destroy()

if __name__=='__main__':App(tk.Tk()).root.mainloop()
