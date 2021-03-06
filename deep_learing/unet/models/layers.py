import torch
import torch.nn as nn


class ContractBlock(nn.Sequential):
    def __init__(self, in_channels, out_channels, kernel_size, padding):
        super().__init__()
        self.add_module('conv1', nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=1, padding=padding))
        self.add_module('bn1', nn.BatchNorm2d(out_channels))
        self.add_module('relu1', nn.ReLU())
        self.add_module('conv2', nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, stride=1, padding=padding))
        self.add_module('bn2', nn.BatchNorm2d(out_channels))
        self.add_module('relu2', nn.ReLU())
        self.add_module('pool', MaxPool2d(kernel_size=3, stride=2, padding=1))

    def forward(self, x):
        return super().forward(x)

class ExpandBlock(nn.Sequential):
    def __init__(self, in_channels, out_channels, kernel_size, padding):
        super().__init__()
        self.add_module('conv1', nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=1, padding=padding))
        self.add_module('bn1', nn.BatchNorm2d(out_channels))
        self.add_module('relu1', nn.ReLU())
        self.add_module('conv2', nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, stride=1, padding=padding))
        self.add_module('bn2', nn.BatchNorm2d(out_channels))
        self.add_module('relu2', nn.ReLU())
        self.add_module('up', nn.ConvTranspose2d(out_channels, out_channels, kernel_size=3, stride=2, padding=1, output_padding=1))

    def forward(self, x):
        return super().forward(x)
