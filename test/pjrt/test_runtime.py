import contextlib
import logging
import os
from typing import Dict, Optional
from unittest import mock
from importlib import reload

import torch_xla
from absl.testing import absltest, parameterized
import torch_xla.core.xla_env_vars as xenv
import torch_xla.core.xla_model as xm
from torch_xla import runtime as xr


class TestExperimentalPjrt(parameterized.TestCase):

  def setUp(self):
    xr.set_device_type('CPU')

  @parameterized.parameters(('CPU', 'CPU'), ('CUDA', 'CUDA'), ('TPU', 'TPU'))
  def test_device_type(self, pjrt_device, expected):
    with mock.patch.dict(os.environ, {'PJRT_DEVICE': pjrt_device}, clear=True):
      self.assertEqual(xr.device_type(), expected)

  def test_set_device_type(self):
    with mock.patch.dict(
        os.environ, {'PJRT_DEVICE': 'CPU'}, clear=True), mock.patch.object(
            torch_xla._XLAC, '_xla_runtime_is_initialized', return_value=False):
      xr.set_device_type('TOASTER')
      self.assertEqual(os.environ['PJRT_DEVICE'], 'TOASTER')

  def test_set_device_type_error(self):
    with mock.patch.dict(
        os.environ, {'PJRT_DEVICE': 'CPU'}, clear=True), mock.patch.object(
            torch_xla._XLAC, '_xla_runtime_is_initialized', return_value=True):
      with self.assertRaises(RuntimeError):
        xr.set_device_type('TPU')

  def test_set_device_type_same_device(self):
    with mock.patch.dict(
        os.environ, {'PJRT_DEVICE': 'CPU'}, clear=True), mock.patch.object(
            torch_xla._XLAC, '_xla_runtime_is_initialized', return_value=True):
      xr.set_device_type('CPU')

  def test_default_ordinals(self):
    global_ordinal = xr.global_ordinal()
    self.assertEqual(global_ordinal, 0)

    local_ordinal = xm.get_local_ordinal()
    self.assertEqual(local_ordinal, 0)

  def test_num_local_devices(self):
    self.assertLen(xm.get_xla_supported_devices(),
                   xr.addressable_device_count())

  def test_num_global_devices(self):
    self.assertLen(torch_xla._XLAC._xla_get_all_devices(),
                   xr.global_device_count())

  def test_xla_device_error(self):
    with self.assertRaises(IndexError):
      torch_xla.device(10)

  @parameterized.named_parameters(('default', {}, True), ('no_default', {
      'PJRT_SELECT_DEFAULT_DEVICE': '0'
  }, False), ('pjrt_cpu', {
      'PJRT_DEVICE': 'CPU',
      'PJRT_SELECT_DEFAULT_DEVICE': '0'
  }, True), ('pjrt_tpu_precedence', {
      'PJRT_DEVICE': 'TPU',
      'XRT_TPU_CONFIG': 'localservice;0;localhost:51011',
  }, True), ('gpu_num_devives', {
      'GPU_NUM_DEVICES': '4'
  }, True), ('pjrt_gpu', {
      'PJRT_DEVICE': 'CUDA',
      'GPU_NUM_DEVICES': '4'
  }, True))
  def test_pjrt_default_device(self, env_vars, expect_using_pjrt):
    # Prevent flag checking during reinitialization of PJRT backend.
    # Without the patch, the test will be impacted by other tests when torch_xla reloads.
    with mock.patch(
        'torch_xla._XLAC._xla_runtime_is_initialized', return_value=False):
      with mock.patch.dict(os.environ, env_vars, clear=True):
        # We need to reload the torch_xla module because clear=True will clear all os.environ.
        global torch_xla
        reload(torch_xla)
        logs_context = contextlib.nullcontext()
        if expect_using_pjrt:
          self.assertIn(xr.device_type(), ['CPU', 'CUDA', 'TPU', 'NEURON'])
        else:
          self.assertIsNone(xr.device_type())

  def test_host_index(self):
    self.assertEqual(xr.host_index(), 0)


if __name__ == '__main__':
  absltest.main()
