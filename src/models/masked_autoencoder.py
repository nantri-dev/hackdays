import torch
import torch.nn as nn

class CurrentMaskedAE(nn.Module):
    def __init__(self, window_size=32, num_sensors=4):
        super().__init__()
        self.window_size = window_size
        self.num_sensors = num_sensors
        
        # 1D Temporal CNN
        self.encoder = nn.Sequential(
            nn.Conv1d(num_sensors - 1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(16, 32, kernel_size=3, padding=1),
            nn.ReLU()
        )
        
        self.decoder = nn.Sequential(
            nn.Conv1d(32, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(16, 1, kernel_size=3, padding=1)
        )
        
    def forward(self, x_masked):
        # x_masked shape: (batch, num_sensors - 1, window_size)
        features = self.encoder(x_masked)
        reconstructed_channel = self.decoder(features)
        # return shape: (batch, 1, window_size)
        return reconstructed_channel
