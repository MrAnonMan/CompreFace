#  Version: 2020.02.21
#
#  MIT License
#
#  Copyright (c) 2018 Jiankang Deng and Jia Guo
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

import sys
import os
import argparse
import onnx
import mxnet as mx

print('mxnet version:', mx.__version__)
print('onnx version:', onnx.__version__)
#make sure to install onnx-1.2.1
#pip uninstall onnx
#pip install onnx==1.2.1
assert onnx.__version__=='1.2.1'
import numpy as np
from mxnet.contrib import onnx as onnx_mxnet

parser = argparse.ArgumentParser(description='convert insightface models to onnx')
# general
parser.add_argument('--prefix', default='./r100-arcface/model', help='prefix to load model.')
parser.add_argument('--epoch', default=0, type=int, help='epoch number to load model.')
parser.add_argument('--input-shape', default='3,112,112', help='input shape.')
parser.add_argument('--output-onnx', default='./r100.onnx', help='path to write onnx model.')
args = parser.parse_args()
input_shape = (1,) + tuple( [int(x) for x in args.input_shape.split(',')] )
print('input-shape:', input_shape)

sym_file = "%s-symbol.json"%args.prefix
params_file = "%s-%04d.params"%(args.prefix, args.epoch)
assert os.path.exists(sym_file)
assert os.path.exists(params_file)
converted_model_path = onnx_mxnet.export_model(sym_file, params_file, [input_shape], np.float32, args.output_onnx)

