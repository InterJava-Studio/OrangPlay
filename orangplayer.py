import sys
import os

# Set the Qt plugin path for frozen applications
if getattr(sys, 'frozen', False):
    # If running as exe/frozen
    plugin_path = os.path.join(os.path.dirname(sys.executable), 'PyQt5', 'plugins')
    os.environ['QT_PLUGIN_PATH'] = plugin_path

# Import PyQt5 modules
from PyQt5.QtCore import Qt, QUrl, QTimer, QModelIndex, QSettings, QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QTreeView,
    QFileDialog, QFileSystemModel, QPushButton, QSlider, QLabel, QStatusBar, QSystemTrayIcon, QMenu,
    QFrame, QListWidget, QListWidgetItem, QMessageBox, QShortcut
)

def setup_vlc_dependencies():
    if not sys.platform.startswith("win"):
        return

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    vlc_base = os.path.join(base_path, "vlc")
    required = {"libvlc.dll", "libvlccore.dll"}
    dll_dir = None
    for root, _, files in os.walk(vlc_base):
        if required.issubset(files):
            dll_dir = root
            break
    if dll_dir:
        os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
        print("Using bundled VLC in:", dll_dir)
    else:
        print("Warning: VLC binaries not found under. Falling back to system installation.")

setup_vlc_dependencies()
import vlc

try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None
class VLCMediaPlayer(QObject):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    mediaEnded = pyqtSignal()

    def __init__(self, parent=None, video_widget=None):
        super().__init__(parent)
        self.instance = vlc.Instance()  # Enable video
        self.player = self.instance.media_player_new()
        self._duration = 0
        self._current_media = None
        self.video_widget = video_widget
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(500)
        self.poll_timer.timeout.connect(self._poll)
        self.poll_timer.start()
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_media_end)

    def set_video_widget(self, widget):
        self.video_widget = widget
        if widget:
            win_id = int(widget.winId())
            if sys.platform == "win32":
                self.player.set_hwnd(win_id)
            elif sys.platform == "darwin":
                self.player.set_nsobject(win_id)
            else:
                self.player.set_xwindow(win_id)

    def set_media(self, file_path):
        media = self.instance.media_new(file_path)
        self.player.set_media(media)
        self._current_media = file_path
        if self.video_widget:
            win_id = int(self.video_widget.winId())
            if sys.platform == "win32":
                self.player.set_hwnd(win_id)
            elif sys.platform == "darwin":
                self.player.set_nsobject(win_id)
            else:
                self.player.set_xwindow(win_id)
            media.add_options(
                'no-audio-time-stretch',  # No audio time stretching
                'network-caching=1000',   # Network cache value
                'clock-synchro=0'         # Clock sync disabled for smoother playback
            )

    def _poll(self):
        duration = self.player.get_length()
        if duration != self._duration:
            self._duration = duration
            self.durationChanged.emit(duration)
        pos = self.player.get_time()
        self.positionChanged.emit(pos)

    def _on_media_end(self, event):
        self.mediaEnded.emit()

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_position(self, position):
        duration = self.get_duration()
        if duration > 0:
            fraction = position / duration
            self.player.set_position(fraction)

    def get_position(self):
        return self.player.get_time()

    def get_duration(self):
        return self.player.get_length()

    def set_volume(self, volume):
        self.player.audio_set_volume(volume)

    def is_playing(self):
        return self.player.is_playing()

def load_icon(icon_name):
    icon_path = os.path.join(os.path.dirname(__file__), icon_name)
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, icon_name)
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return None

def loadStyle():
    user_css_path = os.path.join(os.path.expanduser("~"), "apstyle.css")
    stylesheet = None
    if os.path.exists(user_css_path):
        try:
            with open(user_css_path, 'r') as css_file:
                stylesheet = css_file.read()
            print(f"Loaded user CSS style from: {user_css_path}")
        except Exception as e:
            print(f"Error loading user CSS: {e}")
    else:
        css_file_path = os.path.join(os.path.dirname(__file__), 'style.css')
        try:
            with open(css_file_path, 'r') as css_file:
                stylesheet = css_file.read()
        except FileNotFoundError:
            print(f"Default CSS file not found: {css_file_path}")
    if stylesheet:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
        else:
            print("No QApplication instance found. Stylesheet not applied.")

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OrangPlayer")
        self.setWindowIcon(load_icon('orange.png'))
        self.setGeometry(100, 100, 1000, 600)
        self.always_on_top = False
        loadStyle()
        self.setWindowIcon(self.get_app_icon())
        self.init_ui()
        self.setup_main_ui()
        
        # Global Play/Pause on Space
        self.sc_playpause = QShortcut(Qt.Key_Space, self)
        self.sc_playpause.setContext(Qt.ApplicationShortcut)
        self.sc_playpause.activated.connect(self.play_pause)

        # Optional: navigation shortcuts
        self.sc_next = QShortcut(Qt.Key_Right, self)
        self.sc_next.setContext(Qt.ApplicationShortcut)
        self.sc_next.activated.connect(self.next_track)

        self.sc_prev = QShortcut(Qt.Key_Left, self)
        self.sc_prev.setContext(Qt.ApplicationShortcut)
        self.sc_prev.activated.connect(self.previous_track)

        # Optional: fullscreen toggle (F11 already works via keyPressEvent)
        self.sc_full = QShortcut(Qt.Key_F, self)
        self.sc_full.setContext(Qt.ApplicationShortcut)
        self.sc_full.activated.connect(self.toggle_fullscreen_video)

        self.mediaPlayer = VLCMediaPlayer(self, video_widget=self.videoFrame)
        self.mediaPlayer.set_volume(100)
        self.current_index = 0
        app_context = {"main_window": self}
        self.loop_mode = 0
        self.shuffle = False
        self.folderAudioFiles = []
        self.trackMetadata = {}
        self.setup_dock()
        self.setup_actions()
        self.setup_connections()
        self.updatePlaybackMode()
        self.setStatusBar(QStatusBar(self))
        self.settings = QSettings("InterJava", "Oranges")
        self.setup_view_menu()
        self.trayIcon = None
        self.update_slider = True
        self.videoFrame.hide()
        self.artLabel.show()
        self.titleLabel.show()
        self.authorLabel.show()
        self.albumLabel.show()
        self.yearLabel.show()
        self.resetTrackInfo()
        self.statusBar().showMessage("Select a song to begin")
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_position)
        self.timer.start()

    def init_ui(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        main_widget.setLayout(self.main_layout)

    def get_media_folder_path(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'media')

    def get_app_icon(self):
        media_path = self.get_media_folder_path()
        icon_path = os.path.join(media_path, 'orange.png')
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            print(f"Icon file not found: {icon_path}")
            return QIcon()

    def setup_dock(self):
        self.fileDock = QDockWidget("File Explorer", self)
        self.fileDock.setObjectName("FileExplorerDock")
        self.fileDock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.fileModel = QFileSystemModel()
        self.fileModel.setReadOnly(True)
        self.fileTreeView = QTreeView()
        self.fileTreeView.setModel(self.fileModel)
        self.fileDock.setWidget(self.fileTreeView)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.fileDock)
        self.fileDock.hide()
        self.playlistDock = QDockWidget("Playlist", self)
        self.playlistDock.setObjectName("PlaylistDock")
        self.playlistDock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.playlistWidget = QListWidget()
        self.playlistWidget.itemDoubleClicked.connect(self.on_playlist_item_double_clicked)
        self.playlistDock.setWidget(self.playlistWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.playlistDock)
        self.playlistDock.hide()

    def setup_main_ui(self):
        media_path = self.get_media_folder_path()
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(15)
        self.artLabel = QLabel()
        self.artLabel.setFixedSize(200, 200)
        self.artLabel.setAlignment(Qt.AlignCenter)
        placeholder_path = os.path.join(media_path, "albumartplaceholder.png")
        if os.path.exists(placeholder_path):
            pm = QPixmap(placeholder_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.artLabel.setPixmap(pm)
        else:
            self.artLabel.setText("No Art")
            self.artLabel.setStyleSheet("border: 1px solid #999; color: gray;")
        top_layout.addWidget(self.artLabel, alignment=Qt.AlignTop)
        self.videoFrame = QFrame()
        self.videoFrame.setFixedSize(1280, 800)
        self.videoFrame.setStyleSheet("background-color: black;")
        top_layout.addWidget(self.videoFrame, alignment=Qt.AlignTop)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        self.titleLabel = QLabel("Select a file to play")
        self.titleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.titleLabel.setWordWrap(False)
        info_layout.addWidget(self.titleLabel)
        self.authorLabel = QLabel("")
        self.authorLabel.setStyleSheet("font-size: 13px;")
        self.authorLabel.setWordWrap(False)
        info_layout.addWidget(self.authorLabel)
        self.albumLabel = QLabel("")
        self.albumLabel.setStyleSheet("font-size: 13px;")
        self.albumLabel.setWordWrap(False)
        info_layout.addWidget(self.albumLabel)
        self.yearLabel = QLabel("")
        self.yearLabel.setStyleSheet("font-size: 13px;")
        self.yearLabel.setWordWrap(False)
        info_layout.addWidget(self.yearLabel)
        info_layout.addStretch(1)
        top_layout.addLayout(info_layout)
        self.main_layout.addWidget(top_container)
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        media_controls_widget = QWidget()
        media_controls_layout = QHBoxLayout(media_controls_widget)
        media_controls_layout.setSpacing(15)
        media_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.prevButton = QPushButton()
        self.prevButton.setIcon(QIcon(os.path.join(media_path, "prev.png")))
        self.prevButton.setToolTip("Previous")
        media_controls_layout.addWidget(self.prevButton)
        self.playButton = QPushButton()
        self.play_icon = QIcon(os.path.join(media_path, "play.png"))
        self.pause_icon = QIcon(os.path.join(media_path, "pause.png"))
        self.playButton.setIcon(self.play_icon)
        self.playButton.setToolTip("Play/Pause")
        media_controls_layout.addWidget(self.playButton)
        self.nextButton = QPushButton()
        self.nextButton.setIcon(QIcon(os.path.join(media_path, "next.png")))
        self.nextButton.setToolTip("Next")
        media_controls_layout.addWidget(self.nextButton)
        self.loopButton = QPushButton("Off")
        self.loopButton.setToolTip("Loop")
        self.loopButton.setIcon(QIcon(os.path.join(media_path, "loop.png")))
        media_controls_layout.addWidget(self.loopButton)
        media_controls_layout.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(media_controls_widget, stretch=1, alignment=Qt.AlignCenter)
        volume_icon = QIcon(os.path.join(media_path, "volume.png"))
        self.volumeLabel = QLabel()
        self.volumeLabel.setPixmap(volume_icon.pixmap(24, 24))
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(100)
        controls_layout.addWidget(self.volumeLabel, alignment=Qt.AlignRight)
        controls_layout.addWidget(self.volumeSlider, alignment=Qt.AlignRight)
        bottom_layout.addLayout(controls_layout)
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)
        self.timeElapsedLabel = QLabel("0:00")
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setObjectName("progressBar")
        self.positionSlider.setRange(0, 0)
        self.timeRemainingLabel = QLabel("0:00")
        progress_layout.addWidget(self.timeElapsedLabel)
        progress_layout.addWidget(self.positionSlider, stretch=1)
        progress_layout.addWidget(self.timeRemainingLabel)
        bottom_layout.addLayout(progress_layout)
        self.main_layout.addWidget(bottom_container)

    def _enter_video_fullscreen(self):
        # remember original placement + what was visible
        self._vf_orig_parent = self.videoFrame.parentWidget()
        self._vf_orig_layout = self._vf_orig_parent.layout() if self._vf_orig_parent else None
        self._vf_orig_index  = self._vf_orig_layout.indexOf(self.videoFrame) if self._vf_orig_layout else -1
        self._vf_orig_size   = self.videoFrame.size()
        self._dock_vis = {
            "file": self.fileDock.isVisible(),
            "playlist": self.playlistDock.isVisible(),
        }

        self.showFullScreen()
        self.menuBar().hide()
        self.statusBar().hide()
        self.fileDock.hide()
        self.playlistDock.hide()

        # hide everything except the actual video surface
        for w in self.centralWidget().findChildren(QWidget):
            if w is not self.videoFrame:
                w.hide()

        # reparent the video widget to the window and stretch it
        self.videoFrame.setParent(self)
        rect = QApplication.desktop().screenGeometry(self)
        self.videoFrame.setGeometry(rect)
        self.videoFrame.setFixedSize(rect.size())
        self.videoFrame.setStyleSheet("background-color: black;")
        self.videoFrame.show()

        # rebind VLC to the new native window
        if self.mediaPlayer:
            if sys.platform == "win32":
                self.mediaPlayer.player.set_hwnd(int(self.videoFrame.winId()))
            elif sys.platform == "darwin":
                self.mediaPlayer.player.set_nsobject(int(self.videoFrame.winId()))
            else:
                self.mediaPlayer.player.set_xwindow(int(self.videoFrame.winId()))


    def _exit_video_fullscreen(self):
        # Leave fullscreen UI state
        self.showNormal()
        self.menuBar().show()
        self.statusBar().show()

        # 1) Put the video widget back where it was
        if getattr(self, "_vf_orig_parent", None) is not None:
            self.videoFrame.hide()
            self.videoFrame.setParent(self._vf_orig_parent)

            if getattr(self, "_vf_orig_layout", None) and getattr(self, "_vf_orig_index", -1) >= 0:
                # restore position inside original layout
                self._vf_orig_layout.insertWidget(self._vf_orig_index, self.videoFrame)

            if getattr(self, "_vf_orig_size", None):
                self.videoFrame.setFixedSize(self._vf_orig_size)

            self.videoFrame.show()

        # 2) Restore docks only to their previous visibility
        if getattr(self, "_dock_vis", None):
            self.fileDock.setVisible(self._dock_vis.get("file", False))
            self.playlistDock.setVisible(self._dock_vis.get("playlist", False))

        # 3) Re-show the entire central area (recursively), except the video surface
        cw = self.centralWidget()
        if cw:
            for w in cw.findChildren(QWidget):  # recursive
                if w is not self.videoFrame:
                    w.show()

        # 4) Rebind VLC to the restored video widget
        if self.mediaPlayer:
            self.mediaPlayer.set_video_widget(self.videoFrame)

        # 5) Let the normal logic hide/show art/labels depending on media type
        self.updateTrackInfo()

        # 6) Cleanup temp attributes
        for name in ("_vf_orig_parent", "_vf_orig_layout", "_vf_orig_index",
                    "_vf_orig_size", "_dock_vis"):
            if hasattr(self, name):
                delattr(self, name)




    def resetTrackInfo(self):
        self.titleLabel.setText("Select a song to begin")
        self.authorLabel.setText("")
        self.albumLabel.setText("")
        self.yearLabel.setText("")
        media_path = self.get_media_folder_path()
        placeholder_path = os.path.join(media_path, "albumartplaceholder.png")
        if os.path.exists(placeholder_path):
            pixmap = QPixmap(placeholder_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.artLabel.setPixmap(pixmap)
        else:
            self.artLabel.setText("No Art")
            self.artLabel.setStyleSheet("border: 1px solid #999; color: gray;")
        self.statusBar().showMessage("Select a song to begin")

    def on_playlist_item_double_clicked(self, item):
        index = self.playlistWidget.row(item)
        if 0 <= index < len(self.folderAudioFiles):
            self.current_index = index
            current_volume = self.volumeSlider.value()
            self.mediaPlayer.set_media(self.folderAudioFiles[index])
            self.mediaPlayer.set_video_widget(self.videoFrame)
            self.mediaPlayer.play()
            self.mediaPlayer.set_volume(current_volume)
            self.playButton.setIcon(self.pause_icon)
            self.updateTrackInfo()
            self.update_playlist_selection()

    def update_playlist_selection(self):
        self.playlistWidget.setCurrentRow(self.current_index)

    def populate_playlist(self, files):
        self.playlistWidget.clear()
        for file_path in files:
            meta = self.extractMetadata(file_path)
            display_text = os.path.basename(file_path)
            if meta.get('title') and meta.get('artist'):
                display_text = f"{meta['artist']} - {meta['title']}"
            elif meta.get('title'):
                display_text = meta['title']
            
            item = QListWidgetItem(display_text)
            item.setToolTip(file_path) 
            self.playlistWidget.addItem(item)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Media Folder", "")
        if folder_path:
            media_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.mp4', '.avi', '.mkv', '.webm', '.mov')
            files = []
            for fname in os.listdir(folder_path):
                fpath = os.path.join(folder_path, fname)
                if os.path.isfile(fpath) and fpath.lower().endswith(media_extensions):
                    files.append(fpath)
            files.sort()
            if files:
                self.folderAudioFiles = files
                self.current_index = 0
                self.mediaPlayer.set_media(self.folderAudioFiles[0])
                self.mediaPlayer.set_video_widget(self.videoFrame)
                self.mediaPlayer.play()
                self.populate_playlist(files)
                self.playlistDock.show()
                self.update_playlist_selection()
                self.updateTrackInfo()

    def setup_view_menu(self):
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        minimize_action = QAction("Minimize to Tray", self)
        minimize_action.triggered.connect(self.minimize_to_tray)
        view_menu.addAction(minimize_action)
        self.minimizeOnCloseAction = QAction("Closing Window Minimizes to Tray", self, checkable=True)
        self.minimizeOnCloseAction.setChecked(self.settings.value("closeToTray", False, type=bool))
        self.minimizeOnCloseAction.toggled.connect(lambda checked: self.settings.setValue("closeToTray", checked))
        view_menu.addAction(self.minimizeOnCloseAction)
        fullscreen_action = QAction("Fullscreen Video", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen_video)
        view_menu.addAction(fullscreen_action)

    def toggle_fullscreen_video(self):
        if self.videoFrame.isVisible():
            if not self.isFullScreen():
                self._enter_video_fullscreen()
            else:
                self._exit_video_fullscreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.folderAudioFiles:
                self.play_pause()
                event.accept()
                return
        elif event.key() == Qt.Key_F11:
            if self.videoFrame.isVisible():
                self.toggle_fullscreen_video()
                event.accept()
                return
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self._exit_video_fullscreen()
                event.accept()
                return
        super().keyPressEvent(event)

    def create_tray_icon(self):
        media_path = self.get_media_folder_path()
        tray_icon_path = os.path.join(media_path, 'tray.png')
        if not os.path.exists(tray_icon_path):
            print(f"Tray icon file not found: {tray_icon_path}")
        title = "OrangPlayer"
        artist = None
        album = None
        if self.folderAudioFiles and self.current_index < len(self.folderAudioFiles):
            current_file = self.folderAudioFiles[self.current_index]
            meta = self.extractMetadata(current_file)
            title = meta.get('title') or os.path.basename(current_file)
            artist = meta.get('artist') or None
            album = meta.get('album') or None
        self.trayIcon = QSystemTrayIcon(QIcon(tray_icon_path), self)
        self.trayMenu = QMenu()
        self.trayPlayPauseAction = QAction("Play/Pause", self)
        self.trayPlayPauseAction.triggered.connect(self.play_pause)
        self.trayMenu.addAction(self.trayPlayPauseAction)
        self.trayNextAction = QAction("Next", self)
        self.trayNextAction.triggered.connect(self.next_track)
        self.trayMenu.addAction(self.trayNextAction)
        self.trayPreviousAction = QAction("Previous", self)
        self.trayPreviousAction.triggered.connect(self.previous_track)
        self.trayMenu.addAction(self.trayPreviousAction)
        self.trayLoopAction = QAction("Loop", self)
        self.trayLoopAction.triggered.connect(self.toggle_loop)
        self.trayMenu.addAction(self.trayLoopAction)
        self.trayMenu.addSeparator()
        self.trayExitAction = QAction("Exit", self)
        self.trayExitAction.triggered.connect(self.close)
        self.trayMenu.addAction(self.trayExitAction)
        self.trayIcon.setContextMenu(self.trayMenu)
        tooltipStr = (f"{artist} - " if artist else "") + title + (f"\n{album}" if album else "")
        self.trayIcon.setToolTip(tooltipStr)
        self.trayIcon.activated.connect(self.on_tray_icon_activated)
        self.trayIcon.show()

    def minimize_to_tray(self):
        if self.trayIcon is None:
            self.create_tray_icon()
        self.hide()
        self.trayIcon.showMessage("OrangPlayer", "OrangPlay minimized to tray", QSystemTrayIcon.Information, 2000)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()
            self.activateWindow()
            self.trayIcon.hide()
            self.trayIcon.deleteLater()
            self.trayIcon = None

    def closeEvent(self, event):
        if self.minimizeOnCloseAction.isChecked():
            if self.trayIcon is None:
                event.ignore()
                self.minimize_to_tray()
            else:
                event.accept()
        else:
            event.accept()

    def show_about_dialog(self):
        import platform
        win_ver = platform.version()
        version_number = int(win_ver.split('.')[0])
        build_number = int(win_ver.split('.')[2])
        
        if build_number >= 22000:
            windows_version = "Windows 11"
        elif build_number >= 10240:
            windows_version = "Windows 10"
        elif build_number >= 9600:
            windows_version = "Windows 8.1"
        elif build_number >= 9200:
            windows_version = "Windows 8"
        elif build_number >= 7601:
            windows_version = "Windows 7"
        else:
            windows_version = "Windows Vista"
            
        about_text = f"""OrangPlayer
Operating System: {windows_version} (Build {build_number})
Copyright © 2025 InterJava Projects
Made by adasjusk"""
        QMessageBox.about(self, "About OrangPlayer", about_text)

    def setup_actions(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        openFileAction = QAction("Open File...", self)
        openFileAction.triggered.connect(self.open_file)
        file_menu.addAction(openFileAction)
        openFolderAction = QAction("Open Folder...", self)
        openFolderAction.triggered.connect(self.open_folder)
        file_menu.addAction(openFolderAction)
        file_menu.addSeparator()
        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.close)
        file_menu.addAction(exitAction)
        about_menu = menu_bar.addMenu("About")
        aboutAction = QAction("About OrangPlayer", self)
        aboutAction.triggered.connect(self.show_about_dialog)
        about_menu.addAction(aboutAction)

    def setup_connections(self):
        if self.mediaPlayer:
            self.mediaPlayer.positionChanged.connect(self.on_position_changed)
            self.mediaPlayer.durationChanged.connect(self.on_duration_changed)
            self.mediaPlayer.mediaEnded.connect(self.handle_media_ended)
        self.playButton.clicked.connect(self.play_pause)
        self.prevButton.clicked.connect(self.previous_track)
        self.nextButton.clicked.connect(self.next_track)
        self.loopButton.clicked.connect(self.toggle_loop)
        self.fileTreeView.doubleClicked.connect(self.onFileTreeDoubleClicked)
        if self.mediaPlayer:
            self.volumeSlider.valueChanged.connect(self.mediaPlayer.set_volume)
        self.positionSlider.sliderPressed.connect(lambda: self.allow_position_updates(False))
        self.positionSlider.sliderReleased.connect(self.on_slider_released)

    def allow_position_updates(self, allow):
        self.update_slider = allow

    def on_slider_released(self):
        self.seek(self.positionSlider.value())
        self.allow_position_updates(True)

    def handle_media_ended(self):
        if self.loop_mode == 2:
            current_volume = self.volumeSlider.value()
            self.mediaPlayer.set_media(self.folderAudioFiles[self.current_index])
            self.mediaPlayer.play()
            self.mediaPlayer.set_volume(current_volume)
        else:
            self.current_index += 1
            if self.current_index >= len(self.folderAudioFiles):
                if self.loop_mode == 1:
                    self.current_index = 0
                else:
                    self.current_index -= 1
                    self.mediaPlayer.stop()
                    self.playButton.setIcon(self.play_icon)
                    return
            current_volume = self.volumeSlider.value()
            self.mediaPlayer.set_media(self.folderAudioFiles[self.current_index])
            self.mediaPlayer.play()
            self.mediaPlayer.set_volume(current_volume)
        self.updateTrackInfo()

    def extractMetadata(self, file_path):
        if MutagenFile is None:
            return {
                'title': None,
                'artist': None,
                'album': None,
                'year': None,
                'artwork': None,
                'track': None
            }
        try:
            audio = MutagenFile(file_path)
            if not audio or not audio.tags:
                return {
                    'title': None,
                    'artist': None,
                    'album': None,
                    'year': None,
                    'artwork': None,
                    'track': None
                }
            title, artist, album, year, artwork_data, track = None, None, None, None, None, None
            if file_path.lower().endswith('.m4a'):
                title = audio.tags.get("©nam", [None])[0]
                artist = audio.tags.get("©ART", [None])[0]
                album = audio.tags.get("©alb", [None])[0]
                year = audio.tags.get("©day", [None])[0]
                track_info = audio.tags.get("trkn", [(None, None)])[0]
                track = track_info[0] if track_info else None
                if "covr" in audio.tags:
                    for cover in audio.tags["covr"]:
                        artwork_data = cover
            elif file_path.lower().endswith('.flac'):
                title = audio.get('title', [None])[0] if 'title' in audio else None
                artist = audio.get('artist', [None])[0] if 'artist' in audio else None
                album = audio.get('album', [None])[0] if 'album' in audio else None
                year = audio.get('date', [None])[0] if 'date' in audio else None
                track = audio.get('tracknumber', [None])[0] if 'tracknumber' in audio else None
                
                if audio.pictures:
                    artwork_data = audio.pictures[0].data
            elif file_path.lower().endswith('.ogg'):
                for tag in audio.tags.keys():
                    if tag == "title":
                        title = audio.tags[tag][0]
                    elif tag == "artist":
                        artist = audio.tags[tag][0]
                    elif tag == "album":
                        album = audio.tags[tag][0]
                    elif tag == "date":
                        year = audio.tags[tag][0]
                    elif tag == "metadata_block_picture":
                        from mutagen.flac import Picture
                        import base64
                        data = base64.b64decode(audio.tags[tag][0])
                        picture = Picture(data)
                        artwork_data = picture.data
                    elif tag == "tracknumber":
                        track = audio.tags[tag][0]
            else:
                for tag in audio.tags.keys():
                    if tag.startswith('TIT2'):
                        title = str(audio.tags[tag])
                    elif tag.startswith('TPE1'):
                        artist = str(audio.tags[tag])
                    elif tag.startswith('TALB'):
                        album = str(audio.tags[tag])
                    elif tag.startswith('TDRC') or tag.startswith('TYER'):
                        year = str(audio.tags[tag])
                    elif tag.startswith('APIC'):
                        artwork_data = audio.tags[tag].data
                    elif tag.startswith('TRCK'):
                        try:
                            track_str = str(audio.tags[tag])
                            track = track_str.split('/')[0].strip()
                        except Exception:
                            track = None
            return {
                'title': title,
                'artist': artist,
                'album': album,
                'year': year,
                'artwork': artwork_data,
                'track': track
            }
        except Exception:
            return {
                'title': None,
                'artist': None,
                'album': None,
                'year': None,
                'artwork': None,
                'track': None
            }

    def updateTrackInfo(self):
        current_file = self.folderAudioFiles[self.current_index] if self.folderAudioFiles else None
        video_exts = ('.mp4', '.avi', '.mkv', '.webm', '.mov')
        is_video = current_file and current_file.lower().endswith(video_exts)
        if not current_file:
            self.videoFrame.hide()
            self.artLabel.show()
            self.titleLabel.show()
            self.authorLabel.show()
            self.albumLabel.show()
            self.yearLabel.show()
            self.resetTrackInfo()
            return
        if is_video:
            self.videoFrame.show()
            self.artLabel.hide()
            self.titleLabel.hide()
            self.authorLabel.hide()
            self.albumLabel.hide()
            self.yearLabel.hide()
        else:
            self.videoFrame.hide()
            self.artLabel.show()
            self.titleLabel.show()
            self.authorLabel.show()
            self.albumLabel.show()
            self.yearLabel.show()
        meta = self.extractMetadata(current_file)
        self.trackMetadata[self.current_index] = meta
        title = meta.get('title') or os.path.basename(current_file)
        artist = meta.get('artist') or "Unknown Artist"
        album = meta.get('album') or "Unknown Album"
        year = meta.get('year') or ""
        artwork_data = meta.get('artwork')
        if not is_video:
            self.titleLabel.setText(title)
            self.authorLabel.setText(artist)
            self.albumLabel.setText(album)
            self.yearLabel.setText(year)
            if artwork_data:
                pixmap = QPixmap()
                pixmap.loadFromData(artwork_data)
                pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.artLabel.setPixmap(pixmap)
            else:
                media_path = self.get_media_folder_path()
                placeholder_path = os.path.join(media_path, "albumartplaceholder.png")
                if os.path.exists(placeholder_path):
                    pixmap = QPixmap(placeholder_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.artLabel.setPixmap(pixmap)
                else:
                    self.artLabel.setText("No Art")
                    self.artLabel.setStyleSheet("border: 1px solid #999; color: gray;")
        self.update_status_bar()
        if self.trayIcon:
            tooltipStr = ("{} - ".format(artist) if artist else "") + title + ("\nAlbum: {}".format(album) if album else "")
            self.trayIcon.setToolTip(tooltipStr)

    def onFileTreeDoubleClicked(self, index):
        file_path = self.fileModel.filePath(index)
        if os.path.isfile(file_path) and file_path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
            try:
                idx = self.folderAudioFiles.index(file_path)
            except ValueError:
                idx = len(self.folderAudioFiles)
                self.folderAudioFiles.append(file_path)
            self.current_index = idx
            if self.mediaPlayer:
                current_volume = self.volumeSlider.value()
                self.mediaPlayer.set_media(file_path)
                self.mediaPlayer.play()
                self.mediaPlayer.set_volume(current_volume)
            self.playButton.setIcon(self.pause_icon)
            meta = self.extractMetadata(file_path)
            self.trackMetadata[idx] = meta
            self.updateTrackInfo()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Media File",
            "",
            "Media Files (*.mp3 *.wav *.ogg *.flac *.m4a *.mp4 *.avi *.mkv *.webm *.mov)"
        )
        if not file_path:
            return
        
        self.folderAudioFiles = [file_path]
        self.current_index = 0
        current_volume = self.volumeSlider.value()
        self.mediaPlayer.set_media(file_path)
        self.mediaPlayer.set_video_widget(self.videoFrame)
        self.mediaPlayer.play()
        self.mediaPlayer.set_volume(current_volume)
        self.playButton.setIcon(self.pause_icon)
        self.updateTrackInfo()


    def play_pause(self):
        if self.mediaPlayer and self.folderAudioFiles:
            if self.mediaPlayer.is_playing():
                self.mediaPlayer.pause()
                self.playButton.setIcon(self.play_icon)
            else:
                current_file = self.folderAudioFiles[self.current_index]
                if not self.mediaPlayer._current_media or self.mediaPlayer._current_media != current_file:
                    self.mediaPlayer.set_media(current_file)
                self.mediaPlayer.play()
                self.playButton.setIcon(self.pause_icon)

    def next_track(self):
        if self.folderAudioFiles and self.mediaPlayer:
            self.current_index = (self.current_index + 1) % len(self.folderAudioFiles)
            next_file = self.folderAudioFiles[self.current_index]
            current_volume = self.volumeSlider.value()
            self.mediaPlayer.set_media(next_file)
            self.mediaPlayer.play()
            self.mediaPlayer.set_volume(current_volume)
            self.playButton.setIcon(self.pause_icon)
            self.update_playlist_selection()
            self.updateTrackInfo()

    def previous_track(self):
        if self.folderAudioFiles and self.mediaPlayer:
            self.current_index = (self.current_index - 1) % len(self.folderAudioFiles)
            prev_file = self.folderAudioFiles[self.current_index]
            current_volume = self.volumeSlider.value()
            self.mediaPlayer.set_media(prev_file)
            self.mediaPlayer.play()
            self.mediaPlayer.set_volume(current_volume)
            self.playButton.setIcon(self.pause_icon)
            self.update_playlist_selection()
            self.updateTrackInfo()

    def toggle_loop(self):
        self.loop_mode = (self.loop_mode + 1) % 3
        self.updatePlaybackMode()

    def updatePlaybackMode(self):
        loop_text = {0: "Off", 1: "All", 2: "One"}[self.loop_mode]
        self.loopButton.setText(loop_text)

    def on_position_changed(self, position):
        if self.update_slider:
            self.positionSlider.setValue(position)
            if self.mediaPlayer:
                self.update_time_labels(position, self.mediaPlayer.get_duration())

    def on_duration_changed(self, duration):
        self.positionSlider.setRange(0, duration)
        if self.mediaPlayer:
            self.update_time_labels(self.mediaPlayer.get_position(), duration)

    def update_position(self):
        if self.mediaPlayer:
            pos = self.mediaPlayer.get_position()
            if self.update_slider:
                self.positionSlider.setValue(pos)
            self.update_time_labels(pos, self.mediaPlayer.get_duration())
        self.update_status_bar()

    def update_time_labels(self, position, duration):
        def ms_to_minsec(ms):
            ms = max(ms, 0)
            s = ms // 1000
            m = s // 60
            s = s % 60
            return f"{m}:{s:02d}"

        self.timeElapsedLabel.setText(ms_to_minsec(position))
        if duration > 0:
            self.timeRemainingLabel.setText(ms_to_minsec(duration))
        else:
            self.timeRemainingLabel.setText("0:00")

    def seek(self, position):
        if self.mediaPlayer:
            self.mediaPlayer.set_position(position)

    def update_status_bar(self):
        if not self.folderAudioFiles:
            self.statusBar().showMessage("Select Media File to play")
            return
        file_path = self.folderAudioFiles[self.current_index] if self.current_index < len(self.folderAudioFiles) else ""
        meta = self.trackMetadata.get(self.current_index, {})
        title = meta.get('title') or (os.path.basename(file_path) if file_path else "Unknown")
        artist = meta.get('artist') or "Unknown Artist"
        album = meta.get('album') or "Unknown Album"
        def ms_to_minsec(ms):
            ms = max(ms, 0)
            s = ms // 1000
            m = s // 60
            s = s % 60
            return f"{m}:{s:02d}"
        duration = self.mediaPlayer.get_duration() if self.mediaPlayer else 0
        duration_str = ms_to_minsec(duration) if duration > 0 else "0:00"
        position = self.mediaPlayer.get_position() if self.mediaPlayer else 0
        position_str = ms_to_minsec(position)
        loop_text = {0: "Loop: Off", 1: "Loop: All", 2: "Loop: One"}[self.loop_mode]
        message = (
            f"Now Playing: {title} - {artist} | Album: {album} | "
            f"Duration: {duration_str} | Position: {position_str} | {loop_text}"
        )
        self.statusBar().showMessage(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MusicPlayer()
    if len(sys.argv) > 1:
        file_arg = sys.argv[1]
        if os.path.isfile(file_arg) and file_arg.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
            player.folderAudioFiles = [file_arg]
            player.current_index = 0
            player.mediaPlayer.set_media(file_arg)
            player.mediaPlayer.play()
            player.playButton.setIcon(player.pause_icon)
            player.updateTrackInfo()
    player.show()
    sys.exit(app.exec())