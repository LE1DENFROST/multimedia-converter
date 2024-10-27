from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import QFileDialog, QLabel, QFrame, QSlider, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap , QPalette, QColor
import os
import sys
from PIL import Image
from pydub import AudioSegment
import moviepy.editor as mp
from pathlib import Path
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO
import subprocess
import tempfile


class ConversionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str) 
    def __init__(self, source_file, target_format, file_type):
        super().__init__()
        self.source_file = source_file
        self.target_format = target_format
        self.file_type = file_type   
    def run(self):
        try:
            source_path = Path(self.source_file)
            target_path = source_path.parent / f"{source_path.stem}_converted{self.target_format}"
            if self.file_type == 'resim':
                self.convert_image(source_path, target_path)
            elif self.file_type == 'ses':
                self.convert_audio(source_path, target_path)
            elif self.file_type == 'video':
                self.convert_video(source_path, target_path)   
            self.finished.emit(True, str(target_path))
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def convert_image(self, source_path, target_path):
        try:
            source_ext = source_path.suffix.lower()
            target_ext = Path(target_path).suffix.lower()
            if source_ext == '.svg':
                drawing = svg2rlg(str(source_path))
                temp_buffer = BytesIO()
                renderPM.drawToFile(drawing, temp_buffer, fmt="PNG")
                temp_buffer.seek(0)
                img = Image.open(temp_buffer)
            else:
                img = Image.open(source_path)
            if target_ext == '.avif':
                if img.mode in ['RGBA', 'P']:
                    img = img.convert('RGB')
            elif target_ext in ['.jpg', '.jpeg']:
                if img.mode in ['RGBA', 'P']:
                    img = img.convert('RGB')   
            self.progress.emit(50)
            if target_ext == '.avif':
                img.save(target_path, format='avif', quality=75)
            elif target_ext == '.svg':
                raise Exception("SVG formatına dönüştürme desteklenmiyor. Lütfen başka bir format seçin.")
            else:
                img.save(target_path)
            self.progress.emit(100)
        except Exception as e:
            raise Exception(f"Resim dönüştürme hatası: {str(e)}")
    
    def convert_audio(self, source_path, target_path):
        try:
            target_ext = Path(target_path).suffix.lower()          
            if target_ext in ['.wma', '.m4a']:
                try:
                    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    raise Exception("Bu dönüşüm için ffmpeg gerekli. Lütfen sisteminize ffmpeg yükleyin.")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_path = temp_file.name
                audio = AudioSegment.from_file(str(source_path))
                audio.export(temp_path, format='wav')
                if target_ext == '.wma':
                    codec = 'wmav2'
                else:  # .m4a
                    codec = 'aac'
                try:
                    duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                                  '-of', 'default=noprint_wrappers=1:nokey=1', temp_path]
                    duration = float(subprocess.check_output(duration_cmd).decode().strip())
                    cmd = [
                        'ffmpeg', '-i', temp_path,
                        '-acodec', codec,
                        '-y', 
                        str(target_path)
                    ]
                    process = subprocess.Popen(
                        cmd,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    for line in process.stderr:
                        if "time=" in line:
                            try:
                                time_str = line.split("time=")[1].split()[0]
                                hours, minutes, seconds = map(float, time_str.split(':'))
                                current_time = hours * 3600 + minutes * 60 + seconds
                                progress = int((current_time / duration) * 100)
                                self.progress.emit(min(progress, 99))
                            except:
                                continue
                    process.wait()
                    if process.returncode != 0:
                        raise Exception("FFmpeg dönüşüm hatası")             
                finally:
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                self.progress.emit(100)
            else:
                audio = AudioSegment.from_file(str(source_path))
                duration = len(audio)
                chunk_size = duration // 10
                for i in range(0, duration, chunk_size):
                    chunk = audio[i:i + chunk_size]
                    progress = int((i / duration) * 90)
                    self.progress.emit(progress)
                format_name = target_ext.replace('.', '')
                audio.export(target_path, format=format_name)
                self.progress.emit(100)
        except Exception as e:
            raise Exception(f"Ses dönüşümü hatası: {str(e)}")
        
    def convert_video(self, source_path, target_path):
        try:
            video = mp.VideoFileClip(str(source_path))
            duration = video.duration
            output_ext = os.path.splitext(target_path)[1].lower()
            if output_ext == '.webm':
                video.write_videofile(
                    str(target_path),
                    codec='libvpx',  
                    audio_codec='libvorbis', 
                    verbose=False,
                    logger=None
                )
            else:
                video.write_videofile(
                    str(target_path),
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
            self.progress.emit(100)
            video.close()
        except Exception as e:
            raise Exception(f"Video dönüştürme hatası: {str(e)}")

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(442, 741)
        self.media_frame = QFrame(parent=Form)
        self.media_frame.setGeometry(QtCore.QRect(20, 20, 401, 301))
        self.media_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.media_frame.setFrameShadow(QFrame.Shadow.Raised)
        icon = QtGui.QIcon("./img/icon.ico")
        Form.setWindowIcon(icon)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0)) 
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(255, 255, 255))
        Form.setPalette(palette) 
        self.media_controls_frame = QFrame(parent=Form)
        self.media_controls_frame.setGeometry(QtCore.QRect(20, 330, 401, 40))
        self.controls_layout = QHBoxLayout(self.media_controls_frame)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.play_button = QtWidgets.QPushButton("▶")
        self.stop_button = QtWidgets.QPushButton("⏹")
        self.play_button.setFixedSize(30, 30)
        self.stop_button.setFixedSize(30, 30)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(80)
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.stop_button)
        self.controls_layout.addWidget(self.progress_slider)
        self.controls_layout.addWidget(self.volume_slider)
        offset = 50  
        self.video_widget = QVideoWidget(self.media_frame)
        self.video_widget.setGeometry(0, 0, 401, 301)
        self.video_widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.video_widget.hide()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        self.image_label = QLabel(self.media_frame)
        self.image_label.setGeometry(0, 0, 401, 301)
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.hide()
        self.audio_frame = QFrame(self.media_frame)
        self.audio_frame.setGeometry(0, 0, 401, 301)
        self.audio_play_button = QtWidgets.QPushButton("▶", self.audio_frame)
        self.audio_play_button.setGeometry(175, 125, 50, 50)
        self.audio_play_button.clicked.connect(self.toggle_audio_playback)
        self.audio_frame.hide()
        self.fomat_combobox = QtWidgets.QComboBox(parent=Form)
        self.fomat_combobox.setGeometry(QtCore.QRect(20, 520 + offset, 131, 31))
        self.fomat_combobox.setObjectName("fomat_combobox")
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setGeometry(QtCore.QRect(20, 490 + offset, 331, 31))
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.eklebutonu = QtWidgets.QPushButton(parent=Form)
        self.eklebutonu.setGeometry(QtCore.QRect(20, 380 + offset, 71, 51))
        self.eklebutonu.setObjectName("eklebutonu")     
        self.temizlebutonu = QtWidgets.QPushButton(parent=Form)
        self.temizlebutonu.setGeometry(QtCore.QRect(110, 380 + offset, 71, 51))
        self.temizlebutonu.setObjectName("temizlebutonu")  
        self.dosya_adi_label = QtWidgets.QLabel(parent=Form)
        self.dosya_adi_label.setGeometry(QtCore.QRect(20, 350 + offset, 181, 16))
        font = QtGui.QFont()
        font.setFamily("Cascadia Code")
        self.dosya_adi_label.setFont(font)
        self.dosya_adi_label.setObjectName("dosya_adi_label")  
        self.ses_checkbox = QtWidgets.QCheckBox(parent=Form)
        self.ses_checkbox.setGeometry(QtCore.QRect(240, 380 + offset, 51, 21))
        self.ses_checkbox.setObjectName("ses_checkbox")       
        self.video_checkbox = QtWidgets.QCheckBox(parent=Form)
        self.video_checkbox.setGeometry(QtCore.QRect(240, 410 + offset, 81, 20))
        self.video_checkbox.setObjectName("video_checkbox")   
        self.resim_checkbox = QtWidgets.QCheckBox(parent=Form)
        self.resim_checkbox.setGeometry(QtCore.QRect(310, 380 + offset, 81, 20))
        self.resim_checkbox.setObjectName("resim_checkbox")
        self.dosya_turu_label = QtWidgets.QLabel(parent=Form)
        self.dosya_turu_label.setGeometry(QtCore.QRect(260, 350 + offset, 91, 16))
        font = QtGui.QFont()
        font.setFamily("Cascadia Code")
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.dosya_turu_label.setFont(font)
        self.dosya_turu_label.setObjectName("dosya_turu_label")       
        self.label_5 = QtWidgets.QLabel(parent=Form)
        self.label_5.setGeometry(QtCore.QRect(20, 450 + offset, 231, 31))
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")       
        self.format_adi_labeli = QtWidgets.QLabel(parent=Form)
        self.format_adi_labeli.setGeometry(QtCore.QRect(270, 450 + offset, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Cascadia Code")
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.format_adi_labeli.setFont(font)
        self.format_adi_labeli.setObjectName("format_adi_labeli")       
        self.baslatbutonu = QtWidgets.QPushButton(parent=Form)
        self.baslatbutonu.setGeometry(QtCore.QRect(330, 590 + offset, 91, 71))
        self.baslatbutonu.setObjectName("baslatbutonu")      
        self.progressBar = QtWidgets.QProgressBar(parent=Form)
        self.progressBar.setGeometry(QtCore.QRect(20, 590 + offset, 291, 23))
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.sonuc_mesaji_label = QtWidgets.QLabel(parent=Form)
        self.sonuc_mesaji_label.setGeometry(QtCore.QRect(20, 620 + offset, 281, 41))
        self.sonuc_mesaji_label.setObjectName("sonuc_mesaji_label")
        self.SUPPORTED_FORMATS = {
            'ses': ['.mp3', '.wav', '.ogg', '.aac', '.wma', '.m4a', '.flac'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'resim': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.avif']
        }
        self.setup_initial_state()
        self.setup_connections()
        self.setup_media_connections()
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "le1denfrost Format Dönüştürücü"))
        self.label.setText(_translate("Form", "Çevrilmesini istediğiniz format :"))
        self.eklebutonu.setText(_translate("Form", "EKLE"))
        self.temizlebutonu.setText(_translate("Form", "TEMİZLE"))
        self.dosya_adi_label.setText(_translate("Form", "DOSYA EKLE ⤦"))
        self.ses_checkbox.setText(_translate("Form", "Ses"))
        self.video_checkbox.setText(_translate("Form", "Video"))
        self.resim_checkbox.setText(_translate("Form", "Resim"))
        self.dosya_turu_label.setText(_translate("Form", "DOSYA TÜRÜ"))
        self.label_5.setText(_translate("Form", "Mevcut dosya formatı :"))
        self.format_adi_labeli.setText(_translate("Form", "format adı"))
        self.baslatbutonu.setText(_translate("Form", "BAŞLAT"))
        self.sonuc_mesaji_label.setText(_translate("Form", ""))

    def setup_initial_state(self):
        self.fomat_combobox.setEnabled(False)
        self.baslatbutonu.setEnabled(False)
        self.progressBar.setValue(0)
        self.sonuc_mesaji_label.setText("")
        self.ses_checkbox.setEnabled(False)
        self.video_checkbox.setEnabled(False)
        self.resim_checkbox.setEnabled(False)
        self.media_controls_frame.hide()
        self.checkbox_group = QtWidgets.QButtonGroup()
        self.checkbox_group.addButton(self.ses_checkbox)
        self.checkbox_group.addButton(self.video_checkbox)
        self.checkbox_group.addButton(self.resim_checkbox)
        self.checkbox_group.setExclusive(True)

    def setup_media_connections(self):
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button.clicked.connect(self.stop_playback)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.audio_output.setVolume(0.5)  

    def on_slider_pressed(self):
        self.was_playing = self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if self.was_playing:
            self.media_player.pause()
    
    def on_slider_released(self):
        position = self.progress_slider.value()
        self.media_player.setPosition(position) 
        if self.was_playing:
            self.media_player.play()
    
    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶")
        else:
            self.media_player.play()
            self.play_button.setText("⏸")
    
    def stop_playback(self):
        self.media_player.stop()
        self.play_button.setText("▶")
    
    def update_position(self, position):
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(position)
        self.progress_slider.blockSignals(False)
    
    def update_duration(self, duration):
        self.progress_slider.setRange(0, duration)
    
    def set_position(self, position):
        self.media_player.setPosition(position)
    
    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)
        
    def setup_connections(self):
        self.eklebutonu.clicked.connect(self.dosya_sec)
        self.temizlebutonu.clicked.connect(self.temizle)
        self.baslatbutonu.clicked.connect(self.donusumu_baslat)
        self.ses_checkbox.clicked.connect(self.format_listesini_guncelle)
        self.video_checkbox.clicked.connect(self.format_listesini_guncelle)
        self.resim_checkbox.clicked.connect(self.format_listesini_guncelle)
    
    def dosya_sec(self):
        file_filter = "Tüm Dosyalar (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Dosya Seç", "", file_filter
        )
        if file_path:
            self.current_file = file_path
            self.dosya_adi_label.setText(os.path.basename(file_path))
            self.format_adi_labeli.setText(os.path.splitext(file_path)[1])
            self.ses_checkbox.setEnabled(True)
            self.video_checkbox.setEnabled(True)
            self.resim_checkbox.setEnabled(True)
            self.fomat_combobox.setEnabled(True)
            uzanti = os.path.splitext(file_path)[1].lower()
            if uzanti in self.SUPPORTED_FORMATS['ses']:
                self.ses_checkbox.setChecked(True)
                self.show_audio_preview(file_path)
            elif uzanti in self.SUPPORTED_FORMATS['video']:
                self.video_checkbox.setChecked(True)
                self.show_video_preview(file_path)
            elif uzanti in self.SUPPORTED_FORMATS['resim']:
                self.resim_checkbox.setChecked(True)
                self.show_image_preview(file_path)
            self.format_listesini_guncelle()

    def format_listesini_guncelle(self):
        self.fomat_combobox.clear()
        if self.ses_checkbox.isChecked():
            self.fomat_combobox.addItems(self.SUPPORTED_FORMATS['ses'])
        elif self.video_checkbox.isChecked():
            self.fomat_combobox.addItems(self.SUPPORTED_FORMATS['video'])
        elif self.resim_checkbox.isChecked():
            self.fomat_combobox.addItems(self.SUPPORTED_FORMATS['resim'])
        self.baslatbutonu.setEnabled(True)

    def show_video_preview(self, file_path):
        self.image_label.hide()
        self.audio_frame.hide()
        self.video_widget.show()
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()
        self.play_button.setText("⏸")
        self.media_controls_frame.show()

    def show_image_preview(self, file_path):
        self.video_widget.hide()
        self.audio_frame.hide()
        self.image_label.show()
        pixmap = QPixmap(file_path)
        scaled_pixmap = pixmap.scaled(401, 301, QtCore.Qt.AspectRatioMode.KeepAspectRatio, 
                                    QtCore.Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def show_audio_preview(self, file_path):
        self.video_widget.hide()
        self.image_label.hide()
        self.audio_frame.show()
        self.media_controls_frame.show()
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.play_button.setText("▶")

    def toggle_audio_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.audio_play_button.setText("▶")
        else:
            self.media_player.play()
            self.audio_play_button.setText("⏸")
    
    def temizle(self):
        self.media_player.stop()
        self.video_widget.hide()
        self.image_label.hide()
        self.audio_frame.hide()
        self.audio_play_button.setText("▶")
        self.current_file = None
        self.dosya_adi_label.setText("EKLENEN DOSYA ADI")
        self.format_adi_labeli.setText("format adı")
        self.fomat_combobox.clear()
        self.progressBar.setValue(0)
        self.sonuc_mesaji_label.setText("")
        self.ses_checkbox.setChecked(False)
        self.video_checkbox.setChecked(False)
        self.resim_checkbox.setChecked(False)
        self.ses_checkbox.setEnabled(False)
        self.video_checkbox.setEnabled(False)
        self.resim_checkbox.setEnabled(False)
        self.fomat_combobox.setEnabled(False)
        self.baslatbutonu.setEnabled(False)

    def donusumu_baslat(self):
        if not hasattr(self, 'current_file'):
            QMessageBox.warning(None, "Hata", "Lütfen bir dosya seçin!")
            return
        conversion_type = None
        if self.ses_checkbox.isChecked():
            conversion_type = 'ses'
        elif self.video_checkbox.isChecked():
            conversion_type = 'video'
        elif self.resim_checkbox.isChecked():
            conversion_type = 'resim'
        if not conversion_type:
            QMessageBox.warning(None, "Hata", "Lütfen bir dönüşüm tipi seçin!")
            return
        target_format = self.fomat_combobox.currentText()
        self.disable_ui_elements()
        self.conversion_worker = ConversionWorker(
            self.current_file, 
            target_format,
            conversion_type
        )
        self.conversion_worker.progress.connect(self.update_progress)
        self.conversion_worker.finished.connect(self.conversion_finished)
        self.conversion_worker.start()
        self.sonuc_mesaji_label.setText("Dönüşüm işlemi devam ediyor...")
        
    def disable_ui_elements(self):
        self.eklebutonu.setEnabled(False)
        self.temizlebutonu.setEnabled(False)
        self.baslatbutonu.setEnabled(False)
        self.fomat_combobox.setEnabled(False)
        self.ses_checkbox.setEnabled(False)
        self.video_checkbox.setEnabled(False)
        self.resim_checkbox.setEnabled(False)
    
    def enable_ui_elements(self):
        self.eklebutonu.setEnabled(True)
        self.temizlebutonu.setEnabled(True)
        self.baslatbutonu.setEnabled(True)
        self.fomat_combobox.setEnabled(True)
        self.ses_checkbox.setEnabled(True)
        self.video_checkbox.setEnabled(True)
        self.resim_checkbox.setEnabled(True)
        
    def update_progress(self, value):
        self.progressBar.setValue(value)
    
    def conversion_finished(self, success, message):
        self.enable_ui_elements()
        if success:
            QMessageBox.information(None, "Başarılı", 
                                  f"Dönüşüm tamamlandı!\nDosya konumu: {message}")
            self.sonuc_mesaji_label.setText("Dönüşüm başarıyla tamamlandı!")
            self.progressBar.setValue(100)
        else:
            QMessageBox.critical(None, "Hata", 
                               f"Dönüşüm sırasında bir hata oluştu:\n{message}")
            self.sonuc_mesaji_label.setText("Dönüşüm başarısız!")
            self.progressBar.setValue(0)    

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())