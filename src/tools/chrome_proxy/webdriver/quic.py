# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import time

import common
from common import TestDriver
from common import IntegrationTest


class Quic(IntegrationTest):

  # Ensure Chrome uses DataSaver when QUIC is enabled. This test should pass
  # even if QUIC is disabled on the server side. In that case, Chrome should
  # fallback to using the non-QUIC proxies.
  def testCheckPageWithQuicProxy(self):
    with TestDriver() as t:
      t.AddChromeArg('--enable-spdy-proxy-auth')
      t.AddChromeArg('--enable-quic')
      # Enable QUIC for non-core HTTPS proxies.
      t.AddChromeArg('--data-reduction-proxy-enable-quic-on-non-core-proxies')
      t.AddChromeArg('--force-fieldtrials=DataReductionProxyUseQuic/Enabled')
      t.LoadURL('http://check.googlezip.net/test.html')
      responses = t.GetHTTPResponses()
      self.assertEqual(2, len(responses))
      for response in responses:
        self.assertHasChromeProxyViaHeader(response)

  # Ensure Chrome uses QUIC DataSaver proxy when QUIC is enabled. This test
  # may fail if QUIC is disabled on the server side.
  def testCheckPageWithQuicProxyTransaction(self):
    with TestDriver() as t:
      t.AddChromeArg('--enable-spdy-proxy-auth')
      t.AddChromeArg('--enable-quic')
      # Enable QUIC for non-core HTTPS proxies.
      t.AddChromeArg('--data-reduction-proxy-enable-quic-on-non-core-proxies')
      t.AddChromeArg('--force-fieldtrials=DataReductionProxyUseQuic/Enabled')
      t.LoadURL('http://check.googlezip.net/test.html')
      responses = t.GetHTTPResponses()
      self.assertEqual(2, len(responses))
      for response in responses:
        self.assertHasChromeProxyViaHeader(response)

      # Verify that histogram DataReductionProxy.Quic.ProxyStatus has at least 1
      # sample. This sample must be in bucket 0 (QUIC_PROXY_STATUS_AVAILABLE).
      proxy_status = t.GetHistogram('DataReductionProxy.Quic.ProxyStatus')
      self.assertLessEqual(1, proxy_status['count'])
      self.assertEqual(0, proxy_status['sum'])

      # Navigate to one more page to ensure that established QUIC connection
      # is used for the next request. Give 3 seconds extra headroom for the QUIC
      # connection to be established.
      time.sleep(3)
      t.LoadURL('http://check.googlezip.net/test.html')
      proxy_usage = t.GetHistogram('Net.QuicAlternativeProxy.Usage')
      # Bucket ALTERNATIVE_PROXY_USAGE_NO_RACE should have at least onesample.
      self.assertLessEqual(1, proxy_usage['buckets'][0]['count'])

if __name__ == '__main__':
  IntegrationTest.RunAllTests()
