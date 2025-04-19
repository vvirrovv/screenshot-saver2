import pyautogui,os,json,time,sys,subprocess,tkinter as tk
from tkinter import colorchooser,messagebox
from PIL import ImageGrab,Image,ImageTk
import keyboard
from screeninfo import get_monitors
import winreg,ctypes
config_dir=os.path.join(os.getenv("APPDATA"),"ScreenshotSaver")
config_file=os.path.join(config_dir,"config.json")
script_path=os.path.abspath(__file__)
startup_shortcut=os.path.join(os.getenv("APPDATA"),"Microsoft\\Windows\\Start Menu\\Programs\\Startup","ScreenshotSaver.lnk")
default_config={"screenshot_key":"f10","exit_key":"ctrl+1","selection_color":"#FF7F00","overlay_color":"#FFFFFF","selection_opacity":0.3,"overlay_opacity":0.2,"autostart":False}
active_hotkeys={}
# Variabile globale per l'avvio automatico
autostart_value = False 
if not os.path.exists(config_dir):os.makedirs(config_dir)
if not os.path.exists(config_file):
    with open(config_file,"w") as f:json.dump(default_config,f,indent=4)
def load_config():
    try:
        with open(config_file,"r") as f:return json.load(f)
    except Exception as e:
        print(f"Errore nel caricamento della configurazione: {e}")
        return default_config
def save_config(new_config):
    try:
        print(f"Salvataggio configurazione: {new_config}")
        with open(config_file, "w") as f:json.dump(new_config, f, indent=4)
        return True
    except Exception as e:
        print(f"Errore salvataggio configurazione: {e}")
        return False
config=load_config()
SCREENSHOT_KEY=config.get("screenshot_key","f10").lower()
EXIT_KEY=config.get("exit_key","ctrl+1").lower()
SELECTION_COLOR=config.get("selection_color","#FF7F00")
SELECTION_OPACITY=float(config.get("selection_opacity",0.3))
OVERLAY_COLOR=config.get("overlay_color","#FFFFFF")
OVERLAY_OPACITY=float(config.get("overlay_opacity",0.2))
AUTOSTART=bool(config.get("autostart",False))
desktop_path=os.path.join(os.path.expanduser("~"),"Desktop")
def get_virtual_screen_geometry():
    monitors=get_monitors()
    if not monitors:return 0,0,1920,1080
    min_x,min_y=float('inf'),float('inf')
    max_x,max_y=float('-inf'),float('-inf')
    for m in monitors:
        if not hasattr(m,'x') or not hasattr(m,'y') or not hasattr(m,'width') or not hasattr(m,'height'):continue
        min_x=min(min_x,m.x if m.x is not None else 0)
        min_y=min(min_y,m.y if m.y is not None else 0)
        max_x=max(max_x,(m.x if m.x is not None else 0)+(m.width if m.width is not None else 1920))
        max_y=max(max_y,(m.y if m.y is not None else 0)+(m.height if m.height is not None else 1080))
    if min_x==float('inf'):min_x=0
    if min_y==float('inf'):min_y=0
    if max_x==float('-inf'):max_x=1920
    if max_y==float('-inf'):max_y=1080
    return min_x,min_y,max_x,max_y
def get_primary_monitor():
    monitors=get_monitors()
    if not monitors:
        class DummyMonitor:
            def __init__(self):
                self.x=0;self.y=0;self.width=1920;self.height=1080;self.is_primary=True
        return DummyMonitor()
    for m in monitors:
        if hasattr(m,'is_primary') and m.is_primary:
            if not hasattr(m,'x') or m.x is None:m.x=0
            if not hasattr(m,'y') or m.y is None:m.y=0
            if not hasattr(m,'width') or m.width is None:m.width=1920
            if not hasattr(m,'height') or m.height is None:m.height=1080
            return m
    first_monitor=monitors[0]
    if not hasattr(first_monitor,'x') or first_monitor.x is None:first_monitor.x=0
    if not hasattr(first_monitor,'y') or first_monitor.y is None:first_monitor.y=0
    if not hasattr(first_monitor,'width') or first_monitor.width is None:first_monitor.width=1920
    if not hasattr(first_monitor,'height') or first_monitor.height is None:first_monitor.height=1080
    return first_monitor
def create_settings_icon():
    primary=get_primary_monitor()
    icon_window=tk.Toplevel()
    icon_window.overrideredirect(True)
    icon_window.attributes("-topmost",True)
    icon_size=40
    x_pos=primary.x+primary.width-icon_size-20
    y_pos=int(primary.y+primary.height/2-icon_size/2)
    icon_window.geometry(f"{icon_size}x{icon_size}+{x_pos}+{y_pos}")
    apple_gray="#8E8E93";apple_darkgray="#636366";bg_color="#2C2C2E"
    canvas=tk.Canvas(icon_window,width=icon_size,height=icon_size,bg=bg_color,highlightthickness=0)
    canvas.pack()
    canvas.create_oval(5,5,icon_size-5,icon_size-5,outline=apple_gray,fill=bg_color,width=2)
    canvas.create_text(icon_size/2,icon_size/2,text="⚙",fill=apple_gray,font=("Arial",22))
    def on_enter(e):
        canvas.itemconfig(1,outline=apple_darkgray);canvas.itemconfig(2,fill=apple_darkgray)
    def on_leave(e):
        canvas.itemconfig(1,outline=apple_gray);canvas.itemconfig(2,fill=apple_gray)
    def on_click(e):
        icon_window.destroy();open_settings()
    canvas.bind("<Enter>",on_enter);canvas.bind("<Leave>",on_leave);canvas.bind("<Button-1>",on_click)
    return icon_window
def color_picker(parent,current_color,callback=None):
    color_frame=tk.Frame(parent,bg="#f0f0f0")
    preset_colors=["#FF0000","#FF7F00","#FFFF00","#00FF00","#00FFFF","#0000FF","#8B00FF",
                  "#FF69B4","#FF1493","#FFA500","#32CD32","#1E90FF","#9400D3","#FF00FF",
                  "#000000","#333333","#666666","#999999","#CCCCCC","#FFFFFF"]
    palette_frame=tk.Frame(color_frame,bg="#f0f0f0")
    palette_frame.pack(fill="x",expand=True,pady=5)
    selected_color=tk.StringVar(value=current_color)
    preview_frame=tk.Frame(color_frame,width=80,height=30,bg=current_color)
    preview_frame.pack(pady=5)
    buttons_per_row=7
    for i,color in enumerate(preset_colors):
        row=i//buttons_per_row;col=i%buttons_per_row
        def make_color_setter(clr):
            def set_color():
                selected_color.set(clr);preview_frame.config(bg=clr)
                if callback:callback(clr)
            return set_color
        btn=tk.Button(palette_frame,bg=color,width=3,height=1,relief="flat",command=make_color_setter(color))
        btn.grid(row=row,column=col,padx=2,pady=2)
    def open_advanced_picker():
        color=colorchooser.askcolor(initialcolor=selected_color.get())[1]
        if color:
            selected_color.set(color);preview_frame.config(bg=color)
            if callback:callback(color)
    advanced_btn=tk.Button(color_frame,text="Più colori...",command=open_advanced_picker)
    advanced_btn.pack(pady=5)
    return color_frame,selected_color
def apply_settings_without_restart():
    global SCREENSHOT_KEY,EXIT_KEY,SELECTION_COLOR,SELECTION_OPACITY,OVERLAY_COLOR,OVERLAY_OPACITY,AUTOSTART,active_hotkeys
    new_config=load_config()
    print(f"Applying settings: {new_config}")
    for key in active_hotkeys:
        try:keyboard.remove_hotkey(active_hotkeys[key])
        except:pass
    SCREENSHOT_KEY=new_config.get("screenshot_key","f10").lower()
    EXIT_KEY=new_config.get("exit_key","ctrl+1").lower()
    SELECTION_COLOR=new_config.get("selection_color","#FF7F00")
    SELECTION_OPACITY=float(new_config.get("selection_opacity",0.3))
    OVERLAY_COLOR=new_config.get("overlay_color","#FFFFFF")
    OVERLAY_OPACITY=float(new_config.get("overlay_opacity",0.2))
    AUTOSTART=bool(new_config.get("autostart",False))
    print(f"Updated settings: SCREENSHOT_KEY={SCREENSHOT_KEY}, EXIT_KEY={EXIT_KEY}")
    print(f"SELECTION_COLOR={SELECTION_COLOR}, SELECTION_OPACITY={SELECTION_OPACITY}")
    print(f"OVERLAY_COLOR={OVERLAY_COLOR}, OVERLAY_OPACITY={OVERLAY_OPACITY}")
    print(f"AUTOSTART={AUTOSTART}")
    active_hotkeys["screenshot"]=keyboard.add_hotkey(SCREENSHOT_KEY,select_area)
    active_hotkeys["exit"]=keyboard.add_hotkey(EXIT_KEY,exit_program)
    return new_config
def manage_autostart(enable):
    try:
        if os.path.exists(startup_shortcut):
            os.remove(startup_shortcut)
            print(f"Collegamento esistente rimosso: {startup_shortcut}")
        bat_path=os.path.join(os.getenv("APPDATA"),"Microsoft\\Windows\\Start Menu\\Programs\\Startup","ScreenshotSaver.bat")
        if os.path.exists(bat_path):
            os.remove(bat_path)
            print(f"File .bat rimosso: {bat_path}")
        if enable:
            target_path=sys.executable.replace('python.exe','pythonw.exe')
            if not target_path.endswith('pythonw.exe'):
                target_path=os.path.join(os.path.dirname(sys.executable),'pythonw.exe')
            bat_path=os.path.join(os.getenv("APPDATA"),"Microsoft\\Windows\\Start Menu\\Programs\\Startup","ScreenshotSaver.bat")
            with open(bat_path,'w') as f:
                f.write(f'@echo off\nstart "" "{target_path}" "{script_path}"\n')
            print(f"File .bat creato: {bat_path}")
            return True
        else:
            print(f"Avvio automatico disattivato")
            return True
    except Exception as e:
        print(f"Errore nella gestione dell'avvio automatico: {e}")
        import traceback;traceback.print_exc()
        return False
def open_settings():
    global autostart_value
    settings_window=tk.Tk()
    settings_window.title("ScreenshotSaver 2.1 - Impostazioni")
    settings_window.geometry("500x550")
    settings_window.resizable(False,False)
    current_config=load_config()
    settings_window.configure(bg="#f0f0f0")
    title_label=tk.Label(settings_window,text="ScreenshotSaver 2.1",font=("Arial",16,"bold"),bg="#f0f0f0")
    title_label.pack(pady=(15,5))
    subtitle_label=tk.Label(settings_window,text="Impostazioni",font=("Arial",12),bg="#f0f0f0")
    subtitle_label.pack(pady=(0,15))
    main_container=tk.Frame(settings_window,bg="#f0f0f0")
    main_container.pack(fill="both",expand=True,padx=20)
    canvas=tk.Canvas(main_container,bg="#f0f0f0",highlightthickness=0)
    scrollbar=tk.Scrollbar(main_container,orient="vertical",command=canvas.yview)
    scrollable_frame=tk.Frame(canvas,bg="#f0f0f0")
    scrollable_frame.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0),window=scrollable_frame,anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left",fill="both",expand=True)
    scrollbar.pack(side="right",fill="y")
    commands_frame=tk.LabelFrame(scrollable_frame,text="Comandi",bg="#f0f0f0",padx=10,pady=10)
    commands_frame.pack(fill="x",expand=True,pady=10)
    key_label=tk.Label(commands_frame,text="Tasto Screenshot:",anchor="w",bg="#f0f0f0",font=("Arial",10))
    key_label.grid(row=0,column=0,sticky="w",pady=(10,5))
    key_var=tk.StringVar(value=current_config.get("screenshot_key","f10"))
    key_entry=tk.Entry(commands_frame,textvariable=key_var,width=15)
    key_entry.grid(row=0,column=1,sticky="w",pady=(10,5),padx=5)
    exit_label=tk.Label(commands_frame,text="Tasto Uscita:",anchor="w",bg="#f0f0f0",font=("Arial",10))
    exit_label.grid(row=1,column=0,sticky="w",pady=5)
    exit_var=tk.StringVar(value=current_config.get("exit_key","ctrl+1"))
    exit_entry=tk.Entry(commands_frame,textvariable=exit_var,width=15)
    exit_entry.grid(row=1,column=1,sticky="w",pady=5,padx=5)
    selection_frame=tk.LabelFrame(scrollable_frame,text="Aspetto Selezione",bg="#f0f0f0",padx=10,pady=10)
    selection_frame.pack(fill="x",expand=True,pady=10)
    color_label=tk.Label(selection_frame,text="Colore Selezione:",anchor="w",bg="#f0f0f0",font=("Arial",10))
    color_label.grid(row=0,column=0,sticky="w",pady=(10,5))
    select_color_var=tk.StringVar(value=current_config.get("selection_color","#FF7F00"))
    def update_selection_color(color):select_color_var.set(color)
    color_picker_frame,_=color_picker(selection_frame,select_color_var.get(),update_selection_color)
    color_picker_frame.grid(row=0,column=1,sticky="w",pady=(10,5),padx=5)
    overlay_frame=tk.LabelFrame(scrollable_frame,text="Overlay",bg="#f0f0f0",padx=10,pady=10)
    overlay_frame.pack(fill="x",expand=True,pady=10)
    overlay_color_label=tk.Label(overlay_frame,text="Colore Sfondo:",anchor="w",bg="#f0f0f0",font=("Arial",10))
    overlay_color_label.grid(row=0,column=0,sticky="w",pady=(10,5))
    overlay_color_var=tk.StringVar(value=current_config.get("overlay_color","#FFFFFF"))
    def update_overlay_color(color):overlay_color_var.set(color)
    overlay_color_picker_frame,_=color_picker(overlay_frame,overlay_color_var.get(),update_overlay_color)
    overlay_color_picker_frame.grid(row=0,column=1,sticky="w",pady=(10,5),padx=5)
    startup_frame=tk.LabelFrame(scrollable_frame,text="Avvio",bg="#f0f0f0",padx=10,pady=10)
    startup_frame.pack(fill="x",expand=True,pady=10)
    
    # Leggiamo lo stato di autostart dal file di configurazione
    autostart_value = current_config.get("autostart", False)
    print(f"Stato attuale autostart: {autostart_value}")
    
    # Creiamo un'etichetta e un pulsante per gestire lo stato
    autostart_label = tk.Label(startup_frame, text="Avvia automaticamente con Windows:", bg="#f0f0f0", font=("Arial",10))
    autostart_label.grid(row=0, column=0, sticky="w", pady=5, padx=5)
    
    autostart_state_label = tk.Label(startup_frame, text="Disattivato", bg="#f0f0f0", fg="red", font=("Arial",10,"bold"))
    if autostart_value:
        autostart_state_label.config(text="Attivato", fg="green")
    autostart_state_label.grid(row=0, column=1, sticky="w", pady=5, padx=5)
    
    def toggle_autostart():
        global autostart_value
        autostart_value = not autostart_value
        if autostart_value:
            autostart_state_label.config(text="Attivato", fg="green")
        else:
            autostart_state_label.config(text="Disattivato", fg="red")
        print(f"Autostart cambiato a: {autostart_value}")
    
    toggle_btn = tk.Button(startup_frame, text="Cambia", command=toggle_autostart, bg="#e0e0e0", font=("Arial",9))
    toggle_btn.grid(row=0, column=2, sticky="w", pady=5, padx=5)
    
    preview_frame=tk.LabelFrame(scrollable_frame,text="Anteprima",bg="#f0f0f0",padx=10,pady=10)
    preview_frame.pack(fill="x",expand=True,pady=10)
    preview_canvas=tk.Canvas(preview_frame,width=450,height=120,bg=overlay_color_var.get())
    preview_canvas.pack(pady=10)
    preview_rect=preview_canvas.create_rectangle(100,20,350,100,outline=select_color_var.get(),fill=select_color_var.get(),width=2)
    def update_preview(*args):
        bg_color=overlay_color_var.get()
        preview_canvas.config(bg=bg_color)
        select_color=select_color_var.get()
        preview_canvas.itemconfig(preview_rect,outline=select_color,fill=select_color)
        preview_canvas.itemconfig(preview_rect,stipple="gray50")
    select_color_var.trace("w",update_preview)
    overlay_color_var.trace("w",update_preview)
    def test_selection():
        temp_config={
            "screenshot_key":key_var.get().lower(),
            "exit_key":exit_var.get().lower(),
            "selection_color":select_color_var.get(),
            "selection_opacity":SELECTION_OPACITY,
            "overlay_color":overlay_color_var.get(),
            "overlay_opacity":OVERLAY_OPACITY,
            "autostart":autostart_value
        }
        print(f"Test config: {temp_config}")
        save_config(temp_config)
        apply_settings_without_restart()
        settings_window.withdraw()
        select_area()
        settings_window.after(100,settings_window.deiconify)
    test_btn=tk.Button(preview_frame,text="Testa Selezione",command=test_selection,bg="#e0e0e0",font=("Arial",9))
    test_btn.pack(pady=5)
    btn_frame=tk.Frame(settings_window,bg="#f0f0f0")
    btn_frame.pack(fill="x",pady=15,padx=20)
    def save_settings():
        global autostart_value
        print(f"Valore autostart prima del salvataggio: {autostart_value}, tipo: {type(autostart_value)}")
        new_config={
            "screenshot_key":key_var.get().lower(),
            "exit_key":exit_var.get().lower(),
            "selection_color":select_color_var.get(),
            "selection_opacity":SELECTION_OPACITY,
            "overlay_color":overlay_color_var.get(),
            "overlay_opacity":OVERLAY_OPACITY,
            "autostart":autostart_value
        }
        print(f"Saving config: {new_config}")
        old_autostart=load_config().get("autostart",False)
        if old_autostart!=autostart_value:
            print(f"Cambio stato autostart: {old_autostart} -> {autostart_value}")
            success=manage_autostart(autostart_value)
            if not success:
                messagebox.showwarning("Attenzione","Errore nel configurare l'avvio automatico.")
        success=save_config(new_config)
        if success:
            apply_settings_without_restart()
            settings_window.destroy()
            show_notification("Impostazioni salvate e applicate")
        else:
            messagebox.showerror("Errore","Impossibile salvare le impostazioni!")
    save_btn=tk.Button(btn_frame,text="Salva",command=save_settings,width=10,bg="#4CAF50",fg="white",font=("Arial",10))
    save_btn.pack(side="right",padx=5)
    cancel_btn=tk.Button(btn_frame,text="Annulla",command=settings_window.destroy,width=10,font=("Arial",10))
    cancel_btn.pack(side="right",padx=5)
    update_preview()
    settings_window.mainloop()
def select_area():
    root=tk.Tk()
    root.withdraw()
    settings_icon=create_settings_icon()
    min_x,min_y,max_x,max_y=get_virtual_screen_geometry()
    width=max_x-min_x
    height=max_y-min_y
    select_window=tk.Toplevel(root)
    select_window.attributes("-alpha",OVERLAY_OPACITY)
    select_window.attributes("-topmost",True)
    select_window.overrideredirect(True)
    select_window.geometry(f"{width}x{height}+{min_x}+{min_y}")
    bg_color=OVERLAY_COLOR
    canvas=tk.Canvas(select_window,cursor="cross",bg=bg_color,highlightthickness=0)
    canvas.pack(fill=tk.BOTH,expand=True)
    start_x,start_y=None,None
    rect_id=None
    def on_press(event):
        nonlocal start_x,start_y,rect_id
        start_x,start_y=event.x,event.y
        rect_id=canvas.create_rectangle(start_x,start_y,start_x,start_y,outline=SELECTION_COLOR,width=2,fill=SELECTION_COLOR)
    def on_drag(event):
        nonlocal rect_id
        if rect_id:canvas.coords(rect_id,start_x,start_y,event.x,event.y)
    def on_release(event):
        nonlocal start_x,start_y
        if start_x is None or start_y is None:
            select_window.destroy()
            settings_icon.destroy()
            root.destroy()
            return
        if abs(event.x-start_x)<5 and abs(event.y-start_y)<5:
            select_window.destroy()
            settings_icon.destroy()
            root.destroy()
            return
        x1,y1=start_x+min_x,start_y+min_y
        x2,y2=event.x+min_x,event.y+min_y
        select_window.destroy()
        settings_icon.destroy()
        root.destroy()
        take_screenshot(x1,y1,x2,y2)
    def on_escape(event):
        select_window.destroy()
        settings_icon.destroy()
        root.destroy()
    canvas.bind("<ButtonPress-1>",on_press)
    canvas.bind("<B1-Motion>",on_drag)
    canvas.bind("<ButtonRelease-1>",on_release)
    select_window.bind("<Escape>",on_escape)
    root.mainloop()
def take_screenshot(x1,y1,x2,y2):
    print("📸 Screenshot in corso...")
    time.sleep(0.2)
    x1,x2=min(x1,x2),max(x1,x2)
    y1,y2=min(y1,y2),max(y1,y2)
    try:
        screenshot=ImageGrab.grab(bbox=(x1,y1,x2,y2),all_screens=True)
        timestamp=int(time.time())
        file_path=os.path.join(desktop_path,f"screenshot_{timestamp}.png")
        screenshot.save(file_path)
        print(f"✅ Screenshot salvato: {file_path}")
        show_notification(f"Screenshot salvato sul desktop")
    except Exception as e:
        print(f"❌ Errore durante il salvataggio dello screenshot: {e}")
        show_notification(f"Errore: {e}")
def show_notification(message,duration=2):
    notification=tk.Tk()
    notification.withdraw()
    popup=tk.Toplevel(notification)
    popup.overrideredirect(True)
    popup.attributes("-topmost",True)
    screen_width=notification.winfo_screenwidth()
    screen_height=notification.winfo_screenheight()
    width=300
    height=60
    x=screen_width-width-20
    y=screen_height-height-60
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.configure(bg="#333333")
    label=tk.Label(popup,text=message,fg="white",bg="#333333",font=("Arial",10))
    label.pack(fill=tk.BOTH,expand=True)
    popup.after(duration*1000,popup.destroy)
    notification.after(duration*1000+100,notification.destroy)
    notification.mainloop()
def exit_program():
    print("❌ Chiusura immediata del programma...")
    os._exit(0)
def create_installer():
    try:
        nsis_script_path=os.path.join(os.path.dirname(script_path),"installer.nsi")
        nsis_content=f"""
; Script per l'installer di ScreenshotSaver 2.1
!include "MUI2.nsh"
Name "ScreenshotSaver 2.1"
OutFile "ScreenshotSaver_2.1_Setup.exe"
InstallDir "$PROGRAMFILES\\ScreenshotSaver"
!define MUI_ICON "{os.path.dirname(script_path)}\\icon.ico"
!define MUI_UNICON "{os.path.dirname(script_path)}\\icon.ico"
!define MUI_WELCOMEPAGE_TITLE "Benvenuto nell'installazione di ScreenshotSaver 2.1"
!define MUI_WELCOMEPAGE_TEXT "Questa procedura ti guiderà nell'installazione di ScreenshotSaver 2.1.$\\r$\\n$\\r$\\nScreenshotSaver è un'applicazione per catturare e salvare screenshot in modo semplice e veloce.$\\r$\\n$\\r$\\nPrima di procedere, assicurati di chiudere tutte le istanze di ScreenshotSaver."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Italian"
Section "Installazione" SecInstall
 SetOutPath $INSTDIR
 File "{script_path}"
 File "{os.path.dirname(script_path)}\\icon.ico"
 CreateDirectory "$SMPROGRAMS\\ScreenshotSaver"
 CreateShortcut "$SMPROGRAMS\\ScreenshotSaver\\ScreenshotSaver.lnk" "pythonw.exe" "$\\"$INSTDIR\\screenshot_saver.py$\\""
 CreateShortcut "$DESKTOP\\ScreenshotSaver.lnk" "pythonw.exe" "$\\"$INSTDIR\\screenshot_saver.py$\\""
 WriteUninstaller "$INSTDIR\\uninstall.exe"
 WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ScreenshotSaver" "DisplayName" "ScreenshotSaver 2.1"
 WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ScreenshotSaver" "UninstallString" "$\\"$INSTDIR\\uninstall.exe$\\""
 WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ScreenshotSaver" "DisplayIcon" "$\\"$INSTDIR\\icon.ico$\\""
 WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ScreenshotSaver" "Publisher" "ScreenshotSaver"
 WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ScreenshotSaver" "DisplayVersion" "2.1"
SectionEnd
Section "Uninstall"
 Delete "$INSTDIR\\screenshot_saver.py"
 Delete "$INSTDIR\\icon.ico"
 Delete "$INSTDIR\\uninstall.exe"
 Delete "$SMPROGRAMS\\ScreenshotSaver\\ScreenshotSaver.lnk"
 RMDir "$SMPROGRAMS\\ScreenshotSaver"
 Delete "$DESKTOP\\ScreenshotSaver.lnk"
 RMDir "$INSTDIR"
 DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ScreenshotSaver"
SectionEnd
"""
        with open(nsis_script_path,"w") as nsis_file:nsis_file.write(nsis_content)
        icon_path=os.path.join(os.path.dirname(script_path),"icon.ico")
        if not os.path.exists(icon_path):
            messagebox.showinfo("Creazione Installer","Script NSIS creato con successo!\n\n"+
                             "Per completare l'installer è necessario:\n"+
                             "1. Creare un'icona 'icon.ico' nella stessa cartella\n"+
                             "2. Installare NSIS (Nullsoft Scriptable Install System)\n"+
                             "3. Compilare installer.nsi con NSIS")
        return True
    except Exception as e:
        messagebox.showerror("Errore",f"Errore nella creazione dell'installer: {e}")
        return False
def show_about():
    about_window=tk.Toplevel()
    about_window.title("Informazioni su ScreenshotSaver")
    about_window.geometry("400x300")
    about_window.resizable(False,False)
    about_window.configure(bg="#f0f0f0")
    logo_frame=tk.Frame(about_window,width=100,height=100,bg="#4CAF50")
    logo_frame.pack(pady=(20,10))
    title_label=tk.Label(about_window,text="ScreenshotSaver 2.1",font=("Arial",16,"bold"),bg="#f0f0f0")
    title_label.pack(pady=(10,5))
    desc_label=tk.Label(about_window,text="Uno strumento semplice e veloce\nper catturare screenshot su Windows",font=("Arial",10),bg="#f0f0f0")
    desc_label.pack(pady=5)
    version_label=tk.Label(about_window,text="Versione 2.1",font=("Arial",10),bg="#f0f0f0")
    version_label.pack(pady=5)
    copyright_label=tk.Label(about_window,text="© 2025",font=("Arial",8),bg="#f0f0f0",fg="#666666")
    copyright_label.pack(pady=5)
    close_btn=tk.Button(about_window,text="Chiudi",command=about_window.destroy,width=10,font=("Arial",10))
    close_btn.pack(side="bottom",pady=20)
def main():
    print("🚀 ScreenshotSaver 2.1 avviato in background...")
    keyboard.wait()
if __name__=="__main__":
    if len(sys.argv)>1:
        if sys.argv[1]=="--create-installer":
            create_installer()
            sys.exit()
        elif sys.argv[1]=="--settings":
            open_settings()
            sys.exit()
        elif sys.argv[1]=="--about":
            root=tk.Tk()
            root.withdraw()
            show_about()
            root.mainloop()
            sys.exit()
    # Carica lo stato di autostart dalla configurazione
    autostart_value = load_config().get("autostart", False)
    # Attiva gli hotkey per screenshot e uscita
    active_hotkeys["screenshot"]=keyboard.add_hotkey(SCREENSHOT_KEY,select_area)
    active_hotkeys["exit"]=keyboard.add_hotkey(EXIT_KEY,exit_program)
    main()