import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg # pyqtgraph is better suited for plotting scientific data like spectra

class SpectralAnalyzerWidget(QtWidgets.QWidget):
    spectrum_data_ready = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spectral Analyzer")
        self.setGeometry(100, 100, 600, 400) # Initial window size and position

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Use pyqtgraph for plotting
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        # Configure plot appearance
        self.plot_widget.setBackground('k') # Black background
        self.plot_widget.setTitle("Audio Spectrum", color="#ff9800", size="12pt") # Orange title
        styles = {'color': '#ff9800', 'font-size': '10pt'} # Orange text for labels
        self.plot_widget.setLabel('left', 'Amplitude (dB)', **styles)
        self.plot_widget.setLabel('bottom', 'Frequency (Hz)', **styles)
        self.plot_widget.getAxis('left').setTextPen('#ff9800')
        self.plot_widget.getAxis('bottom').setTextPen('#ff9800')
        self.plot_widget.getAxis('left').setPen('#ff9800')
        self.plot_widget.getAxis('bottom').setPen('#ff9800')

        # Add a grid for better readability
        self.plot_widget.getAxis('left').setGrid(150)
        self.plot_widget.getAxis('bottom').setGrid(150)


        # Create a plot item for the spectrum line
        self.spectrum_curve = self.plot_widget.plot(pen=pg.mkPen(color='#ff9800', width=2)) # Orange line

        self.spectrum_data_ready.connect(self.update_plot)

        self.sample_rate = 44100 # Default sample rate, will be updated from config
        self.chunk_size = 1024 # Default chunk size, can be adjusted

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate

    def set_chunk_size(self, chunk_size):
        self.chunk_size = chunk_size

    @QtCore.pyqtSlot(np.ndarray)
    def update_plot(self, audio_chunk):
        # Perform FFT on the audio chunk
        # Ensure the chunk is the correct size, pad with zeros if necessary
        if len(audio_chunk) < self.chunk_size:
             padded_chunk = np.pad(audio_chunk, (0, self.chunk_size - len(audio_chunk)), 'constant')
        else:
             padded_chunk = audio_chunk[:self.chunk_size]

        # Apply a window function (e.g., Hann window)
        window = np.hanning(len(padded_chunk))
        windowed_chunk = padded_chunk * window

        # Perform FFT
        fft_result = np.fft.fft(windowed_chunk)
        # Get the magnitude of the positive frequency components
        spectrum_magnitude = np.abs(fft_result[:len(fft_result)//2])

        # Convert to dB scale (add a small value to avoid log(0))
        spectrum_db = 20 * np.log10(spectrum_magnitude + 1e-9)

        # Create frequency bins
        frequencies = np.fft.fftfreq(len(fft_result), 1/self.sample_rate)[:len(fft_result)//2]

        # Apply frequency-dependent weighting for sensitivity adjustment
        # Normalize frequencies to a 0-1 range for weighting calculation
        max_freq = self.sample_rate / 2
        normalized_frequencies = frequencies / max_freq

        # Create a weighting curve: e.g., linear or exponential.
        # A simple linear weighting: low frequencies get less weight, high frequencies get more.
        # You can adjust the 'start_weight' and 'end_weight' to fine-tune sensitivity.
        # Using an exponential weighting for a more aggressive curve.
        start_weight = 0.001 # Very low sensitivity at low frequencies
        end_weight = 100.0   # Very high sensitivity at high frequencies

        # Exponential weighting curve: starts at start_weight, ends at end_weight
        # This provides a much steeper curve than linear weighting.
        weighting_curve = np.exp(normalized_frequencies * np.log(end_weight / start_weight)) * start_weight

        # Apply the weighting to the magnitude before converting to dB
        weighted_spectrum_magnitude = spectrum_magnitude * weighting_curve
        spectrum_db = 20 * np.log10(weighted_spectrum_magnitude + 1e-9)

        # Filter out very low frequencies to "truncate" them from display
        min_display_frequency = 80 # Hz, adjust as needed. Common voice fundamental is above this.
        valid_indices = frequencies >= min_display_frequency

        filtered_frequencies = frequencies[valid_indices]
        filtered_spectrum_db = spectrum_db[valid_indices]

        # Update the plot with filtered data
        self.spectrum_curve.setData(filtered_frequencies, filtered_spectrum_db)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = SpectralAnalyzerWidget()
    widget.show()
    # Example of how to send data (replace with actual audio data stream)
    # Generate some dummy data
    # dummy_data = np.random.rand(1024) * 1000
    # widget.spectrum_data_ready.emit(dummy_data)
    sys.exit(app.exec_())
